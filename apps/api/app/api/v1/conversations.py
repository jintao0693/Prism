"""对话接口（含 SSE、上下文压缩）。"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.core.storage import get_storage
from app.models.asset import Asset
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ChatMessageOut,
    CompactOut,
    ConversationCreate,
    ConversationSummaryOut,
    GenerationResultOut,
    SendMessageRequest,
)
from app.services.agent.compact import (
    apply_usage_to_conversation,
    compact_conversation,
    maybe_auto_compact,
)
from app.services.agent.context import load_prior_messages
from app.services.agent.deps import PrismDeps
from app.services.agent.streaming import encode_sse, iter_agent_events
from app.services.media.gateway import MediaGateway
from app.services.providers.registry import build_volcengine_client

router = APIRouter(prefix="/conversations", tags=["对话"])


async def _enrich_results(db: AsyncSession, raw: list) -> list[GenerationResultOut]:
    """用资产表补齐 url / thumbUrl，避免历史 JSON 缺预览或指向失效路径。"""
    from app.services.media.preview import asset_preview_fields

    out: list[GenerationResultOut] = []
    for item in raw:
        data = dict(item) if isinstance(item, dict) else {}
        asset_id = str(data.get("id") or "")
        asset = await db.get(Asset, asset_id) if asset_id else None
        if asset and asset.storage_key:
            preview = asset_preview_fields(asset)
            data["url"] = preview["url"] or data.get("url")
            data["thumbUrl"] = preview["thumbUrl"]
            data["mimeType"] = preview["mimeType"]
            data["previewKind"] = preview["previewKind"]
            if not data.get("kind"):
                data["kind"] = asset.kind
        out.append(GenerationResultOut.model_validate(data))
    return out


async def _msg_out(db: AsyncSession, message: Message) -> ChatMessageOut:
    """ORM Message → 响应模型。"""
    results = None
    if message.results_json:
        raw = json.loads(message.results_json)
        if isinstance(raw, list):
            results = await _enrich_results(db, raw)
    return ChatMessageOut(
        id=message.id,
        role=message.role,  # type: ignore[arg-type]
        content=message.content,
        toolLabel=message.tool_label,
        results=results,
        createdAt=message.created_at.isoformat(),
    )


@router.get("", response_model=list[ConversationSummaryOut])
async def list_conversations(
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationSummaryOut]:
    """会话列表。"""
    assert ctx.workspace_id
    rows = (
        await db.scalars(
            select(Conversation)
            .where(
                Conversation.tenant_id == ctx.tenant_id,
                Conversation.workspace_id == ctx.workspace_id,
            )
            .order_by(Conversation.updated_at.desc()),
        )
    ).all()

    tones = ["a", "b", "c"]
    out: list[ConversationSummaryOut] = []
    for i, c in enumerate(rows):
        out.append(
            ConversationSummaryOut(
                id=c.id,
                title=c.title,
                kind=c.kind,
                updatedAtLabel=c.updated_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M"),
                thumbTone=tones[i % 3],
            ),
        )
    return out


@router.post("", response_model=ConversationSummaryOut)
async def create_conversation(
    body: ConversationCreate,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummaryOut:
    """新建会话。"""
    assert ctx.workspace_id
    conv = Conversation(
        id=f"c_{uuid.uuid4().hex[:10]}",
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        title=body.title,
        kind=body.kind,
    )
    db.add(conv)
    await db.commit()
    return ConversationSummaryOut(
        id=conv.id,
        title=conv.title,
        kind=conv.kind,
        updatedAtLabel="刚刚",
        thumbTone="a",
    )


@router.get("/{conversation_id}/messages", response_model=list[ChatMessageOut])
async def get_messages(
    conversation_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageOut]:
    """拉取历史消息。"""
    conv = await db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages)),
    )
    if not conv or conv.tenant_id != ctx.tenant_id or conv.workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return [await _msg_out(db, m) for m in conv.messages]


@router.post("/{conversation_id}/compact", response_model=CompactOut)
async def compact_messages(
    conversation_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> CompactOut:
    """手动压缩会话上下文（摘要检查点，不删消息）。"""
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.tenant_id != ctx.tenant_id or conv.workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    ark = await build_volcengine_client(db, ctx.tenant_id)
    if not ark or not ark.chat_model:
        raise HTTPException(status_code=400, detail="未配置对话模型，无法压缩")
    result = await compact_conversation(db, conv, ark)
    await db.commit()
    return CompactOut(
        didCompact=result.did_compact,
        generation=result.generation,
        summaryChars=result.summary_chars,
        reason=result.reason,
        contextTokensEstimate=int(conv.context_tokens_estimate or 0),
    )


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """发送消息并以 SSE 流式返回 Agent 事件。"""
    assert ctx.workspace_id
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.tenant_id != ctx.tenant_id or conv.workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=404, detail="会话不存在")

    ref_ids = [x for x in (body.reference_asset_ids or []) if x][:4]
    ref_cards: list[dict] = []
    if ref_ids:
        storage = get_storage()
        for asset_id in ref_ids:
            asset = await db.get(Asset, asset_id)
            if (
                not asset
                or asset.tenant_id != ctx.tenant_id
                or asset.workspace_id != ctx.workspace_id
                or asset.is_deleted
                or asset.kind != "image"
            ):
                raise HTTPException(status_code=400, detail=f"参考图不可用：{asset_id}")
            if not asset.source_conversation_id:
                asset.source_conversation_id = conversation_id
            ref_cards.append(
                {
                    "id": asset.id,
                    "label": "参考图",
                    "tone": "d",
                    "kind": "image",
                    "url": storage.public_url(asset.storage_key) if asset.storage_key else None,
                },
            )

    user_msg = Message(
        id=f"m_{uuid.uuid4().hex[:12]}",
        conversation_id=conversation_id,
        role="user",
        content=body.content,
        results_json=json.dumps(ref_cards, ensure_ascii=False) if ref_cards else None,
    )
    db.add(user_msg)
    await db.flush()

    ark = await build_volcengine_client(db, ctx.tenant_id)
    # 发消息前：usage / 窗口过大则自动压缩（不含本轮）
    compact_result = await maybe_auto_compact(
        db,
        conv,
        ark,
        exclude_message_id=user_msg.id,
    )

    history = await load_prior_messages(
        db,
        conversation_id,
        exclude_message_id=user_msg.id,
        summary_text=conv.summary_text,
        compacted_at=conv.compacted_at,
        include_summary_bridge=bool(conv.summary_text),
    )

    media = await MediaGateway.for_tenant(db, ctx.tenant_id)
    deps = PrismDeps(
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        conversation_id=conversation_id,
        db=db,
        media=media,
        knowledge_base_ids=body.knowledge_base_ids,
        reference_asset_ids=ref_ids,
        history_messages=history,
        compact_generation=int(conv.compact_generation or 0),
    )

    async def event_stream():
        if compact_result.did_compact:
            yield encode_sse(
                {
                    "type": "context.compacted",
                    "data": {
                        "generation": compact_result.generation,
                        "summaryChars": compact_result.summary_chars,
                        "reason": compact_result.reason,
                    },
                },
            )

        final_content = ""
        tool_label = None
        results = []
        async for event in iter_agent_events(deps, body.content, session=db):
            if event["type"] == "message.done":
                data = event.get("data", {})
                final_content = data.get("content", "")
                tool_label = data.get("toolLabel")
                results = data.get("results") or []
            yield encode_sse(event)

        assistant = Message(
            id=f"m_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role="assistant",
            content=final_content,
            tool_label=tool_label,
            results_json=json.dumps(results, ensure_ascii=False) if results else None,
        )
        db.add(assistant)
        apply_usage_to_conversation(
            conv,
            prompt_tokens=deps.last_prompt_tokens,
            completion_tokens=deps.last_completion_tokens,
            total_tokens=deps.last_total_tokens,
        )
        conv.updated_at = datetime.now(UTC)
        await db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

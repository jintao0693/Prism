"""对话接口（含 SSE）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ChatMessageOut,
    ConversationCreate,
    ConversationSummaryOut,
    GenerationResultOut,
    SendMessageRequest,
)
from app.services.agent.deps import PrismDeps
from app.services.agent.streaming import encode_sse, iter_agent_events
from app.services.media.gateway import MediaGateway

router = APIRouter(prefix="/conversations", tags=["对话"])


def _msg_out(message: Message) -> ChatMessageOut:
    """ORM Message → 响应模型。"""
    results = None
    if message.results_json:
        raw = json.loads(message.results_json)
        results = [GenerationResultOut.model_validate(item) for item in raw]
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
                updatedAtLabel=c.updated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
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
    return [_msg_out(m) for m in conv.messages]


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

    user_msg = Message(
        id=f"m_{uuid.uuid4().hex[:12]}",
        conversation_id=conversation_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # 按租户配置选择火山或演示媒体网关
    media = await MediaGateway.for_tenant(db, ctx.tenant_id)
    deps = PrismDeps(
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        conversation_id=conversation_id,
        db=db,
        media=media,
        knowledge_base_ids=body.knowledge_base_ids,
    )

    async def event_stream():
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
        conv.updated_at = datetime.now(timezone.utc)
        await db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

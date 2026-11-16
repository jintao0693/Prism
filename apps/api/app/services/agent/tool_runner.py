"""
统一多模态工具 Agent（Ark 路径）。

用意图 + 规则选择工具（chat / kb / 文生图 / 图生图 / 文生视频 / 图生视频），
产出与 SSE 对齐的事件；媒体结果带血缘并进入后续上下文。
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from app.models.asset import Asset
from app.services.agent.asset_memory import (
    dumps_asset_meta,
    format_media_context,
    list_conversation_assets,
    read_asset_bytes,
    resolve_last_image_asset,
    resolve_reference_image,
    wants_image_refine,
    wants_image_to_video,
)
from app.services.agent.context import assemble_chat_messages, build_system_prompt
from app.services.agent.deps import PrismDeps
from app.services.agent.instructions import PRISM_SYSTEM_INSTRUCTIONS
from app.services.agent.intent import classify_intent
from app.services.knowledge.search_image import search_image
from app.services.knowledge.search_text import search_text
from app.services.providers.volcengine.client import VolcengineArkClient

_VISUAL_KB_RE = re.compile(r"相似|像这|图搜|找图|视觉|主视觉|素材图")


async def run_tool_agent(
    deps: PrismDeps,
    user_text: str,
    *,
    ark: VolcengineArkClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """统一工具循环入口。"""
    has_knowledge = bool(deps.knowledge_base_ids)
    intent, intent_source = await classify_intent(
        user_text,
        ark=ark,
        has_knowledge=has_knowledge,
    )
    yield {
        "type": "intent.resolved",
        "data": {"intent": intent, "source": intent_source},
    }

    # 注入近期资产记忆到历史（模型可见）
    assets = await list_conversation_assets(
        deps.db,
        conversation_id=deps.conversation_id,
        tenant_id=deps.tenant_id,
    )
    media_ctx = format_media_context(assets)
    history = list(deps.history_messages)
    if media_ctx:
        history = [
            {"role": "user", "content": media_ctx},
            {
                "role": "assistant",
                "content": "已了解本会话近期生成资产，跨模态改稿时会优先复用。",
            },
            *history,
        ]

    ref_image = await resolve_reference_image(
        deps.db,
        asset_ids=deps.reference_asset_ids,
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
    )
    last_image = await resolve_last_image_asset(
        deps.db,
        conversation_id=deps.conversation_id,
        tenant_id=deps.tenant_id,
    )
    parent_image = ref_image or last_image
    has_ref = ref_image is not None
    tool = _select_tool(
        intent=intent,
        user_text=user_text,
        has_knowledge=has_knowledge,
        has_last_image=parent_image is not None,
        has_reference_image=has_ref,
    )
    yield {
        "type": "tool.planned",
        "data": {
            "tool": tool,
            "hasLastImage": bool(last_image),
            "hasReferenceImage": has_ref,
            "parentAssetId": parent_image.id if parent_image else None,
        },
    }

    system = build_system_prompt(
        PRISM_SYSTEM_INSTRUCTIONS
        + "\n\n你可以使用会话中的生成资产与用户上传的参考图；改图/出视频时优先复用参考图或上一张图。",
        workspace_id=deps.workspace_id,
        knowledge_base_ids=deps.knowledge_base_ids,
        compact_generation=deps.compact_generation,
    )

    if tool in {"text_to_image", "image_to_image"}:
        async for event in _run_image_tool(
            deps,
            user_text=user_text,
            mode=tool,
            parent=parent_image,
        ):
            yield event
        return

    if tool in {"text_to_video", "image_to_video"}:
        async for event in _run_video_tool(
            deps,
            user_text=user_text,
            mode=tool,
            parent=parent_image,
        ):
            yield event
        return

    # 知识库：可文搜 / 图搜，再回答
    rag_block = ""
    if tool in {"kb_search_text", "kb_search_image", "chat"} and has_knowledge:
        if tool == "kb_search_image" or (
            tool == "chat" and _VISUAL_KB_RE.search(user_text)
        ):
            async for event in _kb_image(deps, user_text):
                if event["type"] == "tool.result":
                    rag_block = str(event["data"].get("text") or "")
                yield event
        elif tool == "kb_search_text" or has_knowledge:
            async for event in _kb_text(deps, user_text):
                if event["type"] == "tool.result":
                    rag_block = str(event["data"].get("text") or "")
                yield event

    latest = user_text
    if rag_block:
        latest = (
            f"可参考知识库检索结果（没有则忽略）：\n{rag_block}\n\n用户问题：{user_text}"
        )

    if ark and ark.chat_model:
        messages, stats = assemble_chat_messages(
            system=system,
            history=history,
            latest_user=latest,
        )
        yield {"type": "context.ready", "data": stats}
        yield {"type": "text.delta", "data": {"text": ""}}
        result = await ark.chat_completion(messages)
        deps.last_prompt_tokens = result.prompt_tokens
        deps.last_completion_tokens = result.completion_tokens
        deps.last_total_tokens = result.total_tokens
        yield {"type": "text.delta", "data": {"text": result.content}}
        yield {
            "type": "message.done",
            "data": {"content": result.content, "results": deps.generated_assets},
        }
        return

    content = (
        f"这是 Prism 演示回复：已收到「{user_text[:80]}」。"
        "请在「设置 → 火山方舟」填写 API Key 并启用。"
    )
    yield {"type": "text.delta", "data": {"text": content}}
    yield {"type": "message.done", "data": {"content": content, "results": []}}


def _select_tool(
    *,
    intent: str,
    user_text: str,
    has_knowledge: bool,
    has_last_image: bool,
    has_reference_image: bool = False,
) -> str:
    """意图 + 规则 → 工具名。"""
    has_image = has_last_image or has_reference_image

    if intent == "video" or wants_image_to_video(user_text):
        if has_image and (
            has_reference_image
            or wants_image_to_video(user_text)
            or wants_image_refine(user_text)
            or "图" in user_text
        ):
            return "image_to_video"
        return "text_to_video"

    if intent == "image":
        # 用户本轮附带参考图 → 默认图生图；否则「再改一点」才走 i2i
        if has_image and (has_reference_image or wants_image_refine(user_text)):
            return "image_to_image"
        return "text_to_image"

    # 附了参考图但意图被判成 chat：仅在明确改图/出片时抢路由
    if has_reference_image:
        if wants_image_to_video(user_text):
            return "image_to_video"
        if wants_image_refine(user_text):
            return "image_to_image"

    if intent == "knowledge" and has_knowledge:
        if _VISUAL_KB_RE.search(user_text):
            return "kb_search_image"
        return "kb_search_text"

    if has_knowledge and _VISUAL_KB_RE.search(user_text):
        return "kb_search_image"

    return "chat"


async def _run_image_tool(
    deps: PrismDeps,
    *,
    user_text: str,
    mode: str,
    parent: Asset | None,
) -> AsyncIterator[dict[str, Any]]:
    tool_name = mode
    yield {"type": "tool.start", "data": {"name": tool_name}}
    image_bytes = None
    parent_id = None
    if mode == "image_to_image" and parent:
        image_bytes = read_asset_bytes(parent)
        parent_id = parent.id
        if not image_bytes:
            mode = "text_to_image"
            tool_name = "text_to_image"
            yield {
                "type": "tool.start",
                "data": {"name": tool_name, "note": "上一张图文件缺失，回退文生图"},
            }

    asset_id, result, key = await deps.media.generate_image(
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        prompt=user_text,
        mode=mode,
        image_bytes=image_bytes,
    )
    meta = dumps_asset_meta(
        prompt=user_text,
        mode=mode,
        parent_asset_id=parent_id,
        provider=deps.media.provider.name,
    )
    asset = Asset(
        id=asset_id,
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        name=result.filename,
        kind="image",
        storage_key=key,
        mime_type=result.mime_type,
        meta=meta,
        source_conversation_id=deps.conversation_id,
    )
    deps.db.add(asset)
    from app.services.media.preview import asset_preview_fields

    preview = asset_preview_fields(asset)
    url = preview["url"]
    card = {
        "id": asset_id,
        "label": "图生图" if mode == "image_to_image" else "生图",
        "tone": "a",
        "kind": "image",
        "url": url,
        "thumbUrl": preview["thumbUrl"],
        "mimeType": preview["mimeType"],
        "previewKind": preview["previewKind"],
        "parentAssetId": parent_id,
    }
    deps.generated_assets.append(card)
    await deps.db.flush()
    yield {
        "type": "tool.result",
        "data": {
            "name": tool_name,
            "asset_id": asset_id,
            "url": url,
            "thumbUrl": preview["thumbUrl"],
        },
    }
    content = (
        f"已完成{'图生图' if mode == 'image_to_image' else '生图'}"
        f"（{deps.media.provider.name}），资产 {asset_id} 已写入资产中心。"
    )
    yield {"type": "text.delta", "data": {"text": content}}
    yield {
        "type": "message.done",
        "data": {
            "content": content,
            "toolLabel": f"{tool_name} · 完成",
            "results": [card],
        },
    }


async def _run_video_tool(
    deps: PrismDeps,
    *,
    user_text: str,
    mode: str,
    parent: Asset | None,
) -> AsyncIterator[dict[str, Any]]:
    tool_name = mode
    yield {"type": "tool.start", "data": {"name": tool_name}}
    image_bytes = None
    parent_id = None
    if mode == "image_to_video" and parent:
        image_bytes = read_asset_bytes(parent)
        parent_id = parent.id
        if not image_bytes:
            mode = "text_to_video"
            tool_name = "text_to_video"

    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_progress_q(status: str, elapsed: float, task_id: str) -> None:
        await queue.put(
            {
                "type": "media.progress",
                "data": {
                    "status": status,
                    "elapsedSec": round(elapsed, 1),
                    "taskId": task_id,
                    "kind": "video",
                },
            },
        )

    async def _produce() -> tuple[str, Any, str]:
        try:
            return await deps.media.generate_video(
                tenant_id=deps.tenant_id,
                workspace_id=deps.workspace_id,
                prompt=user_text,
                mode=mode,
                image_bytes=image_bytes,
                on_progress=on_progress_q,
            )
        finally:
            await queue.put(None)

    task = asyncio.create_task(_produce())
    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
    try:
        asset_id, result, key = await task
    except Exception as exc:
        err = f"视频生成失败：{exc}"
        yield {"type": "tool.result", "data": {"name": tool_name, "error": str(exc)}}
        yield {"type": "text.delta", "data": {"text": err}}
        yield {
            "type": "message.done",
            "data": {"content": err, "toolLabel": f"{tool_name} · 失败", "results": []},
        }
        return

    meta = dumps_asset_meta(
        prompt=user_text,
        mode=mode,
        parent_asset_id=parent_id,
        provider=deps.media.provider.name,
    )
    asset = Asset(
        id=asset_id,
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        name=result.filename,
        kind="video",
        storage_key=key,
        mime_type=result.mime_type,
        meta=meta,
        source_conversation_id=deps.conversation_id,
    )
    deps.db.add(asset)
    from app.services.media.preview import asset_preview_fields

    preview = asset_preview_fields(asset)
    url = preview["url"]
    card = {
        "id": asset_id,
        "label": "图生视频" if mode == "image_to_video" else "生视频",
        "tone": "c",
        "kind": "video",
        "url": url,
        "thumbUrl": preview["thumbUrl"],
        "mimeType": preview["mimeType"],
        "previewKind": preview["previewKind"],
        "parentAssetId": parent_id,
    }
    deps.generated_assets.append(card)
    await deps.db.flush()
    yield {
        "type": "tool.result",
        "data": {
            "name": tool_name,
            "asset_id": asset_id,
            "url": url,
            "thumbUrl": preview["thumbUrl"],
        },
    }
    content = (
        f"已完成{'图生视频' if mode == 'image_to_video' else '视频生成'}"
        f"（{deps.media.provider.name}），可在资产中心查看。"
    )
    yield {"type": "text.delta", "data": {"text": content}}
    yield {
        "type": "message.done",
        "data": {
            "content": content,
            "toolLabel": f"{tool_name} · 完成",
            "results": [card],
        },
    }


async def _kb_text(deps: PrismDeps, user_text: str) -> AsyncIterator[dict[str, Any]]:
    yield {"type": "tool.start", "data": {"name": "kb_search_text"}}
    chunks: list[str] = []
    for kb_id in deps.knowledge_base_ids:
        hits = await search_text(
            deps.db,
            tenant_id=deps.tenant_id,
            knowledge_base_id=kb_id,
            query=user_text,
            top_k=3,
        )
        for h in hits:
            chunks.append(f"[{h.title}] (score={h.score}) {h.summary}")
    text = "\n".join(chunks) if chunks else "未检索到相关内容。"
    yield {
        "type": "tool.result",
        "data": {"name": "kb_search_text", "preview": chunks[:3], "text": text},
    }


async def _kb_image(deps: PrismDeps, user_text: str) -> AsyncIterator[dict[str, Any]]:
    yield {"type": "tool.start", "data": {"name": "kb_search_image"}}
    lines: list[str] = []
    # 若有上一张图，优先以图搜图
    last = await resolve_last_image_asset(
        deps.db,
        conversation_id=deps.conversation_id,
        tenant_id=deps.tenant_id,
    )
    image_bytes = read_asset_bytes(last) if last else None
    for kb_id in deps.knowledge_base_ids:
        hits = await search_image(
            deps.db,
            tenant_id=deps.tenant_id,
            knowledge_base_id=kb_id,
            query_hint=user_text,
            image_bytes=image_bytes,
            top_k=3,
        )
        for h in hits:
            url = h.url or ""
            lines.append(f"{h.title} · 相似 {h.score} · {h.summary}" + (f" · {url}" if url else ""))
    text = "\n".join(lines) if lines else "未找到相似图片。"
    yield {
        "type": "tool.result",
        "data": {"name": "kb_search_image", "preview": lines[:3], "text": text},
    }

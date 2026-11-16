"""Agent 运行器：优先火山对话/生成；否则本地演示。"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Any

from app.models.asset import Asset
from app.services.agent.deps import PrismDeps
from app.services.agent.instructions import PRISM_SYSTEM_INSTRUCTIONS
from app.services.knowledge.search_text import search_text
from app.services.providers.volcengine.client import VolcengineArkClient


async def run_demo_agent(
    deps: PrismDeps,
    user_text: str,
    *,
    ark: VolcengineArkClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """产出与 SSE 对齐的事件。"""
    wants_image = bool(re.search(r"生成|出图|海报|封面|主视觉|画一张|做.*图", user_text))
    wants_video = bool(re.search(r"视频|短片|分镜|出片", user_text))

    # 知识库问答
    if deps.knowledge_base_ids and re.search(r"主色|规范|是什么|什么色|根据知识库", user_text):
        yield {"type": "tool.start", "data": {"name": "kb_search_text"}}
        snippets: list[str] = []
        for kb_id in deps.knowledge_base_ids:
            hits = await search_text(
                deps.db,
                tenant_id=deps.tenant_id,
                knowledge_base_id=kb_id,
                query=user_text,
                top_k=3,
            )
            snippets.extend(f"{h.title}: {h.summary}" for h in hits)
        yield {
            "type": "tool.result",
            "data": {"name": "kb_search_text", "preview": snippets[:3]},
        }
        context = "\n".join(snippets) if snippets else "（无命中）"
        if ark and ark.chat_model:
            answer = await ark.chat(
                [
                    {"role": "system", "content": PRISM_SYSTEM_INSTRUCTIONS},
                    {
                        "role": "user",
                        "content": f"根据以下知识库片段回答：\n{context}\n\n问题：{user_text}",
                    },
                ],
            )
        else:
            answer = "根据知识库：" + (context if snippets else "暂无命中，请补充文档。")
        yield {"type": "text.delta", "data": {"text": answer}}
        yield {"type": "message.done", "data": {"content": answer, "results": []}}
        return

    if wants_image:
        yield {"type": "tool.start", "data": {"name": "text_to_image"}}
        asset_id, result, key = await deps.media.generate_image(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=user_text,
        )
        asset = Asset(
            id=asset_id,
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            name=result.filename,
            kind="image",
            storage_key=key,
            mime_type=result.mime_type,
            meta=result.meta,
            source_conversation_id=deps.conversation_id,
        )
        deps.db.add(asset)
        card = {"id": asset_id, "label": "变体 A", "tone": "a"}
        deps.generated_assets.append(card)
        yield {
            "type": "tool.result",
            "data": {"name": "text_to_image", "asset_id": asset_id},
        }
        content = f"已完成生图（{deps.media.provider.name}），结果已写入资产中心。"
        yield {"type": "text.delta", "data": {"text": content}}
        yield {
            "type": "message.done",
            "data": {
                "content": content,
                "toolLabel": "text_to_image · 完成",
                "results": [card],
            },
        }
        return

    if wants_video:
        yield {"type": "tool.start", "data": {"name": "text_to_video"}}
        asset_id, result, key = await deps.media.generate_video(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=user_text,
        )
        asset = Asset(
            id=asset_id,
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            name=result.filename,
            kind="video",
            storage_key=key,
            mime_type=result.mime_type,
            meta=result.meta,
            source_conversation_id=deps.conversation_id,
        )
        deps.db.add(asset)
        card = {"id": asset_id, "label": "短视频", "tone": "c"}
        yield {
            "type": "tool.result",
            "data": {"name": "text_to_video", "asset_id": asset_id},
        }
        content = f"已完成视频生成（{deps.media.provider.name}），可在资产中心查看。"
        yield {"type": "text.delta", "data": {"text": content}}
        yield {
            "type": "message.done",
            "data": {
                "content": content,
                "toolLabel": "text_to_video · 完成",
                "results": [card],
            },
        }
        return

    # 纯文本：优先火山对话
    if ark and ark.chat_model:
        yield {"type": "text.delta", "data": {"text": ""}}
        content = await ark.chat(
            [
                {"role": "system", "content": PRISM_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": user_text},
            ],
        )
        yield {"type": "text.delta", "data": {"text": content}}
        yield {"type": "message.done", "data": {"content": content, "results": []}}
        return

    content = (
        f"这是 Prism 演示回复：已收到「{user_text[:80]}」。"
        "请在「设置 → 火山方舟」填写 API Key 并启用，即可走真实对话 / 生图 / 生视频 / 向量。"
    )
    yield {"type": "text.delta", "data": {"text": content}}
    yield {"type": "message.done", "data": {"content": content, "results": []}}

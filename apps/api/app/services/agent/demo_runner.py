"""Agent 运行器：意图识别 → 对话 / 生图 / 生视频 / 知识库（带多轮 + 压缩重注）。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.models.asset import Asset
from app.services.agent.context import assemble_chat_messages, build_system_prompt
from app.services.agent.deps import PrismDeps
from app.services.agent.instructions import PRISM_SYSTEM_INSTRUCTIONS
from app.services.agent.intent import classify_intent
from app.services.knowledge.search_text import search_text
from app.services.providers.volcengine.client import VolcengineArkClient


async def run_demo_agent(
    deps: PrismDeps,
    user_text: str,
    *,
    ark: VolcengineArkClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """产出与 SSE 对齐的事件。"""
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

    system = build_system_prompt(
        PRISM_SYSTEM_INSTRUCTIONS,
        workspace_id=deps.workspace_id,
        knowledge_base_ids=deps.knowledge_base_ids,
        compact_generation=deps.compact_generation,
    )

    # 知识库问答：历史 + 本轮 RAG 增强
    if intent == "knowledge" and has_knowledge:
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
        latest = (
            f"根据以下知识库片段回答（可结合对话上文）：\n{context}\n\n问题：{user_text}"
        )
        if ark and ark.chat_model:
            messages, stats = assemble_chat_messages(
                system=system,
                history=deps.history_messages,
                latest_user=latest,
            )
            yield {"type": "context.ready", "data": stats}
            answer = await _chat(deps, ark, messages)
        else:
            answer = "根据知识库：" + (context if snippets else "暂无命中，请补充文档。")
        yield {"type": "text.delta", "data": {"text": answer}}
        yield {"type": "message.done", "data": {"content": answer, "results": []}}
        return

    if intent == "image":
        yield {"type": "tool.start", "data": {"name": "text_to_image"}}
        prompt = _media_prompt(user_text, deps.history_messages)
        asset_id, result, key = await deps.media.generate_image(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=prompt,
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

    if intent == "video":
        yield {"type": "tool.start", "data": {"name": "text_to_video"}}
        prompt = _media_prompt(user_text, deps.history_messages)
        asset_id, result, key = await deps.media.generate_video(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=prompt,
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

    # 勾选了知识库但意图是 chat：仍检索并注入
    if has_knowledge and ark and ark.chat_model:
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
        rag = "\n".join(snippets) if snippets else "（无命中）"
        latest = (
            f"可参考知识库片段（没有则忽略）：\n{rag}\n\n用户问题：{user_text}"
        )
        messages, stats = assemble_chat_messages(
            system=system,
            history=deps.history_messages,
            latest_user=latest,
        )
        yield {"type": "context.ready", "data": stats}
        content = await _chat(deps, ark, messages)
        yield {"type": "text.delta", "data": {"text": content}}
        yield {"type": "message.done", "data": {"content": content, "results": []}}
        return

    # 纯文本：多轮历史 + 本轮
    if ark and ark.chat_model:
        messages, stats = assemble_chat_messages(
            system=system,
            history=deps.history_messages,
            latest_user=user_text,
        )
        yield {"type": "context.ready", "data": stats}
        yield {"type": "text.delta", "data": {"text": ""}}
        content = await _chat(deps, ark, messages)
        yield {"type": "text.delta", "data": {"text": content}}
        yield {"type": "message.done", "data": {"content": content, "results": []}}
        return

    content = (
        f"这是 Prism 演示回复：已收到「{user_text[:80]}」。"
        "请在「设置 → 火山方舟」填写 API Key 并启用，即可走真实对话 / 生图 / 生视频 / 向量。"
    )
    yield {"type": "text.delta", "data": {"text": content}}
    yield {"type": "message.done", "data": {"content": content, "results": []}}


async def _chat(
    deps: PrismDeps,
    ark: VolcengineArkClient,
    messages: list[dict[str, str]],
) -> str:
    """对话并记录 usage，供会话压缩计量。"""
    result = await ark.chat_completion(messages)
    deps.last_prompt_tokens = result.prompt_tokens
    deps.last_completion_tokens = result.completion_tokens
    deps.last_total_tokens = result.total_tokens
    return result.content


def _media_prompt(user_text: str, history: list[dict[str, str]]) -> str:
    """生图/视频：短追问时拼上最近一条用户描述，便于「再偏暖一点」类改稿。"""
    text = user_text.strip()
    if len(text) >= 40:
        return text
    prior_users = [
        m["content"]
        for m in history
        if m.get("role") == "user"
        and m.get("content")
        and not str(m["content"]).startswith("【会话摘要")
    ]
    if not prior_users:
        return text
    last = prior_users[-1].strip()
    if not last or last == text:
        return text
    return f"{last}\n\n补充要求：{text}"

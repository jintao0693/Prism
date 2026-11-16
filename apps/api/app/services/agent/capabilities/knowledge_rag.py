"""知识库检索能力工具。"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.services.agent.asset_memory import read_asset_bytes, resolve_last_image_asset
from app.services.agent.deps import PrismDeps
from app.services.knowledge.search_image import search_image
from app.services.knowledge.search_text import search_text


def register_knowledge_tools(agent: Agent[PrismDeps, str]) -> None:
    """注册文本检索与图搜图工具。"""

    @agent.tool
    async def kb_search_text(ctx: RunContext[PrismDeps], query: str) -> str:
        """在当前挂载的知识库中做文本检索，返回摘要。"""
        deps = ctx.deps
        if not deps.knowledge_base_ids:
            return "未挂载知识库，请先在对话中指定 knowledge_base_ids。"

        chunks: list[str] = []
        for kb_id in deps.knowledge_base_ids:
            hits = await search_text(
                deps.db,
                tenant_id=deps.tenant_id,
                knowledge_base_id=kb_id,
                query=query,
                top_k=3,
            )
            for h in hits:
                chunks.append(f"[{h.title}] (score={h.score}) {h.summary}")
        return "\n".join(chunks) if chunks else "未检索到相关内容。"

    @agent.tool
    async def kb_search_image(ctx: RunContext[PrismDeps], query_hint: str = "") -> str:
        """以文搜图；若本会话有上一张图则优先以图搜图。"""
        deps = ctx.deps
        if not deps.knowledge_base_ids:
            return "未挂载知识库。"

        last = await resolve_last_image_asset(
            deps.db,
            conversation_id=deps.conversation_id,
            tenant_id=deps.tenant_id,
        )
        image_bytes = read_asset_bytes(last) if last else None

        lines: list[str] = []
        for kb_id in deps.knowledge_base_ids:
            hits = await search_image(
                deps.db,
                tenant_id=deps.tenant_id,
                knowledge_base_id=kb_id,
                query_hint=query_hint or None,
                image_bytes=image_bytes,
                top_k=3,
            )
            for h in hits:
                extra = f" · {h.url}" if h.url else ""
                lines.append(f"{h.title} · 相似 {h.score} · {h.summary}{extra}")
        return "\n".join(lines) if lines else "未找到相似图片。"

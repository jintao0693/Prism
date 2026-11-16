"""知识库文本检索：有向量则语义召回，否则关键词回退。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeHitOut
from app.services.knowledge.embedding_utils import cosine_similarity, loads_embedding
from app.services.providers.registry import build_volcengine_client


async def search_text(
    session: AsyncSession,
    *,
    tenant_id: str,
    knowledge_base_id: str,
    query: str,
    top_k: int = 5,
) -> list[KnowledgeHitOut]:
    """在指定知识库内检索。"""
    rows = (
        await session.scalars(
            select(KnowledgeItem).where(
                KnowledgeItem.knowledge_base_id == knowledge_base_id,
                KnowledgeItem.tenant_id == tenant_id,
            ),
        )
    ).all()

    client = await build_volcengine_client(session, tenant_id)
    query_vec: list[float] | None = None
    if client and client.embedding_model:
        try:
            query_vec = await client.embed_text(query)
        except Exception:
            query_vec = None

    scored: list[KnowledgeHitOut] = []
    q = query.strip().lower()

    for item in rows:
        score = 0.5
        if query_vec:
            item_vec = loads_embedding(item.embedding_json)
            if item_vec:
                score = cosine_similarity(query_vec, item_vec)
        # 关键词兜底加权
        hay = f"{item.title}\n{item.content}".lower()
        if q and q in hay:
            score = max(score, 0.85)
        elif any(token and token in hay for token in q.split()):
            score = max(score, 0.7)

        scored.append(
            KnowledgeHitOut(
                id=item.id,
                title=item.title or item.id,
                summary=item.content[:120],
                score=round(float(score), 4),
                tone=item.tone,
            ),
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]

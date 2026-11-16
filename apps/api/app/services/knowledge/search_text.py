"""知识库文本检索：pgvector 优先，否则 embedding_json / 关键词回退。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeHitOut
from app.services.knowledge.embedding_utils import cosine_similarity, loads_embedding
from app.services.knowledge.vector_store import search_by_vector
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
    by_id = {item.id: item for item in rows}

    client = await build_volcengine_client(session, tenant_id)
    query_vec: list[float] | None = None
    if client and client.embedding_model:
        try:
            query_vec = await client.embed_text(query)
        except Exception:
            query_vec = None

    storage = get_storage()
    scored: list[KnowledgeHitOut] = []
    q = query.strip().lower()

    vector_hits: list[tuple[str, float]] | None = None
    if query_vec:
        vector_hits = await search_by_vector(
            session,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            query_vec=query_vec,
            top_k=max(top_k * 3, top_k),
        )

    if vector_hits is not None:
        for item_id, score in vector_hits:
            item = by_id.get(item_id)
            if not item:
                continue
            scored.append(_hit(item, score, storage))
        # 关键词补强：未进向量结果但标题/正文命中的
        seen = {h.id for h in scored}
        for item in rows:
            if item.id in seen:
                continue
            hay = f"{item.title}\n{item.content}".lower()
            if q and q in hay:
                scored.append(_hit(item, 0.85, storage))
            elif any(token and token in hay for token in q.split()):
                scored.append(_hit(item, 0.7, storage))
    else:
        for item in rows:
            score = 0.5
            if query_vec:
                item_vec = loads_embedding(item.embedding_json)
                if item_vec:
                    score = cosine_similarity(query_vec, item_vec)
            hay = f"{item.title}\n{item.content}".lower()
            if q and q in hay:
                score = max(score, 0.85)
            elif any(token and token in hay for token in q.split()):
                score = max(score, 0.7)
            scored.append(_hit(item, score, storage))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


def _hit(item: KnowledgeItem, score: float, storage) -> KnowledgeHitOut:
    url = storage.public_url(item.storage_key) if item.storage_key else None
    thumb = None
    if item.item_type == "image" and item.storage_key:
        thumb = storage.public_thumb_url(item.storage_key, mime_type="image/png")
    return KnowledgeHitOut(
        id=item.id,
        title=item.title or item.id,
        summary=item.content[:400],
        score=round(float(score), 4),
        tone=item.tone,
        itemType=item.item_type,
        url=url,
        thumbUrl=thumb or url,
    )

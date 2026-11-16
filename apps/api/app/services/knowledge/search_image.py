"""图搜图：pgvector 优先；否则 embedding_json；种子无向量则降权。"""

from __future__ import annotations

import base64

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeHitOut
from app.services.knowledge.embedding_utils import cosine_similarity, loads_embedding
from app.services.knowledge.vector_store import search_by_vector
from app.services.providers.registry import build_volcengine_client


async def search_image(
    session: AsyncSession,
    *,
    tenant_id: str,
    knowledge_base_id: str,
    query_hint: str | None = None,
    image_bytes: bytes | None = None,
    image_mime: str = "image/png",
    top_k: int = 5,
) -> list[KnowledgeHitOut]:
    """返回知识库中的图片条目排序结果。"""
    rows = (
        await session.scalars(
            select(KnowledgeItem).where(
                KnowledgeItem.knowledge_base_id == knowledge_base_id,
                KnowledgeItem.tenant_id == tenant_id,
                KnowledgeItem.item_type == "image",
            ),
        )
    ).all()
    by_id = {item.id: item for item in rows}

    client = await build_volcengine_client(session, tenant_id)
    query_vec: list[float] | None = None
    embed_error: str | None = None

    if client and client.embedding_model:
        try:
            if image_bytes:
                mime = image_mime if image_mime.startswith("image/") else "image/png"
                b64 = base64.b64encode(image_bytes).decode("ascii")
                data_url = f"data:{mime};base64,{b64}"
                query_vec = await client.embed_image_url(data_url)
            elif query_hint:
                query_vec = await client.embed_text(query_hint)
        except Exception as exc:
            query_vec = None
            embed_error = str(exc)
    elif image_bytes:
        raise ValueError("未配置 Embedding 模型，无法以图搜图")

    if image_bytes and not query_vec:
        raise ValueError(
            embed_error
            or "图片向量化失败。请确认图片边长 ≥ 14px，且 Embedding 模型可用。",
        )

    hint = (query_hint or "").lower()
    storage = get_storage()
    hits: list[KnowledgeHitOut] = []

    vector_hits: list[tuple[str, float]] | None = None
    if query_vec:
        vector_hits = await search_by_vector(
            session,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            query_vec=query_vec,
            top_k=max(top_k * 3, top_k),
            item_type="image",
        )

    if vector_hits is not None:
        for item_id, score in vector_hits:
            item = by_id.get(item_id)
            if not item:
                continue
            if hint and hint in f"{item.title} {item.content}".lower():
                score = max(score, min(0.98, score + 0.08))
            hits.append(_hit(item, score, storage))
        # 补上无索引的图片（降权）
        seen = {h.id for h in hits}
        for item in rows:
            if item.id in seen:
                continue
            score = 0.28
            if hint and hint in f"{item.title} {item.content}".lower():
                score = 0.75
            hits.append(_hit(item, score, storage))
    else:
        base = 0.72
        for i, item in enumerate(rows):
            score = max(0.4, base - i * 0.04)
            if not item.storage_key:
                score = min(score, 0.55)
            if query_vec:
                item_vec = loads_embedding(item.embedding_json)
                if item_vec:
                    score = cosine_similarity(query_vec, item_vec)
                else:
                    score = min(score, 0.28)
            if hint and hint in f"{item.title} {item.content}".lower():
                score = max(score, min(0.98, score + 0.08))
            hits.append(_hit(item, score, storage))

    hits.sort(key=lambda x: x.score, reverse=True)
    return hits[:top_k]


def _hit(item: KnowledgeItem, score: float, storage) -> KnowledgeHitOut:
    return KnowledgeHitOut(
        id=item.id,
        title=item.title,
        summary=item.content[:120] or "图片素材",
        score=round(float(score), 4),
        tone=item.tone,
        itemType=item.item_type,
        url=storage.public_url(item.storage_key) if item.storage_key else None,
    )

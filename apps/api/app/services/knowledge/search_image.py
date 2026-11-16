"""图搜图：优先多模态向量；否则回退图片条目+提示词。"""

from __future__ import annotations

import base64

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeHitOut
from app.services.knowledge.embedding_utils import cosine_similarity, loads_embedding
from app.services.providers.registry import build_volcengine_client


async def search_image(
    session: AsyncSession,
    *,
    tenant_id: str,
    knowledge_base_id: str,
    query_hint: str | None = None,
    image_bytes: bytes | None = None,
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

    client = await build_volcengine_client(session, tenant_id)
    query_vec: list[float] | None = None

    if client and client.embedding_model:
        try:
            if image_bytes:
                b64 = base64.b64encode(image_bytes).decode("ascii")
                data_url = f"data:image/png;base64,{b64}"
                query_vec = await client.embed_image_url(data_url)
            elif query_hint:
                query_vec = await client.embed_text(query_hint)
        except Exception:
            query_vec = None

    hint = (query_hint or "").lower()
    hits: list[KnowledgeHitOut] = []
    base = 0.9

    for i, item in enumerate(rows):
        score = max(0.55, base - i * 0.06)
        if query_vec:
            item_vec = loads_embedding(item.embedding_json)
            if item_vec:
                score = cosine_similarity(query_vec, item_vec)
        if hint and hint in f"{item.title} {item.content}".lower():
            score = max(score, min(0.98, score + 0.08))

        hits.append(
            KnowledgeHitOut(
                id=item.id,
                title=item.title,
                summary=item.content[:120] or "图片素材",
                score=round(float(score), 4),
                tone=item.tone,
            ),
        )

    hits.sort(key=lambda x: x.score, reverse=True)
    return hits[:top_k]

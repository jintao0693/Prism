"""知识库入库（文档/图片）骨架。"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem
from app.services.knowledge.embedding_utils import dumps_embedding
from app.services.providers.registry import build_volcengine_client


async def ingest_text_document(
    session: AsyncSession,
    *,
    tenant_id: str,
    knowledge_base_id: str,
    title: str,
    content: str,
) -> KnowledgeItem:
    """写入文档条目；若已配置火山向量模型则写入 embedding。"""
    embedding_json = None
    client = await build_volcengine_client(session, tenant_id)
    if client and client.embedding_model:
        try:
            vec = await client.embed_text(f"{title}\n{content}"[:2000])
            embedding_json = dumps_embedding(vec)
        except Exception:  # noqa: BLE001
            embedding_json = None

    item = KnowledgeItem(
        id=f"ki_{uuid.uuid4().hex[:12]}",
        knowledge_base_id=knowledge_base_id,
        tenant_id=tenant_id,
        item_type="document",
        title=title,
        content=content,
        embedding_json=embedding_json,
        tone="a",
    )
    session.add(item)
    await session.flush()
    return item

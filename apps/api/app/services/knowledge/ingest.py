"""知识库入库：文档 / 图片（含多模态向量）。"""

from __future__ import annotations

import base64
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.knowledge import KnowledgeItem
from app.services.knowledge.embedding_utils import dumps_embedding
from app.services.knowledge.vector_store import upsert_vector
from app.services.providers.registry import build_volcengine_client

logger = logging.getLogger(__name__)

_TONES = ("a", "b", "c", "d", "e", "f")
_MAX_IMAGE_BYTES = 8 * 1024 * 1024


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
    vec: list[float] | None = None
    client = await build_volcengine_client(session, tenant_id)
    if client and client.embedding_model:
        try:
            vec = await client.embed_text(f"{title}\n{content}"[:2000])
            embedding_json = dumps_embedding(vec)
        except Exception as exc:
            logger.warning("文档向量化失败: %s", exc)
            embedding_json = None
            vec = None

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
    if vec:
        await upsert_vector(
            session,
            item_id=item.id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            item_type="document",
            vec=vec,
        )
    return item


async def ingest_image(
    session: AsyncSession,
    *,
    tenant_id: str,
    workspace_id: str,
    knowledge_base_id: str,
    filename: str,
    data: bytes,
    content_type: str = "image/png",
    title: str | None = None,
    caption: str = "",
) -> KnowledgeItem:
    """上传图片入库并尽量写入多模态 embedding。"""
    if not data:
        raise ValueError("图片内容为空")
    if len(data) > _MAX_IMAGE_BYTES:
        raise ValueError("图片过大，请控制在 8MB 以内")

    storage = get_storage()
    key = storage.build_key(
        tenant_id,
        workspace_id,
        filename or "upload.png",
        folder="knowledge",
    )
    await storage.put_bytes(key, data, content_type=content_type)

    display_title = (title or filename or "未命名图片").strip() or "未命名图片"
    embedding_json = None
    vec: list[float] | None = None
    client = await build_volcengine_client(session, tenant_id)
    if client and client.embedding_model:
        try:
            mime = content_type if content_type.startswith("image/") else "image/png"
            b64 = base64.b64encode(data).decode("ascii")
            data_url = f"data:{mime};base64,{b64}"
            vec = await client.embed_image_url(data_url)
            embedding_json = dumps_embedding(vec)
        except Exception as exc:
            logger.warning("图片向量化失败: %s", exc)
            embedding_json = None
            vec = None

    tone = _TONES[uuid.uuid4().int % len(_TONES)]
    item = KnowledgeItem(
        id=f"ki_{uuid.uuid4().hex[:12]}",
        knowledge_base_id=knowledge_base_id,
        tenant_id=tenant_id,
        item_type="image",
        title=display_title,
        content=caption or display_title,
        storage_key=key,
        embedding_json=embedding_json,
        tone=tone,
    )
    session.add(item)
    await session.flush()
    if vec:
        await upsert_vector(
            session,
            item_id=item.id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            item_type="image",
            vec=vec,
        )
    return item

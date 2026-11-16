"""对已有条目重新写入向量。"""

from __future__ import annotations

import base64
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.knowledge import KnowledgeItem
from app.services.knowledge.embedding_utils import dumps_embedding
from app.services.knowledge.vector_store import upsert_vector
from app.services.providers.registry import build_volcengine_client

logger = logging.getLogger(__name__)


async def reembed_item(session: AsyncSession, item: KnowledgeItem) -> KnowledgeItem:
    """按条目类型重新向量化；失败抛 ValueError。"""
    client = await build_volcengine_client(session, item.tenant_id)
    if not client or not client.embedding_model:
        raise ValueError("未配置 Embedding 模型")

    try:
        if item.item_type == "document":
            vec = await client.embed_text(f"{item.title}\n{item.content}"[:2000])
        elif item.item_type == "image":
            if not item.storage_key:
                raise ValueError("该图片没有本地文件，无法向量化")
            storage = get_storage()
            path = storage.resolve_path(item.storage_key)
            if not path.exists():
                raise ValueError("图片文件缺失，请重新上传")
            data = path.read_bytes()
            mime = "image/png"
            if item.storage_key.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif item.storage_key.lower().endswith(".webp"):
                mime = "image/webp"
            b64 = base64.b64encode(data).decode("ascii")
            vec = await client.embed_image_url(f"data:{mime};base64,{b64}")
        else:
            raise ValueError(f"不支持的条目类型: {item.item_type}")
    except ValueError:
        raise
    except Exception as exc:
        logger.warning("重新向量化失败 %s: %s", item.id, exc)
        raise ValueError(str(exc)) from exc

    item.embedding_json = dumps_embedding(vec)
    await upsert_vector(
        session,
        item_id=item.id,
        tenant_id=item.tenant_id,
        knowledge_base_id=item.knowledge_base_id,
        item_type=item.item_type,
        vec=vec,
    )
    await session.flush()
    return item

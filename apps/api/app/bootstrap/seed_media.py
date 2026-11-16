"""为种子知识库图片 / 资产写入真实本地文件（可重复执行）。"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.png_util import solid_png
from app.bootstrap.seed import TENANT_ID, WS_SPRING
from app.core.storage import get_storage
from app.models.asset import Asset
from app.models.knowledge import KnowledgeItem

logger = logging.getLogger(__name__)

# 固定相对 key，便于幂等回填
_SEED_IMAGES: dict[str, tuple[str, tuple[int, int, int], str]] = {
    # item_id: (filename, rgb, caption已在 DB)
    "ki_2": ("spring_hero_v3.png", (15, 110, 106), "knowledge"),
    "ki_3": ("kv_storefront.jpg", (232, 168, 56), "knowledge"),
}

_SEED_ASSETS: dict[str, tuple[str, tuple[int, int, int]]] = {
    "a1": ("hero_01.png", (15, 110, 106)),
    "a2": ("hero_02.png", (232, 168, 56)),
    # 视频无真实文件时用海报图占位，便于缩略图
    "a3": ("teaser_poster.png", (90, 110, 130)),
}


async def ensure_demo_media(session: AsyncSession) -> None:
    """补齐种子条目/资产的 storage_key 与本地 PNG。"""
    storage = get_storage()
    fixed = 0

    for item_id, (filename, rgb, folder) in _SEED_IMAGES.items():
        item = await session.get(KnowledgeItem, item_id)
        if not item:
            continue
        if item.storage_key:
            path = storage.resolve_path(item.storage_key)
            if path.exists():
                continue
        key = f"{TENANT_ID}/{WS_SPRING}/{folder}/seed_{item_id}_{filename}"
        # jpg 扩展名也写 PNG 字节，浏览器仍可按内容显示；mime 记 png
        data = solid_png(64, 64, rgb)
        await storage.put_bytes(key, data, content_type="image/png")
        item.storage_key = key
        fixed += 1

    for asset_id, (filename, rgb) in _SEED_ASSETS.items():
        asset = await session.get(Asset, asset_id)
        if not asset:
            continue
        if asset.storage_key:
            path = storage.resolve_path(asset.storage_key)
            if path.exists():
                continue
        key = f"{TENANT_ID}/{WS_SPRING}/assets/seed_{asset_id}_{filename}"
        data = solid_png(64, 64, rgb)
        await storage.put_bytes(key, data, content_type="image/png")
        asset.storage_key = key
        if asset.kind == "video":
            asset.mime_type = "image/png"
            # 仍标记为 video，缩略图用海报
        else:
            asset.mime_type = "image/png"
        fixed += 1

    if fixed:
        await session.commit()
        logger.info("已回填 %s 个种子媒体文件", fixed)
    else:
        # 幂等检查：即使无写入也确认一次
        missing = (
            await session.scalars(
                select(KnowledgeItem).where(
                    KnowledgeItem.id.in_(list(_SEED_IMAGES.keys())),
                    KnowledgeItem.storage_key.is_(None),
                ),
            )
        ).all()
        if missing:
            logger.warning("仍有种子图片无 storage_key: %s", [m.id for m in missing])

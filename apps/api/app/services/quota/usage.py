"""本月生成用量：按资产实算 + 写回 QuotaUsage。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.quota import QuotaUsage

_SEED_ASSET_IDS = {"a1", "a2", "a3"}


def current_year_month() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m")


def _month_start_utc() -> datetime:
    now = datetime.now(tz=UTC)
    return datetime(now.year, now.month, 1, tzinfo=UTC)


def _is_upload(meta: str | None) -> bool:
    raw = meta or ""
    return '"mode": "upload"' in raw or '"mode":"upload"' in raw


async def count_generated_media(
    db: AsyncSession,
    tenant_id: str,
) -> tuple[int, int]:
    """统计本月「生成」的图/视频（排除上传与种子画廊）。"""
    start = _month_start_utc()
    rows = (
        await db.scalars(
            select(Asset).where(
                Asset.tenant_id == tenant_id,
                Asset.is_deleted.is_(False),
                Asset.created_at >= start,
            ),
        )
    ).all()
    images = 0
    videos = 0
    for asset in rows:
        if asset.id in _SEED_ASSET_IDS:
            continue
        if _is_upload(asset.meta):
            continue
        if asset.kind == "image":
            images += 1
        elif asset.kind == "video":
            videos += 1
    return images, videos


async def sync_quota_usage(
    db: AsyncSession,
    tenant_id: str,
) -> QuotaUsage:
    """按资产实算并写回本月 QuotaUsage。"""
    ym = current_year_month()
    images, videos = await count_generated_media(db, tenant_id)
    row = await db.scalar(
        select(QuotaUsage).where(
            QuotaUsage.tenant_id == tenant_id,
            QuotaUsage.year_month == ym,
        ),
    )
    if not row:
        row = QuotaUsage(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            year_month=ym,
            images_count=images,
            videos_count=videos,
        )
        db.add(row)
    else:
        row.images_count = images
        row.videos_count = videos
    await db.flush()
    return row


async def record_media_generation(
    db: AsyncSession,
    tenant_id: str,
    *,
    kind: Literal["image", "video"],
) -> None:
    """生成成功后即时 +1（最终以 sync 实算为准，避免漏计）。"""
    ym = current_year_month()
    row = await db.scalar(
        select(QuotaUsage).where(
            QuotaUsage.tenant_id == tenant_id,
            QuotaUsage.year_month == ym,
        ),
    )
    if not row:
        row = QuotaUsage(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            year_month=ym,
            images_count=0,
            videos_count=0,
        )
        db.add(row)
        await db.flush()
    if kind == "image":
        row.images_count = int(row.images_count or 0) + 1
    else:
        row.videos_count = int(row.videos_count or 0) + 1
    await db.flush()

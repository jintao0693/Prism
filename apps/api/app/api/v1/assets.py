"""资产接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.core.storage import get_storage
from app.models.asset import Asset
from app.schemas.asset import AssetOut

router = APIRouter(prefix="/assets", tags=["资产"])

# 演示用色调轮转
_TONES = ["a", "b", "c", "d", "e", "f"]


@router.get("", response_model=list[AssetOut])
async def list_assets(
    kind: str = Query(default="all"),
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[AssetOut]:
    """资产列表，可按 image/video 过滤。"""
    assert ctx.workspace_id
    stmt = select(Asset).where(
        Asset.tenant_id == ctx.tenant_id,
        Asset.workspace_id == ctx.workspace_id,
        Asset.is_deleted.is_(False),
    )
    if kind in {"image", "video"}:
        stmt = stmt.where(Asset.kind == kind)
    rows = (await db.scalars(stmt.order_by(Asset.created_at.desc()))).all()

    storage = get_storage()
    out: list[AssetOut] = []
    for i, asset in enumerate(rows):
        url = storage.public_url(asset.storage_key) if asset.storage_key else None
        out.append(
            AssetOut(
                id=asset.id,
                name=asset.name,
                kind=asset.kind,  # type: ignore[arg-type]
                meta=asset.meta,
                tone=_TONES[i % len(_TONES)],
                url=url,
            ),
        )
    return out

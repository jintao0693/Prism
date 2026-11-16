"""资产接口。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.core.storage import get_storage
from app.models.asset import Asset
from app.schemas.asset import AssetOut
from app.services.agent.asset_memory import dumps_asset_meta
from app.services.media.preview import asset_preview_fields

router = APIRouter(prefix="/assets", tags=["资产"])

# 演示用色调轮转
_TONES = ["a", "b", "c", "d", "e", "f"]
_ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}


def _to_out(asset: Asset, tone: str) -> AssetOut:
    preview = asset_preview_fields(asset)
    return AssetOut(
        id=asset.id,
        name=asset.name,
        kind=asset.kind,  # type: ignore[arg-type]
        meta=asset.meta,
        tone=tone,
        url=preview["url"],
        thumbUrl=preview["thumbUrl"],
        mimeType=preview["mimeType"],
        previewKind=preview["previewKind"],
    )


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
    return [_to_out(asset, _TONES[i % len(_TONES)]) for i, asset in enumerate(rows)]


@router.post("/upload", response_model=AssetOut)
async def upload_asset(
    file: UploadFile = File(...),
    conversation_id: str | None = Form(default=None),
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> AssetOut:
    """上传参考图到资产中心（可供对话 i2i / i2v 引用）。"""
    assert ctx.workspace_id
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPG / WEBP / GIF")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件")
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="单张图片请小于 12MB")

    filename = file.filename or "upload.png"
    storage = get_storage()
    key = storage.build_key(
        ctx.tenant_id,
        ctx.workspace_id,
        filename,
        folder="uploads",
    )
    await storage.put_bytes(key, data, content_type=content_type or "image/png")

    asset_id = f"asset_{uuid.uuid4().hex[:12]}"
    asset = Asset(
        id=asset_id,
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        name=filename,
        kind="image",
        storage_key=key,
        mime_type=content_type or "image/png",
        meta=dumps_asset_meta(
            prompt="",
            mode="upload",
            provider="user_upload",
            extra={"source": "upload"},
        ),
        source_conversation_id=conversation_id or None,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _to_out(asset, "a")

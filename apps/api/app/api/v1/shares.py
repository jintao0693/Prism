"""只读分享链接。"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.models.asset import Asset
from app.models.share import ShareLink
from app.schemas.share import ShareCreate, ShareOut, SharePublicOut
from app.services.media.preview import asset_preview_fields

router = APIRouter(prefix="/shares", tags=["分享"])


@router.post("", response_model=ShareOut)
async def create_share(
    body: ShareCreate,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> ShareOut:
    """为资产等创建只读分享令牌。"""
    assert ctx.workspace_id
    resource_type = (body.resource_type or "asset").strip().lower()
    if resource_type not in {"asset", "conversation"}:
        raise HTTPException(status_code=400, detail="仅支持 asset / conversation 分享")

    title = body.title.strip()
    if resource_type == "asset":
        asset = await db.get(Asset, body.resource_id)
        if (
            not asset
            or asset.tenant_id != ctx.tenant_id
            or asset.workspace_id != ctx.workspace_id
            or asset.is_deleted
        ):
            raise HTTPException(status_code=404, detail="资产不存在")
        if not title:
            title = asset.name

    expires_at = None
    if body.expires_in_hours:
        expires_at = datetime.now(UTC) + timedelta(hours=body.expires_in_hours)

    token = secrets.token_urlsafe(18)
    link = ShareLink(
        id=f"sh_{uuid.uuid4().hex[:10]}",
        token=token,
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        resource_type=resource_type,
        resource_id=body.resource_id,
        title=title or "分享",
        note=body.note or "",
        expires_at=expires_at,
        created_by=ctx.user.id,
    )
    db.add(link)
    await db.commit()

    return ShareOut(
        id=link.id,
        token=token,
        title=link.title,
        resourceType=resource_type,
        resourceId=body.resource_id,
        sharePath=f"/share/{token}",
    )


@router.get("/public/{token}", response_model=SharePublicOut)
async def get_public_share(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> SharePublicOut:
    """无需登录的公开分享页数据。"""
    from sqlalchemy import select

    link = await db.scalar(select(ShareLink).where(ShareLink.token == token))
    if not link:
        raise HTTPException(status_code=404, detail="分享不存在或已失效")
    if link.expires_at and link.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="分享已过期")

    if link.resource_type == "asset":
        asset = await db.get(Asset, link.resource_id)
        if not asset or asset.is_deleted:
            raise HTTPException(status_code=404, detail="资源已删除")
        preview = asset_preview_fields(asset)
        return SharePublicOut(
            title=link.title,
            note=link.note,
            resourceType=link.resource_type,
            resourceId=link.resource_id,
            url=preview["url"],
            thumbUrl=preview["thumbUrl"],
            mimeType=preview["mimeType"],
            previewKind=preview["previewKind"],
            kind=asset.kind,
        )

    return SharePublicOut(
        title=link.title,
        note=link.note,
        resourceType=link.resource_type,
        resourceId=link.resource_id,
    )
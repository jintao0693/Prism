"""工作空间接口。"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    RequestContext,
    get_current_context,
    require_min_role,
    require_workspace,
)
from app.core.db import get_db
from app.models.asset import Asset
from app.models.conversation import Conversation
from app.models.tenant import Membership
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    BrandPackOut,
    BrandPackUpdate,
    WorkspaceMemberOut,
    WorkspaceOut,
    WorkspaceUpdate,
)
from app.services.brand.pack import get_workspace_brand_pack, save_workspace_brand_pack

router = APIRouter(prefix="/workspaces", tags=["工作空间"])


def _relative_label(dt: datetime) -> str:
    """简易相对时间文案。"""
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    delta = now - dt
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return "刚刚"
    if hours < 24:
        return f"{hours} 小时前"
    days = hours // 24
    if days == 1:
        return "昨天"
    return f"{days} 天前"


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceOut]:
    """列出当前租户下工作空间。"""
    rows = (
        await db.scalars(
            select(Workspace).where(Workspace.tenant_id == ctx.tenant_id),
        )
    ).all()

    result: list[WorkspaceOut] = []
    for ws in rows:
        conv_count = await db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.workspace_id == ws.id,
                Conversation.tenant_id == ctx.tenant_id,
            ),
        )
        asset_count = await db.scalar(
            select(func.count())
            .select_from(Asset)
            .where(
                Asset.workspace_id == ws.id,
                Asset.tenant_id == ctx.tenant_id,
                Asset.is_deleted.is_(False),
            ),
        )
        result.append(
            WorkspaceOut(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                status=ws.status,
                conversationCount=int(conv_count or 0),
                assetCount=int(asset_count or 0),
                updatedAtLabel=_relative_label(ws.updated_at),
            ),
        )
    return result


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: str,
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOut:
    """获取单个工作空间。"""
    ws = await db.get(Workspace, workspace_id)
    if not ws or ws.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="工作空间不存在")

    conv_count = await db.scalar(
        select(func.count())
        .select_from(Conversation)
        .where(
            Conversation.workspace_id == ws.id,
            Conversation.tenant_id == ctx.tenant_id,
        ),
    )
    asset_count = await db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(
            Asset.workspace_id == ws.id,
            Asset.tenant_id == ctx.tenant_id,
            Asset.is_deleted.is_(False),
        ),
    )
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        status=ws.status,
        conversationCount=int(conv_count or 0),
        assetCount=int(asset_count or 0),
        updatedAtLabel=_relative_label(ws.updated_at),
    )


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: str,
    body: WorkspaceUpdate,
    ctx: RequestContext = Depends(require_min_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOut:
    """重命名或归档工作空间。"""
    ws = await db.get(Workspace, workspace_id)
    if not ws or ws.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="工作空间不存在")
    if body.name is not None:
        ws.name = body.name
    if body.description is not None:
        ws.description = body.description
    if body.status is not None:
        ws.status = body.status
    ws.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(ws)
    return await get_workspace(workspace_id, ctx, db)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberOut])
async def list_workspace_members(
    workspace_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceMemberOut]:
    """当前租户成员（工作空间级演示）。"""
    assert ctx.workspace_id == workspace_id
    rows = (
        await db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.tenant_id == ctx.tenant_id)
            .order_by(User.name),
        )
    ).all()
    out: list[WorkspaceMemberOut] = []
    for membership, user in rows:
        out.append(
            WorkspaceMemberOut(
                userId=user.id,
                name=user.name,
                email=user.email,
                role=membership.role,
                avatarText=user.avatar_text,
            ),
        )
    return out


@router.get("/{workspace_id}/brand-pack", response_model=BrandPackOut)
async def get_brand_pack(
    workspace_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> BrandPackOut:
    """读取 Brand Pack。"""
    assert ctx.workspace_id == workspace_id
    pack = await get_workspace_brand_pack(db, workspace_id)
    data = pack.to_dict()
    return BrandPackOut.model_validate(data)


@router.put("/{workspace_id}/brand-pack", response_model=BrandPackOut)
async def put_brand_pack(
    workspace_id: str,
    body: BrandPackUpdate,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> BrandPackOut:
    """保存 Brand Pack。"""
    assert ctx.workspace_id == workspace_id
    current = (await get_workspace_brand_pack(db, workspace_id)).to_dict()
    patch = body.model_dump(by_alias=True, exclude_none=True)
    merged = {**current, **patch}
    pack = await save_workspace_brand_pack(db, workspace_id, merged)
    await db.commit()
    return BrandPackOut.model_validate(pack.to_dict())


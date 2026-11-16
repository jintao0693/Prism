"""工作空间接口。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, get_current_context
from app.core.db import get_db
from app.models.asset import Asset
from app.models.conversation import Conversation
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["工作空间"])


def _relative_label(dt: datetime) -> str:
    """简易相对时间文案。"""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
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
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="工作空间不存在")

    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        status=ws.status,
        conversationCount=0,
        assetCount=0,
        updatedAtLabel=_relative_label(ws.updated_at),
    )


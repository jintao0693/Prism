"""API 依赖：当前用户 / 租户 / 工作空间上下文。"""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import try_decode_access_token
from app.models.tenant import Membership
from app.models.user import User
from app.models.workspace import Workspace

security = HTTPBearer(auto_error=False)


@dataclass
class RequestContext:
    """一次请求的租户上下文（强制隔离用）。"""

    user: User
    tenant_id: str
    role: str
    workspace_id: str | None = None


async def get_current_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    db: AsyncSession = Depends(get_db),
) -> RequestContext:
    """解析 JWT，校验成员关系，注入租户上下文。"""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    payload = try_decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效")

    user_id = str(payload.get("sub", ""))
    tenant_id = str(payload.get("tenant_id") or x_tenant_id or "")
    role = str(payload.get("role", "viewer"))

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    membership = await db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user_id,
        ),
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无租户权限")

    return RequestContext(
        user=user,
        tenant_id=tenant_id,
        role=membership.role or role,
    )


async def require_workspace(
    ctx: RequestContext = Depends(get_current_context),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    db: AsyncSession = Depends(get_db),
) -> RequestContext:
    """要求并校验工作空间归属当前租户。"""
    if not x_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少 X-Workspace-Id",
        )

    workspace = await db.get(Workspace, x_workspace_id)
    if not workspace or workspace.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作空间不存在")

    ctx.workspace_id = x_workspace_id
    return ctx

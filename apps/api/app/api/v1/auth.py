"""鉴权接口。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, get_current_context
from app.core.db import get_db
from app.core.security import create_access_token, verify_password
from app.models.tenant import Membership, Tenant
from app.models.user import User
from app.schemas.auth import LoginRequest, TenantOut, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["鉴权"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """邮箱密码登录，返回 JWT。"""
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    membership = await db.scalar(select(Membership).where(Membership.user_id == user.id))
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户未加入租户")

    tenant = await db.get(Tenant, membership.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")

    token = create_access_token(
        user.id,
        tenant_id=tenant.id,
        role=membership.role,
    )
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            avatarText=user.avatar_text,
            role=membership.role,
        ),
        tenant=TenantOut.model_validate(tenant),
    )


@router.get("/me", response_model=UserOut)
async def me(ctx: RequestContext = Depends(get_current_context)) -> UserOut:
    """当前用户。"""
    return UserOut(
        id=ctx.user.id,
        name=ctx.user.name,
        email=ctx.user.email,
        avatarText=ctx.user.avatar_text,
        role=ctx.role,
    )

"""鉴权相关 Schema。"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求。"""

    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    """用户信息。"""

    id: str
    name: str
    email: str
    avatar_text: str = Field(alias="avatarText")
    role: str

    model_config = {"populate_by_name": True, "from_attributes": True}


class TenantOut(BaseModel):
    """租户信息。"""

    id: str
    name: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录成功返回。"""

    access_token: str
    token_type: str = "bearer"
    user: UserOut
    tenant: TenantOut

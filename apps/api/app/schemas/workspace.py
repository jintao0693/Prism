"""工作空间 Schema。"""

from pydantic import BaseModel, Field


class WorkspaceUpdate(BaseModel):
    """更新工作空间（重命名 / 归档等）。"""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|evergreen|archived)$")


class WorkspaceMemberOut(BaseModel):
    """成员列表项。"""

    user_id: str = Field(alias="userId")
    name: str
    email: str
    role: str
    avatar_text: str = Field(alias="avatarText")

    model_config = {"populate_by_name": True}


class BrandPackOut(BaseModel):
    """Brand Pack 只读视图。"""

    name: str
    primary_color: str = Field(alias="primaryColor")
    accent_color: str = Field(alias="accentColor")
    primary_color_name: str = Field(alias="primaryColorName")
    accent_color_name: str = Field(alias="accentColorName")
    keywords: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    tone_hint: str = Field(alias="toneHint", default="")

    model_config = {"populate_by_name": True}


class BrandPackUpdate(BaseModel):
    """Brand Pack 保存载荷（字段均可选，未传则保留默认）。"""

    name: str | None = None
    primary_color: str | None = Field(default=None, alias="primaryColor")
    accent_color: str | None = Field(default=None, alias="accentColor")
    primary_color_name: str | None = Field(default=None, alias="primaryColorName")
    accent_color_name: str | None = Field(default=None, alias="accentColorName")
    keywords: list[str] | None = None
    forbidden: list[str] | None = None
    tone_hint: str | None = Field(default=None, alias="toneHint")

    model_config = {"populate_by_name": True}


class WorkspaceOut(BaseModel):
    """工作空间列表项。"""

    id: str
    name: str
    description: str
    status: str
    conversation_count: int = Field(alias="conversationCount", default=0)
    asset_count: int = Field(alias="assetCount", default=0)
    updated_at_label: str = Field(alias="updatedAtLabel", default="")

    model_config = {"populate_by_name": True, "from_attributes": True}


class WorkspaceCreate(BaseModel):
    """创建工作空间。"""

    name: str = Field(min_length=1, max_length=128)
    description: str = ""

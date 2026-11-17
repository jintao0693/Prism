"""分享链接 Schema。"""

from pydantic import BaseModel, Field


class ShareCreate(BaseModel):
    """创建只读分享。"""

    resource_type: str = Field(alias="resourceType", default="asset")
    resource_id: str = Field(alias="resourceId", min_length=1)
    title: str = ""
    note: str = ""
    expires_in_hours: int | None = Field(default=None, alias="expiresInHours", ge=1, le=720)

    model_config = {"populate_by_name": True}


class ShareOut(BaseModel):
    """创建分享响应。"""

    id: str
    token: str
    title: str
    resource_type: str = Field(alias="resourceType")
    resource_id: str = Field(alias="resourceId")
    share_path: str = Field(alias="sharePath")

    model_config = {"populate_by_name": True}


class SharePublicOut(BaseModel):
    """公开分享页载荷。"""

    title: str
    note: str
    resource_type: str = Field(alias="resourceType")
    resource_id: str = Field(alias="resourceId")
    url: str | None = None
    thumb_url: str | None = Field(default=None, alias="thumbUrl")
    mime_type: str | None = Field(default=None, alias="mimeType")
    preview_kind: str = Field(default="image", alias="previewKind")
    kind: str = "image"

    model_config = {"populate_by_name": True}
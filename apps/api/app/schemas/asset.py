"""资产 Schema。"""

from typing import Literal

from pydantic import BaseModel, Field


class AssetOut(BaseModel):
    """资产列表项。"""

    id: str
    name: str
    kind: Literal["image", "video"]
    meta: str
    tone: str = "a"
    url: str | None = None
    thumb_url: str | None = Field(default=None, alias="thumbUrl")
    mime_type: str | None = Field(default=None, alias="mimeType")
    # 预览策略：image | video | poster（视频但文件是海报图）
    preview_kind: Literal["image", "video", "poster"] = Field(
        default="image",
        alias="previewKind",
    )

    model_config = {"populate_by_name": True, "from_attributes": True}


class AssetListQuery(BaseModel):
    """资产筛选。"""

    kind: Literal["all", "image", "video"] = "all"

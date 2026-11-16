"""通用响应模型。"""

from pydantic import BaseModel, Field


class OkResponse(BaseModel):
    """简单成功响应。"""

    ok: bool = True
    message: str = "ok"


class UsageSummaryOut(BaseModel):
    """用量摘要（对齐前端）。含软上限供接近时轻提示。"""

    images_this_month: int = Field(alias="imagesThisMonth")
    videos_this_month: int = Field(alias="videosThisMonth")
    images_soft_limit: int = Field(alias="imagesSoftLimit", default=50)
    videos_soft_limit: int = Field(alias="videosSoftLimit", default=10)

    model_config = {"populate_by_name": True}

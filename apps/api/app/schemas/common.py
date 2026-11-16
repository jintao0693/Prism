"""通用响应模型。"""

from pydantic import BaseModel, Field


class OkResponse(BaseModel):
    """简单成功响应。"""

    ok: bool = True
    message: str = "ok"


class UsageSummaryOut(BaseModel):
    """用量摘要（对齐前端）。"""

    images_this_month: int = Field(alias="imagesThisMonth")
    videos_this_month: int = Field(alias="videosThisMonth")

    model_config = {"populate_by_name": True}

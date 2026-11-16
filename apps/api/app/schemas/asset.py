"""资产 Schema。"""

from typing import Literal

from pydantic import BaseModel


class AssetOut(BaseModel):
    """资产列表项。"""

    id: str
    name: str
    kind: Literal["image", "video"]
    meta: str
    tone: str = "a"
    url: str | None = None

    model_config = {"from_attributes": True}


class AssetListQuery(BaseModel):
    """资产筛选。"""

    kind: Literal["all", "image", "video"] = "all"

"""知识库 Schema。"""

from pydantic import BaseModel, Field


class KnowledgeBaseOut(BaseModel):
    """知识库。"""

    id: str
    name: str
    description: str
    document_count: int = Field(alias="documentCount", default=0)
    image_count: int = Field(alias="imageCount", default=0)

    model_config = {"populate_by_name": True}


class KnowledgeHitOut(BaseModel):
    """检索命中。"""

    id: str
    title: str
    summary: str
    score: float
    tone: str


class SearchTextRequest(BaseModel):
    """文本检索。"""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50, alias="topK")

    model_config = {"populate_by_name": True}


class SearchImageRequest(BaseModel):
    """图搜图（演示：可用 query 提示代替真实图像向量）。"""

    query_hint: str | None = Field(default=None, alias="queryHint")
    asset_id: str | None = Field(default=None, alias="assetId")
    top_k: int = Field(default=5, ge=1, le=50, alias="topK")

    model_config = {"populate_by_name": True}


class KnowledgeBaseCreate(BaseModel):
    """新建知识库。"""

    name: str
    description: str = ""

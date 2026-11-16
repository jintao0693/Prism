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
    item_type: str = Field(default="image", alias="itemType")
    url: str | None = None
    thumb_url: str | None = Field(default=None, alias="thumbUrl")

    model_config = {"populate_by_name": True}


class KnowledgeItemOut(BaseModel):
    """知识库条目。"""

    id: str
    title: str
    item_type: str = Field(alias="itemType")
    summary: str = ""
    url: str | None = None
    thumb_url: str | None = Field(default=None, alias="thumbUrl")
    has_embedding: bool = Field(alias="hasEmbedding", default=False)

    model_config = {"populate_by_name": True}


class SearchTextRequest(BaseModel):
    """文本检索。"""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50, alias="topK")

    model_config = {"populate_by_name": True}


class SearchImageRequest(BaseModel):
    """以文搜图 / 兼容旧客户端。"""

    query_hint: str | None = Field(default=None, alias="queryHint")
    asset_id: str | None = Field(default=None, alias="assetId")
    top_k: int = Field(default=5, ge=1, le=50, alias="topK")

    model_config = {"populate_by_name": True}


class KnowledgeBaseCreate(BaseModel):
    """新建知识库。"""

    name: str
    description: str = ""


class DocumentIngestRequest(BaseModel):
    """文本入库。"""

    title: str = Field(min_length=1)
    content: str = Field(min_length=1)

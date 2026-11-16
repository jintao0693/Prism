"""设置 / 供应商配置 Schema。"""

from pydantic import BaseModel, Field


class VolcengineProviderOut(BaseModel):
    """火山方舟配置（密钥脱敏）。"""

    provider: str = "volcengine_ark"
    enabled: bool = False
    base_url: str
    chat_model: str = Field(alias="chatModel")
    image_model: str = Field(alias="imageModel")
    video_model: str = Field(alias="videoModel")
    embedding_model: str = Field(alias="embeddingModel")
    api_key_masked: str = Field(alias="apiKeyMasked")
    has_api_key: bool = Field(alias="hasApiKey")
    note: str = ""

    model_config = {"populate_by_name": True}


class VolcengineProviderUpdate(BaseModel):
    """更新火山配置；apiKey 留空表示不修改。"""

    enabled: bool | None = None
    base_url: str | None = Field(default=None, alias="baseUrl")
    chat_model: str | None = Field(default=None, alias="chatModel")
    image_model: str | None = Field(default=None, alias="imageModel")
    video_model: str | None = Field(default=None, alias="videoModel")
    embedding_model: str | None = Field(default=None, alias="embeddingModel")
    api_key: str | None = Field(default=None, alias="apiKey")
    note: str | None = None

    model_config = {"populate_by_name": True}


class ProviderTestResult(BaseModel):
    """连通性测试结果。"""

    ok: bool
    message: str
    detail: str | None = None

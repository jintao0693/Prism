"""工作空间 Schema。"""

from pydantic import BaseModel, Field


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

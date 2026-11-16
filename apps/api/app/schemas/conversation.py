"""对话 Schema。"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationSummaryOut(BaseModel):
    """会话列表项。"""

    id: str
    title: str
    kind: str
    updated_at_label: str = Field(alias="updatedAtLabel")
    thumb_tone: str = Field(alias="thumbTone", default="a")

    model_config = {"populate_by_name": True}


class GenerationResultOut(BaseModel):
    """生成结果卡片。"""

    id: str
    label: str
    tone: str
    kind: str | None = None
    url: str | None = None
    thumb_url: str | None = Field(default=None, alias="thumbUrl")
    mime_type: str | None = Field(default=None, alias="mimeType")
    preview_kind: str | None = Field(default=None, alias="previewKind")
    parent_asset_id: str | None = Field(default=None, alias="parentAssetId")

    model_config = {"populate_by_name": True}


class ChatMessageOut(BaseModel):
    """消息。"""

    id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_label: str | None = Field(default=None, alias="toolLabel")
    results: list[GenerationResultOut] | None = None
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class SendMessageRequest(BaseModel):
    """发送消息。"""

    content: str = Field(min_length=1)
    knowledge_base_ids: list[str] = Field(default_factory=list, alias="knowledgeBaseIds")
    # 本轮显式参考图（资产中心 / 对话上传），优先于「上一张生成图」
    reference_asset_ids: list[str] = Field(
        default_factory=list,
        alias="referenceAssetIds",
        max_length=4,
    )

    model_config = {"populate_by_name": True}


class ConversationCreate(BaseModel):
    """新建会话。"""

    title: str = "新对话"
    kind: str = "chat"


class ConversationUpdate(BaseModel):
    """更新会话（重命名等）。"""

    title: str = Field(min_length=1, max_length=255)


class ConversationDetailOut(BaseModel):
    """会话详情（含压缩检查点）。"""

    id: str
    title: str
    kind: str
    updated_at_label: str = Field(alias="updatedAtLabel")
    summary_text: str | None = Field(default=None, alias="summaryText")
    compact_generation: int = Field(alias="compactGeneration", default=0)
    context_tokens_estimate: int = Field(alias="contextTokensEstimate", default=0)

    model_config = {"populate_by_name": True}


class CompactOut(BaseModel):
    """手动 / 自动压缩结果。"""

    did_compact: bool = Field(alias="didCompact")
    generation: int
    summary_chars: int = Field(alias="summaryChars", default=0)
    reason: str = ""
    context_tokens_estimate: int = Field(alias="contextTokensEstimate", default=0)

    model_config = {"populate_by_name": True}


class SseEvent(BaseModel):
    """SSE 事件载荷。"""

    type: str
    data: dict[str, Any] = Field(default_factory=dict)

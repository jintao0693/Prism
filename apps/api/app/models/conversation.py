"""对话与消息。"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin, WorkspaceScopedMixin


class Conversation(Base, TimestampMixin, WorkspaceScopedMixin):
    """一次创作/问答会话。"""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="新对话")
    # chat | image | video
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="chat")

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    """会话中的一条消息。"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversations.id"),
        index=True,
        nullable=False,
    )
    # user | assistant | system | tool
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 工具标签 / 结果 JSON 字符串（演示期简化）
    tool_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

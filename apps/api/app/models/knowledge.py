"""知识库与条目（含向量占位字段）。"""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin, WorkspaceScopedMixin


class KnowledgeBase(Base, TimestampMixin, WorkspaceScopedMixin):
    """知识库容器。"""

    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    items: Mapped[list["KnowledgeItem"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )


class KnowledgeItem(Base, TimestampMixin):
    """知识条目：文档块或图片。"""

    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("knowledge_bases.id"),
        index=True,
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # document | image
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # 向量序列化占位（生产应迁 pgvector / 外部向量库）
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 图搜演示用相似度标签
    tone: Mapped[str] = mapped_column(String(8), nullable=False, default="a")

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="items")


class KnowledgeSegment(Base, TimestampMixin):
    """视频片段检索占位表（Phase 2）。"""

    __tablename__ = "knowledge_segments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    asset_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    t_start_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    t_end_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    caption: Mapped[str] = mapped_column(Text, nullable=False, default="")
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)

"""资产元数据。"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, WorkspaceScopedMixin


class Asset(Base, TimestampMixin, WorkspaceScopedMixin):
    """图片 / 视频等生成或上传产物。"""

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # image | video
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/octet-stream")
    meta: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 血缘（简版）
    source_conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # soft delete
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)

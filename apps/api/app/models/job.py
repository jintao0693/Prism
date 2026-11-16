"""异步生成任务。"""

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, WorkspaceScopedMixin


class GenerationJob(Base, TimestampMixin, WorkspaceScopedMixin):
    """生图 / 生视频等异步作业。"""

    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # image | video | ingest
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # queued | running | succeeded | failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    external_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    progress_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_elapsed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mode: Mapped[str | None] = mapped_column(String(32), nullable=True)

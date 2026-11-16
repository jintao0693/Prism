"""用量配额（骨架）。"""

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, TenantScopedMixin


class QuotaUsage(Base, TimestampMixin, TenantScopedMixin):
    """按月统计生成用量。"""

    __tablename__ = "quota_usages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "year_month", name="uq_quota_tenant_month"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    images_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    videos_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

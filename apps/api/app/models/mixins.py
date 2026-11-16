"""模型公共字段混入。"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """创建 / 更新时间。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class TenantScopedMixin:
    """租户隔离字段。"""

    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)


class WorkspaceScopedMixin(TenantScopedMixin):
    """租户 + 工作空间隔离。"""

    workspace_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

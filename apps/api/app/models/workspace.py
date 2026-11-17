"""工作空间。"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin


class Workspace(Base, TimestampMixin, TenantScopedMixin):
    """租户下的工作空间（对话/知识库/资产归属此层）。"""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # active | evergreen | archived
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    # Brand Pack JSON（主色/禁忌/气质等）
    brand_pack_json: Mapped[str] = mapped_column(Text, nullable=False, default="")

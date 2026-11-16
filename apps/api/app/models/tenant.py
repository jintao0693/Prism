"""租户与成员关系。"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin


class Tenant(Base, TimestampMixin):
    """租户（SaaS 组织）。"""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="tenant")


class Membership(Base, TimestampMixin):
    """用户在租户内的角色。"""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    # owner | admin | creator | viewer
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="creator")

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")

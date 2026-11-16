"""租户级模型供应商配置（首期：火山方舟）。"""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin


class TenantProviderConfig(Base, TimestampMixin, TenantScopedMixin):
    """
    每个租户一套供应商配置。
    api_key 存加密密文；模型 ID 可为方舟 Model ID 或 Endpoint ID。
    """

    __tablename__ = "tenant_provider_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", name="uq_tenant_provider"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # volcengine_ark | openai | ...
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="volcengine_ark")
    # 是否启用该供应商
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    # 加密后的 API Key
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 方舟 Base URL
    base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="https://ark.cn-beijing.volces.com/api/v3",
    )
    # 各能力模型 ID（用户在控制台开通后的 ID）
    chat_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    image_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    video_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    # 备注
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")

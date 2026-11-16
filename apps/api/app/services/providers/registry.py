"""按租户加载供应商配置与客户端。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.models.provider_config import TenantProviderConfig
from app.services.providers.volcengine.client import VolcengineArkClient

PROVIDER_VOLCENGINE = "volcengine_ark"

# 设置页默认占位（用户需换成自己在方舟控制台开通的 Model/Endpoint ID）
DEFAULT_VOLCENGINE = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "chat_model": "doubao-seed-1-6-251015",
    "image_model": "doubao-seedream-4-0-250828",
    "video_model": "doubao-seedance-1-0-pro-250528",
    "embedding_model": "doubao-embedding-vision-250615",
}


@dataclass
class ProviderSnapshot:
    """供 API 返回的配置快照（密钥脱敏）。"""

    provider: str
    enabled: bool
    base_url: str
    chat_model: str
    image_model: str
    video_model: str
    embedding_model: str
    api_key_masked: str
    has_api_key: bool
    note: str


async def get_or_create_volcengine_config(
    session: AsyncSession,
    tenant_id: str,
) -> TenantProviderConfig:
    """获取或创建火山配置行。"""
    row = await session.scalar(
        select(TenantProviderConfig).where(
            TenantProviderConfig.tenant_id == tenant_id,
            TenantProviderConfig.provider == PROVIDER_VOLCENGINE,
        ),
    )
    if row:
        return row

    import uuid

    row = TenantProviderConfig(
        id=f"pc_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        provider=PROVIDER_VOLCENGINE,
        enabled=False,
        api_key_encrypted="",
        base_url=DEFAULT_VOLCENGINE["base_url"],
        chat_model=DEFAULT_VOLCENGINE["chat_model"],
        image_model=DEFAULT_VOLCENGINE["image_model"],
        video_model=DEFAULT_VOLCENGINE["video_model"],
        embedding_model=DEFAULT_VOLCENGINE["embedding_model"],
        note="请填写火山方舟 API Key，并将模型 ID 换成控制台中已开通的 ID",
    )
    session.add(row)
    await session.flush()
    return row


def to_snapshot(row: TenantProviderConfig) -> ProviderSnapshot:
    """ORM → 脱敏快照。"""
    plain = decrypt_secret(row.api_key_encrypted) if row.api_key_encrypted else ""
    return ProviderSnapshot(
        provider=row.provider,
        enabled=row.enabled,
        base_url=row.base_url,
        chat_model=row.chat_model,
        image_model=row.image_model,
        video_model=row.video_model,
        embedding_model=row.embedding_model,
        api_key_masked=mask_secret(plain),
        has_api_key=bool(plain),
        note=row.note,
    )


async def save_volcengine_config(
    session: AsyncSession,
    tenant_id: str,
    *,
    api_key: str | None,
    enabled: bool | None,
    base_url: str | None,
    chat_model: str | None,
    image_model: str | None,
    video_model: str | None,
    embedding_model: str | None,
    note: str | None,
) -> TenantProviderConfig:
    """更新火山配置；api_key 为空字符串表示不改动。"""
    row = await get_or_create_volcengine_config(session, tenant_id)
    if enabled is not None:
        row.enabled = enabled
    if base_url is not None:
        row.base_url = base_url.rstrip("/")
    if chat_model is not None:
        row.chat_model = chat_model
    if image_model is not None:
        row.image_model = image_model
    if video_model is not None:
        row.video_model = video_model
    if embedding_model is not None:
        row.embedding_model = embedding_model
    if note is not None:
        row.note = note
    if api_key is not None and api_key.strip():
        # 仅当用户提交了新 Key 才覆盖
        row.api_key_encrypted = encrypt_secret(api_key.strip())
    await session.flush()
    return row


async def build_volcengine_client(
    session: AsyncSession,
    tenant_id: str,
) -> VolcengineArkClient | None:
    """
    若租户已启用且配置了 Key，返回客户端；否则 None（走演示 Provider）。
    """
    row = await session.scalar(
        select(TenantProviderConfig).where(
            TenantProviderConfig.tenant_id == tenant_id,
            TenantProviderConfig.provider == PROVIDER_VOLCENGINE,
        ),
    )
    if not row or not row.enabled:
        return None
    api_key = decrypt_secret(row.api_key_encrypted)
    if not api_key:
        return None
    return VolcengineArkClient(
        api_key,
        base_url=row.base_url or DEFAULT_VOLCENGINE["base_url"],
        chat_model=row.chat_model,
        image_model=row.image_model,
        video_model=row.video_model,
        embedding_model=row.embedding_model,
    )

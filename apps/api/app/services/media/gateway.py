"""媒体网关：按租户选择 Provider，落盘并返回元信息。"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import StorageService, get_storage
from app.services.media.providers.base import MediaProvider, MediaResult
from app.services.media.providers.demo import DemoMediaProvider
from app.services.media.providers.volcengine import VolcengineMediaProvider
from app.services.providers.registry import build_volcengine_client


class MediaGateway:
    """统一生图/生视频入口。"""

    def __init__(
        self,
        provider: MediaProvider | None = None,
        storage: StorageService | None = None,
    ) -> None:
        self.provider = provider or DemoMediaProvider()
        self.storage = storage or get_storage()

    @classmethod
    async def for_tenant(
        cls,
        session: AsyncSession,
        tenant_id: str,
    ) -> "MediaGateway":
        """根据租户配置选择火山或演示 Provider。"""
        client = await build_volcengine_client(session, tenant_id)
        if client:
            return cls(provider=VolcengineMediaProvider(client))
        return cls(provider=DemoMediaProvider())

    async def generate_image(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        prompt: str,
        mode: str = "text_to_image",
        image_bytes: bytes | None = None,
    ) -> tuple[str, MediaResult, str]:
        """生成图片并写入存储。返回 (asset_id, result, storage_key)。"""
        if mode == "image_to_image" and image_bytes:
            result = await self.provider.image_to_image(prompt, image_bytes=image_bytes)
        else:
            result = await self.provider.text_to_image(prompt)

        asset_id = f"asset_{uuid.uuid4().hex[:12]}"
        key = self.storage.build_key(
            tenant_id,
            workspace_id,
            result.filename,
            folder="images",
        )
        await self.storage.put_bytes(key, result.data, content_type=result.mime_type)
        return asset_id, result, key

    async def generate_video(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        prompt: str,
        mode: str = "text_to_video",
        image_bytes: bytes | None = None,
        duration: int = 5,
    ) -> tuple[str, MediaResult, str]:
        """生成视频并写入存储。"""
        if mode == "image_to_video" and image_bytes:
            result = await self.provider.image_to_video(prompt, image_bytes=image_bytes)
        else:
            result = await self.provider.text_to_video(prompt, duration=duration)

        asset_id = f"asset_{uuid.uuid4().hex[:12]}"
        key = self.storage.build_key(
            tenant_id,
            workspace_id,
            result.filename,
            folder="videos",
        )
        await self.storage.put_bytes(key, result.data, content_type=result.mime_type)
        return asset_id, result, key

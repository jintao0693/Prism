"""对象存储抽象：本地目录演示实现，后续可换 S3/OSS。"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import get_settings


class StorageService:
    """租户隔离的文件存储。路径约定：{root}/{tenant_id}/{workspace_id}/{key}"""

    def __init__(self) -> None:
        settings = get_settings()
        self.backend = settings.storage_backend
        self.root = Path(settings.local_storage_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def build_key(
        self,
        tenant_id: str,
        workspace_id: str,
        filename: str,
        *,
        folder: str = "assets",
    ) -> str:
        """生成对象相对路径。"""
        safe_name = filename.replace("..", "_").replace("/", "_")
        return f"{tenant_id}/{workspace_id}/{folder}/{uuid.uuid4().hex}_{safe_name}"

    async def put_bytes(
        self,
        relative_key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        """写入字节并返回可访问的本地路径或 key。"""
        # content_type 预留：接 S3 时写入 metadata
        _ = content_type
        if self.backend != "local":
            # TODO: 接入 S3 / MinIO
            raise NotImplementedError("当前仅实现 local 存储后端")

        path = self.root / relative_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return relative_key

    def resolve_path(self, relative_key: str) -> Path:
        """解析本地绝对路径。"""
        return self.root / relative_key

    def public_url(self, relative_key: str) -> str:
        """演示用 URL（后续改为签名 URL）。"""
        return f"/media/{relative_key}"


def get_storage() -> StorageService:
    """工厂：获取存储服务实例。"""
    return StorageService()

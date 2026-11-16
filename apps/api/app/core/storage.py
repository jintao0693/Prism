"""对象存储抽象：本地目录演示实现，后续可换 S3/OSS。"""

from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import quote

from app.core.config import get_settings
from app.core.thumbnails import ensure_thumb_file, make_jpeg_thumb, thumb_key_for


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
        make_thumb: bool | None = None,
    ) -> str:
        """写入字节并返回 key；图片默认旁路写缩略图。"""
        if self.backend != "local":
            # TODO: 接入 S3 / MinIO
            raise NotImplementedError("当前仅实现 local 存储后端")

        path = self.root / relative_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        should_thumb = make_thumb
        if should_thumb is None:
            should_thumb = content_type.startswith("image/") or relative_key.lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".gif"),
            )
        if should_thumb:
            thumb = make_jpeg_thumb(data)
            if thumb:
                tkey = thumb_key_for(relative_key)
                tpath = self.root / tkey
                tpath.parent.mkdir(parents=True, exist_ok=True)
                tpath.write_bytes(thumb)
        return relative_key

    def resolve_path(self, relative_key: str) -> Path:
        """解析本地绝对路径。"""
        return self.root / relative_key

    def public_url(self, relative_key: str) -> str:
        """演示用 URL（对路径分段编码，保留点号扩展名）。"""
        parts = [quote(p, safe="._-") for p in relative_key.split("/") if p != ""]
        return "/media/" + "/".join(parts)

    def public_thumb_url(self, relative_key: str, *, mime_type: str = "") -> str | None:
        """若有缩略图则返回预览 URL；视频海报（image mime）也可。"""
        if not relative_key:
            return None
        lower = relative_key.lower()
        is_image = mime_type.startswith("image/") or lower.endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif"),
        )
        if not is_image:
            return None
        tkey = thumb_key_for(relative_key)
        source = self.resolve_path(relative_key)
        thumb = self.resolve_path(tkey)
        if ensure_thumb_file(source, thumb):
            return self.public_url(tkey)
        # 小图直接用原图
        if source.exists() and source.stat().st_size < 200_000:
            return self.public_url(relative_key)
        return None


def get_storage() -> StorageService:
    """工厂：获取存储服务实例。"""
    return StorageService()

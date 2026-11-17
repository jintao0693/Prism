"""对象存储抽象：本地目录 + 可选 S3/MinIO。"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from urllib.parse import quote

from app.core.config import get_settings
from app.core.thumbnails import ensure_thumb_file, make_jpeg_thumb, thumb_key_for

logger = logging.getLogger(__name__)


class StorageService:
    """租户隔离的文件存储。路径约定：{tenant_id}/{workspace_id}/{folder}/..."""

    def __init__(self) -> None:
        settings = get_settings()
        self.backend = (settings.storage_backend or "local").lower()
        self.root = Path(settings.local_storage_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.s3_endpoint = settings.s3_endpoint
        self.s3_access_key = settings.s3_access_key
        self.s3_secret_key = settings.s3_secret_key
        self.s3_bucket = settings.s3_bucket
        self._s3 = None

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

    def _get_s3(self):
        if self._s3 is not None:
            return self._s3
        try:
            import boto3
            from botocore.client import Config
        except ImportError as exc:
            raise RuntimeError(
                "storage_backend=s3 需要安装 boto3：pip install boto3",
            ) from exc
        if not (self.s3_endpoint and self.s3_access_key and self.s3_secret_key):
            raise RuntimeError("S3/MinIO 未配置 endpoint / access_key / secret_key")
        self._s3 = boto3.client(
            "s3",
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )
        return self._s3

    async def put_bytes(
        self,
        relative_key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        make_thumb: bool | None = None,
    ) -> str:
        """写入字节并返回 key；图片默认旁路写缩略图。"""
        if self.backend == "s3":
            client = self._get_s3()
            client.put_object(
                Bucket=self.s3_bucket,
                Key=relative_key,
                Body=data,
                ContentType=content_type,
            )
            # 缩略图仍写本地旁路（预览走 /media 时需同步；生产可改预签名）
            path = self.root / relative_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif self.backend == "local":
            path = self.root / relative_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        else:
            raise NotImplementedError(f"未知存储后端: {self.backend}")

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
                if self.backend == "s3":
                    try:
                        self._get_s3().put_object(
                            Bucket=self.s3_bucket,
                            Key=tkey,
                            Body=thumb,
                            ContentType="image/jpeg",
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("S3 缩略图上传失败: %s", exc)
        return relative_key

    def resolve_path(self, relative_key: str) -> Path:
        """解析本地绝对路径（本地缓存或 local backend）。"""
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
        if source.exists() and source.stat().st_size < 200_000:
            return self.public_url(relative_key)
        return None


def get_storage() -> StorageService:
    """工厂：获取存储服务实例。"""
    return StorageService()

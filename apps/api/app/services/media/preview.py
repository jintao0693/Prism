"""素材预览元信息：缩略图 URL / 预览类型。"""

from __future__ import annotations

from typing import Literal

from app.core.storage import StorageService, get_storage
from app.models.asset import Asset

PreviewKind = Literal["image", "video", "poster"]


def resolve_preview(
    *,
    storage_key: str | None,
    kind: str,
    mime_type: str = "",
    storage: StorageService | None = None,
) -> tuple[str | None, str | None, str | None, PreviewKind]:
    """
    返回 (url, thumb_url, mime, preview_kind)。

    - 真实视频：preview_kind=video，thumb 暂无（可后续抽帧）
    - 视频条目但文件是图片海报：preview_kind=poster，用 img 预览
    - 普通图片：preview_kind=image，优先 thumb
    """
    store = storage or get_storage()
    if not storage_key:
        return None, None, mime_type or None, "image" if kind != "video" else "video"

    url = store.public_url(storage_key)
    mime = mime_type or ""
    lower = storage_key.lower()
    looks_image = mime.startswith("image/") or lower.endswith(
        (".png", ".jpg", ".jpeg", ".webp", ".gif"),
    )
    looks_video = mime.startswith("video/") or lower.endswith(
        (".mp4", ".webm", ".mov"),
    )

    if kind == "video" and looks_image and not looks_video:
        thumb = store.public_thumb_url(storage_key, mime_type=mime or "image/png")
        return url, thumb or url, mime or "image/png", "poster"

    if looks_video or (kind == "video" and not looks_image):
        return url, None, mime or "video/mp4", "video"

    thumb = store.public_thumb_url(storage_key, mime_type=mime or "image/png")
    return url, thumb or url, mime or "image/png", "image"


def asset_preview_fields(asset: Asset, storage: StorageService | None = None) -> dict:
    url, thumb, mime, preview = resolve_preview(
        storage_key=asset.storage_key,
        kind=asset.kind,
        mime_type=asset.mime_type or "",
        storage=storage,
    )
    return {
        "url": url,
        "thumbUrl": thumb,
        "mimeType": mime,
        "previewKind": preview,
    }

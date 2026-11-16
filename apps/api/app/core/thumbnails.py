"""本地缩略图：大图预览不要直接塞 2K 原图。"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

_THUMB_MAX = 480
_THUMB_SUFFIX = ".thumb.jpg"


def thumb_key_for(storage_key: str) -> str:
    """同目录旁路缩略图 key。"""
    return f"{storage_key}{_THUMB_SUFFIX}"


def make_jpeg_thumb(data: bytes, *, max_side: int = _THUMB_MAX) -> bytes | None:
    """从图片字节生成 JPEG 缩略图；非图片返回 None。"""
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82, optimize=True)
            return buf.getvalue()
    except (OSError, ValueError, Image.UnidentifiedImageError) as exc:
        logger.debug("缩略图失败: %s", exc)
        return None


def ensure_thumb_file(source_path: Path, thumb_path: Path) -> bool:
    """若缩略图不存在则从原图生成。返回是否可用。"""
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return True
    if not source_path.exists():
        return False
    try:
        data = source_path.read_bytes()
    except OSError:
        return False
    thumb = make_jpeg_thumb(data)
    if not thumb:
        return False
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    thumb_path.write_bytes(thumb)
    return True

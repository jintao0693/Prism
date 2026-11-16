"""演示供应商：不调用真实模型，返回占位 PNG/MP4 字节。"""

from __future__ import annotations

import struct
import zlib

from app.services.media.providers.base import MediaProvider, MediaResult


def _png_placeholder(width: int = 64, height: int = 64) -> bytes:
    """生成极简纯色 PNG，便于联调存储链路。"""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes([15, 110, 106, 255]) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


class DemoMediaProvider(MediaProvider):
    """本地演示用 Provider。"""

    name = "demo"

    async def text_to_image(self, prompt: str, *, size: str = "1024x1024") -> MediaResult:
        _ = size
        return MediaResult(
            data=_png_placeholder(),
            mime_type="image/png",
            filename="demo_image.png",
            meta=f"demo text_to_image · {prompt[:40]}",
        )

    async def image_to_image(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        _ = image_bytes
        return await self.text_to_image(prompt)

    async def text_to_video(self, prompt: str, *, duration: int = 5) -> MediaResult:
        # 最小假视频文件头（并非可播完整 mp4，仅占位）
        data = b"\x00\x00\x00\x18ftypmp42" + prompt.encode("utf-8")[:32]
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="demo_video.mp4",
            meta=f"demo text_to_video · {duration}s · {prompt[:40]}",
        )

    async def image_to_video(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        _ = image_bytes
        return await self.text_to_video(prompt)

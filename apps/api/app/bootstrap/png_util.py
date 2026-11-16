"""无第三方依赖的纯色 PNG 生成（种子素材用）。"""

from __future__ import annotations

import struct
import zlib


def solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """生成不透明 RGB PNG。"""
    r, g, b = rgb
    row = b"\x00" + bytes([r, g, b]) * width
    raw = row * height

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(raw, 9)),
            chunk(b"IEND", b""),
        ],
    )

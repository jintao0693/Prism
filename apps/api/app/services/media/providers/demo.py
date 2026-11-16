"""演示供应商：不调用真实模型，返回占位 PNG/MP4 字节。"""

from __future__ import annotations

import asyncio

from app.bootstrap.png_util import solid_png
from app.services.media.providers.base import MediaProvider, MediaResult, ProgressCallback


class DemoMediaProvider(MediaProvider):
    """本地演示用 Provider。"""

    name = "demo"

    async def text_to_image(self, prompt: str, *, size: str = "1024x1024") -> MediaResult:
        _ = size
        return MediaResult(
            data=solid_png(64, 64, (15, 110, 106)),
            mime_type="image/png",
            filename="demo_image.png",
            meta=f"demo text_to_image · {prompt[:40]}",
        )

    async def image_to_image(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        _ = image_bytes
        return MediaResult(
            data=solid_png(64, 64, (232, 168, 56)),
            mime_type="image/png",
            filename="demo_image_edit.png",
            meta=f"demo image_to_image · {prompt[:40]}",
        )

    async def text_to_video(
        self,
        prompt: str,
        *,
        duration: int = 5,
        on_progress: ProgressCallback | None = None,
    ) -> MediaResult:
        if on_progress:
            value = on_progress("succeeded", 0.0, "demo_task")
            if asyncio.iscoroutine(value):
                await value
        data = b"\x00\x00\x00\x18ftypmp42" + prompt.encode("utf-8")[:32]
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="demo_video.mp4",
            meta=f"demo text_to_video · {duration}s · {prompt[:40]}",
        )

    async def image_to_video(
        self,
        prompt: str,
        *,
        image_bytes: bytes,
        duration: int = 5,
        on_progress: ProgressCallback | None = None,
    ) -> MediaResult:
        _ = image_bytes
        return await self.text_to_video(
            prompt,
            duration=duration,
            on_progress=on_progress,
        )

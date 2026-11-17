"""火山方舟生图 / 生视频 Provider（含图生图 / 图生视频）。"""

from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.media.providers.base import MediaProvider, MediaResult
from app.services.providers.volcengine.client import VolcengineArkClient

ProgressCallback = Callable[[str, float, str], Awaitable[None] | None]


def _to_data_url(image_bytes: bytes, mime: str = "image/png") -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"


class VolcengineMediaProvider(MediaProvider):
    """对接 Seedream / Seedance。"""

    name = "volcengine_ark"

    def __init__(self, client: VolcengineArkClient) -> None:
        self.client = client

    async def text_to_image(self, prompt: str, *, size: str = "1024x1024") -> MediaResult:
        ark_size = "2K"
        if size in {"1K", "2K", "1.5K"}:
            ark_size = size
        data = await self.client.generate_image(prompt, size=ark_size)
        return MediaResult(
            data=data,
            mime_type="image/png",
            filename="volc_image.png",
            meta=f"volcengine text_to_image · {prompt[:40]}",
        )

    async def image_to_image(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        data_url = _to_data_url(image_bytes)
        data = await self.client.generate_image(prompt, size="2K", image=data_url)
        return MediaResult(
            data=data,
            mime_type="image/png",
            filename="volc_image_edit.png",
            meta=f"volcengine image_to_image · {prompt[:40]}",
        )

    async def text_to_video(
        self,
        prompt: str,
        *,
        duration: int = 5,
        on_progress: ProgressCallback | None = None,
    ) -> MediaResult:
        data = await self.client.generate_video(
            prompt,
            duration=duration,
            on_progress=on_progress,
        )
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="volc_video.mp4",
            meta=f"volcengine text_to_video · {duration}s · {prompt[:40]}",
        )

    async def image_to_video(
        self,
        prompt: str,
        *,
        image_bytes: bytes,
        duration: int = 5,
        on_progress: ProgressCallback | None = None,
    ) -> MediaResult:
        data_url = _to_data_url(image_bytes)
        data = await self.client.generate_video(
            prompt,
            duration=duration,
            image_url=data_url,
            on_progress=on_progress,
        )
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="volc_i2v.mp4",
            meta=f"volcengine image_to_video · {duration}s · {prompt[:40]}",
        )

    async def reference_to_video(
        self,
        prompt: str,
        *,
        reference_images: list[bytes],
        duration: int = 15,
        ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool | None = True,
        on_progress: ProgressCallback | None = None,
    ) -> MediaResult:
        """Seedance 2.0+ 多模态参考生视频（多张 reference_image，最长约 15s）。"""
        refs = [_to_data_url(img) for img in reference_images[:9] if img]
        if not refs:
            raise ValueError("多模态参考生视频至少需要 1 张参考图")
        data = await self.client.generate_video(
            prompt,
            duration=duration,
            ratio=ratio,
            resolution=resolution,
            reference_image_urls=refs,
            generate_audio=generate_audio,
            on_progress=on_progress,
        )
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="volc_ref2v.mp4",
            meta=(
                f"volcengine reference_to_video · {duration}s · "
                f"{len(refs)} refs · {prompt[:40]}"
            ),
        )

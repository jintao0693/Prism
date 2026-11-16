"""火山方舟生图 / 生视频 Provider。"""

from __future__ import annotations

from app.services.media.providers.base import MediaProvider, MediaResult
from app.services.providers.volcengine.client import VolcengineArkClient


class VolcengineMediaProvider(MediaProvider):
    """对接 Seedream / Seedance。"""

    name = "volcengine_ark"

    def __init__(self, client: VolcengineArkClient) -> None:
        self.client = client

    async def text_to_image(self, prompt: str, *, size: str = "1024x1024") -> MediaResult:
        # 方舟常用 size 为 2K / 1K；将常见像素映射
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
        # MVP：图生图可后续补 reference image；先退回文生图
        _ = image_bytes
        return await self.text_to_image(prompt)

    async def text_to_video(self, prompt: str, *, duration: int = 5) -> MediaResult:
        data = await self.client.generate_video(prompt, duration=duration)
        return MediaResult(
            data=data,
            mime_type="video/mp4",
            filename="volc_video.mp4",
            meta=f"volcengine text_to_video · {duration}s · {prompt[:40]}",
        )

    async def image_to_video(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        # MVP：需要可访问的 image_url；暂用文生视频
        _ = image_bytes
        return await self.text_to_video(prompt)

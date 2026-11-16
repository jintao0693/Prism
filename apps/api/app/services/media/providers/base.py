"""媒体供应商抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MediaResult:
    """生成结果：字节 + MIME + 展示名。"""

    data: bytes
    mime_type: str
    filename: str
    meta: str = ""


class MediaProvider(ABC):
    """生图 / 生视频供应商。"""

    name: str = "base"

    @abstractmethod
    async def text_to_image(self, prompt: str, *, size: str = "1024x1024") -> MediaResult:
        """文生图。"""

    @abstractmethod
    async def image_to_image(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        """图生图。"""

    @abstractmethod
    async def text_to_video(self, prompt: str, *, duration: int = 5) -> MediaResult:
        """文生视频。"""

    @abstractmethod
    async def image_to_video(self, prompt: str, *, image_bytes: bytes) -> MediaResult:
        """图生视频。"""

"""火山方舟 HTTP 客户端：对话 / 生图 / 生视频 / 多模态向量。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE = "https://ark.cn-beijing.volces.com/api/v3"


class VolcengineArkError(RuntimeError):
    """方舟调用失败。"""


class VolcengineArkClient:
    """
    字节跳动 / 火山方舟统一客户端。

    - 对话：OpenAI 兼容 /chat/completions
    - 生图：/images/generations
    - 生视频：异步 /contents/generations/tasks + 轮询
    - 向量：/embeddings/multimodal（不兼容 OpenAI embeddings）
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE,
        chat_model: str = "",
        image_model: str = "",
        video_model: str = "",
        embedding_model: str = "",
        timeout: float = 120.0,
    ) -> None:
        if not api_key:
            raise VolcengineArkError("未配置火山方舟 API Key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.image_model = image_model
        self.video_model = video_model
        self.embedding_model = embedding_model
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
            )
        if resp.status_code >= 400:
            raise VolcengineArkError(
                f"方舟接口错误 {resp.status_code}: {resp.text[:500]}",
            )
        if not resp.content:
            return {}
        return resp.json()

    # ---------- 对话 ----------
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """调用对话模型，返回助手文本。"""
        model_id = model or self.chat_model
        if not model_id:
            raise VolcengineArkError("未配置对话模型 ID（chat_model）")
        data = await self._request(
            "POST",
            "/chat/completions",
            json_body={
                "model": model_id,
                "messages": messages,
                "temperature": temperature,
            },
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VolcengineArkError(f"对话响应解析失败: {data}") from exc

    # ---------- 生图 ----------
    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str = "2K",
        response_format: str = "url",
        watermark: bool = False,
    ) -> bytes:
        """文生图，返回图片字节。"""
        model_id = model or self.image_model
        if not model_id:
            raise VolcengineArkError("未配置生图模型 ID（image_model）")

        data = await self._request(
            "POST",
            "/images/generations",
            json_body={
                "model": model_id,
                "prompt": prompt,
                "size": size,
                "response_format": response_format,
                "watermark": watermark,
            },
        )
        items = data.get("data") or []
        if not items:
            raise VolcengineArkError(f"生图无结果: {data}")

        item = items[0]
        if item.get("b64_json"):
            import base64

            return base64.b64decode(item["b64_json"])

        url = item.get("url")
        if not url:
            raise VolcengineArkError(f"生图响应缺少 url/b64: {item}")
        return await self._download(url)

    # ---------- 生视频（异步任务） ----------
    async def create_video_task(
        self,
        prompt: str,
        *,
        model: str | None = None,
        ratio: str = "16:9",
        duration: int | None = 5,
        image_url: str | None = None,
    ) -> str:
        """创建视频任务，返回 task_id。"""
        model_id = model or self.video_model
        if not model_id:
            raise VolcengineArkError("未配置视频模型 ID（video_model）")

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.insert(
                0,
                {"type": "image_url", "image_url": {"url": image_url}},
            )

        body: dict[str, Any] = {
            "model": model_id,
            "content": content,
        }
        # 部分模型支持 ratio / duration，以 extra 字段尝试传递
        if ratio:
            body["ratio"] = ratio
        if duration is not None:
            body["duration"] = duration

        data = await self._request(
            "POST",
            "/contents/generations/tasks",
            json_body=body,
        )
        task_id = data.get("id")
        if not task_id:
            raise VolcengineArkError(f"创建视频任务失败: {data}")
        return str(task_id)

    async def get_video_task(self, task_id: str) -> dict[str, Any]:
        """查询视频任务状态。"""
        return await self._request("GET", f"/contents/generations/tasks/{task_id}")

    async def generate_video(
        self,
        prompt: str,
        *,
        model: str | None = None,
        ratio: str = "16:9",
        duration: int | None = 5,
        image_url: str | None = None,
        poll_interval: float = 8.0,
        max_wait: float = 600.0,
    ) -> bytes:
        """创建并轮询视频任务，成功后下载视频字节。"""
        task_id = await self.create_video_task(
            prompt,
            model=model,
            ratio=ratio,
            duration=duration,
            image_url=image_url,
        )
        logger.info("火山视频任务已创建: %s", task_id)

        elapsed = 0.0
        while elapsed < max_wait:
            result = await self.get_video_task(task_id)
            status = result.get("status")
            if status == "succeeded":
                content = result.get("content") or {}
                video_url = content.get("video_url")
                if not video_url:
                    raise VolcengineArkError(f"任务成功但无 video_url: {result}")
                return await self._download(video_url)
            if status == "failed":
                raise VolcengineArkError(f"视频生成失败: {result.get('error') or result}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise VolcengineArkError(f"视频任务超时: {task_id}")

    # ---------- 多模态向量 ----------
    async def embed_text(
        self,
        text: str,
        *,
        model: str | None = None,
        dimensions: int = 1024,
    ) -> list[float]:
        """文本向量化。"""
        return await self._embed(
            [{"type": "text", "text": text}],
            model=model,
            dimensions=dimensions,
        )

    async def embed_image_url(
        self,
        image_url: str,
        *,
        model: str | None = None,
        dimensions: int = 1024,
    ) -> list[float]:
        """图片 URL / data-url 向量化。"""
        return await self._embed(
            [{"type": "image_url", "image_url": {"url": image_url}}],
            model=model,
            dimensions=dimensions,
        )

    async def _embed(
        self,
        inputs: list[dict[str, Any]],
        *,
        model: str | None,
        dimensions: int,
    ) -> list[float]:
        model_id = model or self.embedding_model
        if not model_id:
            raise VolcengineArkError("未配置向量模型 ID（embedding_model）")

        data = await self._request(
            "POST",
            "/embeddings/multimodal",
            json_body={
                "model": model_id,
                "encoding_format": "float",
                "dimensions": dimensions,
                "input": inputs,
            },
        )
        # 响应结构：data 可能是对象或列表，兼容常见形态
        payload = data.get("data")
        if isinstance(payload, dict) and "embedding" in payload:
            return list(payload["embedding"])
        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, dict) and "embedding" in first:
                return list(first["embedding"])
        if "embedding" in data:
            return list(data["embedding"])
        raise VolcengineArkError(f"向量响应解析失败: {data}")

    async def _download(self, url: str) -> bytes:
        """下载远程资源。"""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            raise VolcengineArkError(f"下载失败 {resp.status_code}: {url}")
        return resp.content

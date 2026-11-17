"""火山方舟 HTTP 客户端：对话 / 生图 / 生视频 / 多模态向量。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE = "https://ark.cn-beijing.volces.com/api/v3"


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


async def _maybe_await(value: Any) -> None:
    if asyncio.iscoroutine(value):
        await value


class VolcengineArkError(RuntimeError):
    """方舟调用失败。"""


@dataclass
class ChatCompletionResult:
    """对话结果（含 usage，供上下文压缩计量）。"""

    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


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
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> ChatCompletionResult:
        """调用对话模型，返回文本 + usage。"""
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
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VolcengineArkError(f"对话响应解析失败: {data}") from exc
        usage = data.get("usage") or {}
        return ChatCompletionResult(
            content=content if isinstance(content, str) else str(content),
            prompt_tokens=_as_int(usage.get("prompt_tokens")),
            completion_tokens=_as_int(usage.get("completion_tokens")),
            total_tokens=_as_int(usage.get("total_tokens")),
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """调用对话模型，返回助手文本。"""
        result = await self.chat_completion(
            messages,
            model=model,
            temperature=temperature,
        )
        return result.content

    async def chat_completion_stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str | ChatCompletionResult]:
        """
        流式对话：yield 文本增量（str），结束时 yield ChatCompletionResult（含 usage）。
        """
        model_id = model or self.chat_model
        if not model_id:
            raise VolcengineArkError("未配置对话模型 ID（chat_model）")

        url = f"{self.base_url}/chat/completions"
        body = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        pieces: list[str] = []
        usage: dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._headers(),
                json=body,
            ) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", errors="replace")[:500]
                    raise VolcengineArkError(f"方舟接口错误 {resp.status_code}: {text}")
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except Exception:
                        continue
                    if chunk.get("usage"):
                        usage = chunk["usage"] or {}
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if isinstance(piece, str) and piece:
                        pieces.append(piece)
                        yield piece

        yield ChatCompletionResult(
            content="".join(pieces),
            prompt_tokens=_as_int(usage.get("prompt_tokens")),
            completion_tokens=_as_int(usage.get("completion_tokens")),
            total_tokens=_as_int(usage.get("total_tokens")),
        )

    # ---------- 生图 ----------
    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str = "2K",
        response_format: str = "url",
        watermark: bool = False,
        image: str | list[str] | None = None,
    ) -> bytes:
        """文生图 / 图生图，返回图片字节。image 为 URL 或 data-url（可多张）。"""
        model_id = model or self.image_model
        if not model_id:
            raise VolcengineArkError("未配置生图模型 ID（image_model）")

        body: dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "size": size,
            "response_format": response_format,
            "watermark": watermark,
        }
        if image:
            body["image"] = image

        data = await self._request(
            "POST",
            "/images/generations",
            json_body=body,
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
        last_frame_url: str | None = None,
        reference_image_urls: list[str] | None = None,
        generate_audio: bool | None = None,
        resolution: str | None = None,
    ) -> str:
        """创建视频任务，返回 task_id。

        互斥模式（与方舟一致，不可混用）：
        - 首帧 / 首尾帧：`image_url`（+ 可选 `last_frame_url`）
        - 多模态参考生视频（Seedance 2.0+）：`reference_image_urls`（最多 9 张）
        - 文生视频：仅文本
        """
        model_id = model or self.video_model
        if not model_id:
            raise VolcengineArkError("未配置视频模型 ID（video_model）")

        refs = [u for u in (reference_image_urls or []) if u][:9]
        if refs and (image_url or last_frame_url):
            raise VolcengineArkError(
                "多模态参考图与首帧/首尾帧模式互斥，请只选一种",
            )

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if refs:
            for url in refs:
                content.append(
                    {
                        "type": "image_url",
                        "role": "reference_image",
                        "image_url": {"url": url},
                    },
                )
        elif image_url and last_frame_url:
            content.insert(
                0,
                {
                    "type": "image_url",
                    "role": "first_frame",
                    "image_url": {"url": image_url},
                },
            )
            content.insert(
                1,
                {
                    "type": "image_url",
                    "role": "last_frame",
                    "image_url": {"url": last_frame_url},
                },
            )
        elif image_url:
            content.insert(
                0,
                {"type": "image_url", "image_url": {"url": image_url}},
            )

        body: dict[str, Any] = {
            "model": model_id,
            "content": content,
        }
        # 首帧/首尾帧图生视频时，输出比例跟随首帧图，不可再传 ratio
        frame_locked = bool(image_url) and not refs
        if ratio and not frame_locked:
            body["ratio"] = ratio
        if duration is not None:
            body["duration"] = duration
        if resolution:
            body["resolution"] = resolution
        if generate_audio is not None:
            body["generate_audio"] = generate_audio

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
        last_frame_url: str | None = None,
        reference_image_urls: list[str] | None = None,
        generate_audio: bool | None = None,
        resolution: str | None = None,
        poll_interval: float = 8.0,
        max_wait: float = 600.0,
        on_progress: Any | None = None,
    ) -> bytes:
        """创建并轮询视频任务，成功后下载视频字节。on_progress(status, elapsed, task_id)。"""
        task_id = await self.create_video_task(
            prompt,
            model=model,
            ratio=ratio,
            duration=duration,
            image_url=image_url,
            last_frame_url=last_frame_url,
            reference_image_urls=reference_image_urls,
            generate_audio=generate_audio,
            resolution=resolution,
        )
        logger.info("火山视频任务已创建: %s", task_id)
        if on_progress:
            await _maybe_await(on_progress("submitted", 0.0, task_id))

        elapsed = 0.0
        while elapsed < max_wait:
            result = await self.get_video_task(task_id)
            status = str(result.get("status") or "unknown")
            if on_progress:
                await _maybe_await(on_progress(status, elapsed, task_id))
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

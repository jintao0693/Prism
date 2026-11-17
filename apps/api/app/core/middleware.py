"""请求 ID 与简易限流中间件。"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT = 180
_RATE_WINDOW_SEC = 60.0


class RequestIdMiddleware(BaseHTTPMiddleware):
    """注入 X-Request-Id，便于日志串联。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """按客户端 IP 的进程内滑动窗口限流（开发 / 演示）。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client = request.client
        key = client.host if client else "unknown"
        now = time.monotonic()
        bucket = _RATE_BUCKETS[key]
        while bucket and now - bucket[0] > _RATE_WINDOW_SEC:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT:
            rid = getattr(request.state, "request_id", "")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
                headers={"X-Request-Id": rid} if rid else {},
            )
        bucket.append(now)
        return await call_next(request)
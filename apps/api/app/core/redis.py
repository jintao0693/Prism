"""Redis 客户端（可选）。未连通时返回 None，业务可降级。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)
_redis: Redis | None = None


async def get_redis() -> Redis | None:
    """获取全局 Redis；失败则记日志并返回 None。"""
    global _redis
    if _redis is not None:
        return _redis
    try:
        from redis.asyncio import from_url

        settings = get_settings()
        client = from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        _redis = client
        return _redis
    except Exception as exc:
        logger.warning("Redis 不可用，将跳过队列能力: %s", exc)
        return None


async def close_redis() -> None:
    """关闭 Redis 连接。"""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

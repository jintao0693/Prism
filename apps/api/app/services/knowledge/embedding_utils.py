"""向量工具：相似度与序列化。"""

from __future__ import annotations

import json
import math


def dumps_embedding(vec: list[float]) -> str:
    """向量 → JSON 字符串。"""
    return json.dumps(vec)


def loads_embedding(raw: str | None) -> list[float] | None:
    """JSON → 向量。"""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [float(x) for x in data]
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """余弦相似度。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

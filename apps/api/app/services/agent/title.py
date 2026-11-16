"""根据首条 brief 生成会话标题。"""

from __future__ import annotations

import re

_DEFAULT_TITLES = {
    "",
    "新对话",
    "untitled",
    "untitled conversation",
}

_SPACE_RE = re.compile(r"\s+")


def is_placeholder_title(title: str | None) -> bool:
    return (title or "").strip().lower() in _DEFAULT_TITLES


def title_from_brief(content: str, *, max_len: int = 28) -> str:
    """取首条用户 brief 的可读短标题。"""
    text = _SPACE_RE.sub(" ", (content or "").strip())
    # 去掉常见前缀口癖
    for prefix in ("请帮我", "请", "帮我", "我想", "我要"):
        if text.startswith(prefix):
            text = text[len(prefix) :].lstrip("，,：: ")
            break
    if not text:
        return "新对话"
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rstrip("，,。.!！？?、 ")
    return f"{cut}…"

"""用户意图识别：优先对话模型分类，失败回退正则。"""

from __future__ import annotations

import logging
import re
from typing import Literal

from app.services.providers.volcengine.client import VolcengineArkClient

logger = logging.getLogger(__name__)

Intent = Literal["chat", "image", "video", "knowledge"]

_VALID: set[str] = {"chat", "image", "video", "knowledge"}

_INTENT_SYSTEM = """你是 Prism 的意图分类器。根据用户一句话，判断唯一意图，只输出下列单词之一（小写，不要解释、不要标点、不要换行）：
- chat：普通问答、闲聊、解释、建议（不立刻生图/生视频）
- image：用户要生成/绘制图片、海报、封面、主视觉等静态画面
- video：用户要生成视频、短片、出片、镜头/分镜成片
- knowledge：用户在问品牌规范、主色、资料库/知识库内容

若同时像问答又像生成，优先生成类（image/video）。
若同时像 image 与 video，有「视频/短片/出片」则选 video，否则选 image。
""".strip()


def classify_intent_regex(user_text: str, *, has_knowledge: bool) -> Intent:
    """规则兜底：不依赖外网模型。"""
    text = user_text.strip()
    if has_knowledge and re.search(
        r"主色|规范|是什么|什么色|根据知识库|知识库|VI|品牌色",
        text,
    ):
        return "knowledge"
    # 视频优先于生图（「生成一段视频」也会命中「生成」）
    if re.search(r"视频|短片|分镜|出片|图生视频|做.*片", text):
        return "video"
    if re.search(r"生成|出图|海报|封面|主视觉|画一张|做.*图|文生图", text):
        return "image"
    return "chat"


def _parse_intent_label(raw: str) -> Intent | None:
    """从模型输出里抠出意图标签。"""
    text = (raw or "").strip().lower()
    # 允许模型偶尔带引号/句号
    text = text.strip("`\"'。．.，,")
    first = re.split(r"[\s\n，,。；;]", text, maxsplit=1)[0]
    if first in _VALID:
        return first  # type: ignore[return-value]
    for label in ("knowledge", "video", "image", "chat"):
        if label in text:
            return label  # type: ignore[return-value]
    return None


async def classify_intent(
    user_text: str,
    *,
    ark: VolcengineArkClient | None,
    has_knowledge: bool,
) -> tuple[Intent, str]:
    """
    返回 (意图, 来源)。
    来源：model | regex
    """
    fallback = classify_intent_regex(user_text, has_knowledge=has_knowledge)

    if not ark or not ark.chat_model:
        return fallback, "regex"

    try:
        raw = await ark.chat(
            [
                {"role": "system", "content": _INTENT_SYSTEM},
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
        )
        parsed = _parse_intent_label(raw)
        if parsed is None:
            logger.warning("意图识别无法解析，回退正则: %s", raw[:80])
            return fallback, "regex"
        # 未引用知识库时，knowledge 落到 chat，避免空检索
        if parsed == "knowledge" and not has_knowledge:
            return "chat", "model"
        return parsed, "model"
    except Exception as exc:
        logger.warning("意图识别调用失败，回退正则: %s", exc)
        return fallback, "regex"

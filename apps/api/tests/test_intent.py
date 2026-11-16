"""意图识别：正则兜底与标签解析。"""

from __future__ import annotations

from app.services.agent.intent import (
    _parse_intent_label,
    classify_intent_regex,
)


def test_regex_video_beats_generate() -> None:
    assert (
        classify_intent_regex("生成一段 15 秒种草短视频", has_knowledge=False)
        == "video"
    )


def test_regex_image() -> None:
    assert classify_intent_regex("画一张电商主视觉海报", has_knowledge=False) == "image"


def test_regex_chat() -> None:
    assert classify_intent_regex("Prism 是做什么的？", has_knowledge=False) == "chat"


def test_regex_knowledge() -> None:
    assert (
        classify_intent_regex("我们品牌主色规范是什么？", has_knowledge=True)
        == "knowledge"
    )
    # 未挂知识库时不当作 knowledge
    assert (
        classify_intent_regex("我们品牌主色规范是什么？", has_knowledge=False)
        == "chat"
    )


def test_parse_intent_label() -> None:
    assert _parse_intent_label("image") == "image"
    assert _parse_intent_label("VIDEO\n") == "video"
    assert _parse_intent_label('"chat"') == "chat"
    assert _parse_intent_label("意图：knowledge") == "knowledge"

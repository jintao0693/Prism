"""工具选择规则单测。"""

from app.services.agent.tool_runner import _select_tool


def test_refine_uses_i2i() -> None:
    assert (
        _select_tool(
            intent="image",
            user_text="再偏暖一点",
            has_knowledge=False,
            has_last_image=True,
        )
        == "image_to_image"
    )


def test_reference_forces_i2i() -> None:
    assert (
        _select_tool(
            intent="image",
            user_text="按这张参考图做一张商店页头图",
            has_knowledge=False,
            has_last_image=False,
            has_reference_image=True,
        )
        == "image_to_image"
    )


def test_video_from_image() -> None:
    assert (
        _select_tool(
            intent="video",
            user_text="把上一张做成短视频",
            has_knowledge=False,
            has_last_image=True,
        )
        == "image_to_video"
    )


def test_reference_video() -> None:
    assert (
        _select_tool(
            intent="video",
            user_text="做成 5 秒预告",
            has_knowledge=False,
            has_last_image=False,
            has_reference_image=True,
        )
        == "image_to_video"
    )


def test_plain_image() -> None:
    assert (
        _select_tool(
            intent="image",
            user_text="生成一张春季主视觉",
            has_knowledge=False,
            has_last_image=False,
        )
        == "text_to_image"
    )


def test_visual_kb() -> None:
    assert (
        _select_tool(
            intent="knowledge",
            user_text="帮我图搜相似主视觉素材",
            has_knowledge=True,
            has_last_image=True,
        )
        == "kb_search_image"
    )

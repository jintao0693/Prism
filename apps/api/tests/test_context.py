"""多轮上下文裁剪 / 压缩判定单测。"""

from app.models.conversation import Conversation
from app.services.agent.compact import should_compact
from app.services.agent.context import SUMMARY_PREFIX, assemble_chat_messages


def test_assemble_keeps_latest_and_trims_oldest() -> None:
    history = [
        {"role": "user", "content": "第一轮很长" * 200},
        {"role": "assistant", "content": "答一" * 200},
        {"role": "user", "content": "第二轮"},
        {"role": "assistant", "content": "答二"},
        {"role": "user", "content": "第三轮"},
        {"role": "assistant", "content": "答三"},
    ]
    messages, stats = assemble_chat_messages(
        system="SYS",
        history=history,
        latest_user="本轮问题",
        max_chars=800,
    )
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "本轮问题"}
    assert int(stats["chars"]) <= 800 + 50
    joined = " ".join(m["content"] for m in messages)
    assert "第一轮很长" not in joined or int(stats["historyCount"]) < len(history)


def test_assemble_drops_trailing_user_in_history() -> None:
    history = [
        {"role": "user", "content": "上句"},
        {"role": "assistant", "content": "上答"},
        {"role": "user", "content": "未完成的 user"},
    ]
    messages, _stats = assemble_chat_messages(
        system="SYS",
        history=history,
        latest_user="真正本轮",
    )
    assert messages[-1]["content"] == "真正本轮"
    assert messages[-2]["role"] == "assistant"


def test_assemble_preserves_summary_bridge_when_trimming() -> None:
    history = [
        {"role": "user", "content": f"{SUMMARY_PREFIX}\n品牌主色是青石色"},
        {"role": "assistant", "content": "已收到会话摘要，将据此继续协助，不再要求用户重复已知信息。"},
        {"role": "user", "content": "x" * 500},
        {"role": "assistant", "content": "y" * 500},
        {"role": "user", "content": "最近一句"},
        {"role": "assistant", "content": "最近答复"},
    ]
    messages, stats = assemble_chat_messages(
        system="SYS",
        history=history,
        latest_user="本轮",
        max_chars=900,
    )
    assert stats["hasSummary"] is True
    assert any(SUMMARY_PREFIX in m["content"] for m in messages)


def test_should_compact_by_tokens() -> None:
    conv = Conversation(
        id="c_test",
        tenant_id="t",
        workspace_id="w",
        title="t",
        context_tokens_estimate=30_000,
    )
    need, reason = should_compact(conv, window_message_count=12)
    assert need is True
    assert "tokens" in reason


def test_should_compact_skips_short_window() -> None:
    conv = Conversation(
        id="c_test2",
        tenant_id="t",
        workspace_id="w",
        title="t",
        context_tokens_estimate=30_000,
    )
    need, reason = should_compact(conv, window_message_count=3)
    assert need is False
    assert reason == "messages_below_min"

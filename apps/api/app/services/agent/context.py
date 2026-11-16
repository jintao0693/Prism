"""多轮对话上下文：摘要检查点 + 轮次/字符裁剪 + 压缩后重注。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.conversation import Message

# 约 12 轮（user+assistant），字符预算偏保守
DEFAULT_MAX_MESSAGES = 24
DEFAULT_MAX_CHARS = 12_000
_ALLOWED_ROLES = frozenset({"user", "assistant"})
SUMMARY_PREFIX = "【会话摘要·压缩检查点】"
SUMMARY_ACK = "已收到会话摘要，将据此继续协助，不再要求用户重复已知信息。"


def estimate_tokens_from_text(text: str) -> int:
    """粗略 token 估计（中英混合：约 2 字符 ≈ 1 token）。"""
    if not text:
        return 0
    return max(1, len(text) // 2)


def build_system_prompt(
    base: str,
    *,
    workspace_id: str,
    knowledge_base_ids: list[str] | None = None,
    compact_generation: int = 0,
) -> str:
    """
    稳定 system 前缀 + 压缩后重注的宿主上下文（工作区 / KB）。
    易变 RAG 仍放在本轮 user 里，不塞进 system。
    """
    parts = [base.strip()]
    reinject = [
        "【运行时上下文】",
        f"- 工作空间: {workspace_id}",
    ]
    if knowledge_base_ids:
        reinject.append(f"- 已勾选知识库: {', '.join(knowledge_base_ids)}")
    else:
        reinject.append("- 已勾选知识库: （无）")
    if compact_generation > 0:
        reinject.append(
            f"- 上下文已压缩 {compact_generation} 次；上方若有摘要检查点请优先遵循",
        )
    parts.append("\n".join(reinject))
    return "\n\n".join(parts)


async def load_prior_messages(
    session: AsyncSession,
    conversation_id: str,
    *,
    exclude_message_id: str | None = None,
    summary_text: str | None = None,
    compacted_at: datetime | None = None,
    max_messages: int | None = None,
    max_chars: int | None = None,
    include_summary_bridge: bool = True,
) -> list[dict[str, str]]:
    """
    拉取模型窗口历史（不含当前这条）。
    若有压缩检查点：只取 compacted_at 之后的消息，并前置摘要桥接。
    """
    settings = get_settings()
    limit = max_messages if max_messages is not None else settings.context_keep_recent_messages
    # 未压缩时仍允许更长滑动窗
    if not summary_text and max_messages is None:
        limit = DEFAULT_MAX_MESSAGES

    rows = (
        await session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc()),
        )
    ).all()

    out: list[dict[str, str]] = []
    for msg in rows:
        if exclude_message_id and msg.id == exclude_message_id:
            continue
        if msg.role not in _ALLOWED_ROLES:
            continue
        if compacted_at is not None and msg.created_at is not None:
            # 压缩点之前的原文不再进入模型窗口（仍在 DB 存档）
            msg_ts = msg.created_at
            if msg_ts.tzinfo is None and compacted_at.tzinfo is not None:
                # SQLite 可能丢 tz；按 naive 比较
                cut = compacted_at.replace(tzinfo=None)
                if msg_ts <= cut:
                    continue
            elif msg_ts <= compacted_at:
                continue
        content = (msg.content or "").strip()
        if not content:
            continue
        out.append({"role": msg.role, "content": content})

    if len(out) > limit:
        out = out[-limit:]

    if include_summary_bridge and summary_text and summary_text.strip():
        bridge = [
            {
                "role": "user",
                "content": f"{SUMMARY_PREFIX}\n{summary_text.strip()}",
            },
            {"role": "assistant", "content": SUMMARY_ACK},
        ]
        out = bridge + out

    # 可选再按字符压一次（压缩路径会传更大 max_chars）
    char_budget = max_chars if max_chars is not None else DEFAULT_MAX_CHARS
    while len(out) > 2 and _chars(out) > char_budget:
        # 尽量保住摘要桥接（前两条）
        if summary_text and len(out) > 2:
            out.pop(2)
        else:
            out.pop(0)

    return out


def assemble_chat_messages(
    *,
    system: str,
    history: list[dict[str, str]],
    latest_user: str,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> tuple[list[dict[str, str]], dict[str, int | bool]]:
    """
    组装 OpenAI 风格 messages：system + 裁剪后的历史 + 本轮 user。
    从最旧历史开始丢弃，直到总字符 ≤ max_chars（保留摘要桥接优先）。
    """
    latest = latest_user.strip()
    system_text = system.strip()
    fixed = len(system_text) + len(latest)
    budget = max(1_000, max_chars - fixed)

    trimmed = list(history)
    while trimmed and _chars(trimmed) > budget:
        # 若前两条是摘要桥接，优先丢后面的
        if (
            len(trimmed) > 2
            and trimmed[0].get("content", "").startswith(SUMMARY_PREFIX)
        ):
            trimmed.pop(2)
        else:
            trimmed.pop(0)

    if trimmed and trimmed[-1]["role"] == "user":
        trimmed.pop()

    messages: list[dict[str, str]] = [{"role": "system", "content": system_text}]
    messages.extend(trimmed)
    messages.append({"role": "user", "content": latest})

    has_summary = any(
        (m.get("content") or "").startswith(SUMMARY_PREFIX) for m in trimmed
    )
    stats: dict[str, int | bool] = {
        "historyCount": len(trimmed),
        "messageCount": len(messages),
        "chars": _chars(messages),
        "estimatedTokens": estimate_tokens_from_text(
            system_text + latest + "".join(m.get("content") or "" for m in trimmed),
        ),
        "hasSummary": has_summary,
    }
    return messages, stats


def _chars(messages: list[dict[str, str]]) -> int:
    return sum(len(m.get("content") or "") for m in messages)

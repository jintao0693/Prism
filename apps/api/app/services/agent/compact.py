"""会话上下文压缩：usage 触发 + 摘要检查点（借鉴 Codex compaction）。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.conversation import Conversation
from app.services.agent.context import (
    SUMMARY_PREFIX,
    estimate_tokens_from_text,
    load_prior_messages,
)
from app.services.providers.volcengine.client import VolcengineArkClient

logger = logging.getLogger(__name__)

_COMPACT_SYSTEM = """你是 Prism 的会话压缩器。把多轮对话压成一份给后续助手用的交接摘要。
只输出摘要正文，不要寒暄。建议结构：
1) 用户目标与约束
2) 已确认的事实 / 偏好 / 品牌要点
3) 已完成动作（生图/视频/检索等）
4) 未决问题与下一步
保持简洁，控制在 800 字内。""".strip()


@dataclass
class CompactResult:
    """压缩结果。"""

    did_compact: bool
    generation: int
    summary_chars: int = 0
    kept_messages: int = 0
    reason: str = ""


def should_compact(
    conversation: Conversation,
    *,
    window_message_count: int,
    pending_history_chars: int = 0,
) -> tuple[bool, str]:
    """是否需要压缩（按当前模型窗口，不是全库消息数）。"""
    settings = get_settings()
    if window_message_count < settings.context_compact_min_messages:
        return False, "messages_below_min"
    limit = int(settings.context_window_tokens * settings.context_compact_ratio)
    estimate = int(conversation.context_tokens_estimate or 0)
    if estimate >= limit:
        return True, f"tokens>={limit}"
    # usage 尚未回填 / 偏低时：窗口字符过大也压
    if pending_history_chars >= 10_000:
        return True, "chars_heuristic"
    return False, "ok"


async def compact_conversation(
    session: AsyncSession,
    conversation: Conversation,
    ark: VolcengineArkClient,
    *,
    exclude_message_id: str | None = None,
) -> CompactResult:
    """
    生成摘要检查点：不删旧消息；之后模型窗口 = 摘要 + compacted_at 之后的新消息。
    """
    settings = get_settings()
    if not ark.chat_model:
        return CompactResult(
            did_compact=False,
            generation=conversation.compact_generation,
            reason="no_chat_model",
        )

    # 压缩时看「尚未被摘要覆盖」的窗口内容
    history = await load_prior_messages(
        session,
        conversation.id,
        exclude_message_id=exclude_message_id,
        summary_text=None,
        compacted_at=conversation.compacted_at,
        max_messages=80,
        max_chars=40_000,
        include_summary_bridge=False,
    )
    if len(history) < settings.context_compact_min_messages:
        return CompactResult(
            did_compact=False,
            generation=conversation.compact_generation,
            reason="not_enough_history",
        )

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    if conversation.summary_text:
        transcript = (
            f"{SUMMARY_PREFIX}\n{conversation.summary_text}\n\n---\n\n{transcript}"
        )

    result = await ark.chat_completion(
        [
            {"role": "system", "content": _COMPACT_SYSTEM},
            {
                "role": "user",
                "content": f"请压缩以下对话：\n\n{transcript[:24000]}",
            },
        ],
        temperature=0.2,
    )
    summary = (result.content or "").strip()
    if not summary:
        return CompactResult(
            did_compact=False,
            generation=conversation.compact_generation,
            reason="empty_summary",
        )

    now = datetime.now(UTC)
    conversation.summary_text = summary
    conversation.compacted_at = now
    conversation.compact_generation = int(conversation.compact_generation or 0) + 1
    # 压缩后窗口估计：摘要 + 将保留的近期（本轮尚未计入）
    conversation.context_tokens_estimate = estimate_tokens_from_text(summary) + 200
    if result.prompt_tokens is not None:
        conversation.last_prompt_tokens = result.prompt_tokens
    if result.completion_tokens is not None:
        conversation.last_completion_tokens = result.completion_tokens

    await session.flush()
    logger.info(
        "会话 %s 已压缩 generation=%s chars=%s",
        conversation.id,
        conversation.compact_generation,
        len(summary),
    )
    return CompactResult(
        did_compact=True,
        generation=conversation.compact_generation,
        summary_chars=len(summary),
        kept_messages=settings.context_keep_recent_messages,
        reason="compacted",
    )


async def maybe_auto_compact(
    session: AsyncSession,
    conversation: Conversation,
    ark: VolcengineArkClient | None,
    *,
    exclude_message_id: str | None = None,
) -> CompactResult:
    """发消息前：超阈值则自动压缩。"""
    if ark is None or not ark.chat_model:
        return CompactResult(
            did_compact=False,
            generation=int(conversation.compact_generation or 0),
            reason="no_ark",
        )

    # 评估「当前窗口」体量（不含摘要桥接，避免重复压）
    history_preview = await load_prior_messages(
        session,
        conversation.id,
        exclude_message_id=exclude_message_id,
        summary_text=None,
        compacted_at=conversation.compacted_at,
        max_messages=80,
        max_chars=60_000,
        include_summary_bridge=False,
    )
    pending_chars = sum(len(m["content"]) for m in history_preview)
    need, reason = should_compact(
        conversation,
        window_message_count=len(history_preview),
        pending_history_chars=pending_chars,
    )
    if not need:
        return CompactResult(
            did_compact=False,
            generation=int(conversation.compact_generation or 0),
            reason=reason,
        )
    return await compact_conversation(
        session,
        conversation,
        ark,
        exclude_message_id=exclude_message_id,
    )


def apply_usage_to_conversation(
    conversation: Conversation,
    *,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None = None,
) -> None:
    """把本轮模型 usage 写回会话计量。"""
    if prompt_tokens is not None:
        conversation.last_prompt_tokens = prompt_tokens
        # 下一轮阈值主要看「已占用 prompt」
        conversation.context_tokens_estimate = prompt_tokens
    if completion_tokens is not None:
        conversation.last_completion_tokens = completion_tokens
    if total_tokens is not None and prompt_tokens is None:
        conversation.context_tokens_estimate = total_tokens

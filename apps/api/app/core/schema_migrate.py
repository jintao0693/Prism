"""开发期轻量列迁移：create_all 不会给已有表加列。"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

logger = logging.getLogger(__name__)

_CONVERSATION_COLUMNS: dict[str, str] = {
    "summary_text": "TEXT",
    "compacted_at": "TIMESTAMP",
    "compact_generation": "INTEGER DEFAULT 0",
    "context_tokens_estimate": "INTEGER DEFAULT 0",
    "last_prompt_tokens": "INTEGER",
    "last_completion_tokens": "INTEGER",
}


async def ensure_runtime_schema(engine: AsyncEngine) -> None:
    """为 conversations 补齐压缩相关列（SQLite / Postgres）。"""
    dialect = engine.dialect.name
    async with engine.begin() as conn:
        existing = await _existing_columns(conn, "conversations", dialect)
        for name, col_type in _CONVERSATION_COLUMNS.items():
            if name in existing:
                continue
            sql = f"ALTER TABLE conversations ADD COLUMN {name} {col_type}"
            await conn.execute(text(sql))
            logger.info("已添加列 conversations.%s", name)


async def _existing_columns(
    conn: AsyncConnection,
    table: str,
    dialect: str,
) -> set[str]:
    if dialect == "sqlite":
        rows = (await conn.execute(text(f"PRAGMA table_info({table})"))).all()
        return {str(r[1]) for r in rows}
    rows = (
        await conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table
                """,
            ),
            {"table": table},
        )
    ).all()
    return {str(r[0]) for r in rows}

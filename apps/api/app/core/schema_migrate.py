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

_JOB_COLUMNS: dict[str, str] = {
    "conversation_id": "VARCHAR(64)",
    "external_task_id": "VARCHAR(128)",
    "progress_status": "VARCHAR(64)",
    "progress_elapsed": "FLOAT DEFAULT 0",
    "mode": "VARCHAR(32)",
}


async def ensure_runtime_schema(engine: AsyncEngine) -> None:
    """为已有表补齐开发期新增列（SQLite / Postgres）。"""
    dialect = engine.dialect.name
    async with engine.begin() as conn:
        await _ensure_columns(conn, "conversations", _CONVERSATION_COLUMNS, dialect)
        await _ensure_columns(conn, "generation_jobs", _JOB_COLUMNS, dialect)


async def _ensure_columns(
    conn: AsyncConnection,
    table: str,
    columns: dict[str, str],
    dialect: str,
) -> None:
    existing = await _existing_columns(conn, table, dialect)
    if not existing and dialect == "sqlite":
        # 表尚未 create_all 时跳过；启动稍后会建表
        return
    for name, col_type in columns.items():
        if name in existing:
            continue
        sql = f"ALTER TABLE {table} ADD COLUMN {name} {col_type}"
        await conn.execute(text(sql))
        logger.info("已添加列 %s.%s", table, name)


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

"""向量索引：Postgres + pgvector 优先，SQLite 回退到条目 embedding_json。"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import engine
from app.services.knowledge.embedding_utils import cosine_similarity, loads_embedding

logger = logging.getLogger(__name__)

EMBED_DIM = 1024


def uses_pgvector() -> bool:
    """当前 DATABASE_URL 是否走 Postgres/pgvector。"""
    return "postgresql" in get_settings().database_url


def _vec_literal(vec: list[float]) -> str:
    """pgvector 文本字面量。"""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


async def ensure_vector_schema() -> None:
    """Postgres 下创建 extension + knowledge_vectors 表。"""
    if not uses_pgvector():
        return
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    item_id VARCHAR(64) PRIMARY KEY,
                    tenant_id VARCHAR(64) NOT NULL,
                    knowledge_base_id VARCHAR(64) NOT NULL,
                    item_type VARCHAR(32) NOT NULL,
                    embedding vector({EMBED_DIM}) NOT NULL
                )
                """,
            ),
        )
        await conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_knowledge_vectors_kb
                ON knowledge_vectors (knowledge_base_id, tenant_id, item_type)
                """,
            ),
        )
    logger.info("pgvector knowledge_vectors 已就绪")


async def upsert_vector(
    session: AsyncSession,
    *,
    item_id: str,
    tenant_id: str,
    knowledge_base_id: str,
    item_type: str,
    vec: list[float],
) -> None:
    """写入 / 更新向量索引（仅 Postgres）。"""
    if not uses_pgvector():
        return
    if len(vec) != EMBED_DIM:
        # 维度不一致时仍写入 JSON；索引侧跳过以免炸表
        logger.warning(
            "向量维度 %s != %s，跳过 pgvector upsert (%s)",
            len(vec),
            EMBED_DIM,
            item_id,
        )
        return
    lit = _vec_literal(vec)
    await session.execute(
        text(
            """
            INSERT INTO knowledge_vectors
                (item_id, tenant_id, knowledge_base_id, item_type, embedding)
            VALUES
                (:item_id, :tenant_id, :kb_id, :item_type, CAST(:embedding AS vector))
            ON CONFLICT (item_id) DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                knowledge_base_id = EXCLUDED.knowledge_base_id,
                item_type = EXCLUDED.item_type,
                embedding = EXCLUDED.embedding
            """,
        ),
        {
            "item_id": item_id,
            "tenant_id": tenant_id,
            "kb_id": knowledge_base_id,
            "item_type": item_type,
            "embedding": lit,
        },
    )


async def delete_vector(session: AsyncSession, item_id: str) -> None:
    """删除索引行。"""
    if not uses_pgvector():
        return
    await session.execute(
        text("DELETE FROM knowledge_vectors WHERE item_id = :item_id"),
        {"item_id": item_id},
    )


async def search_by_vector(
    session: AsyncSession,
    *,
    tenant_id: str,
    knowledge_base_id: str,
    query_vec: list[float],
    top_k: int = 5,
    item_type: str | None = None,
) -> list[tuple[str, float]] | None:
    """
    返回 [(item_id, cosine_similarity), ...]。
    Postgres 用 pgvector；否则返回 None，由调用方走 JSON 全表扫。
    """
    if uses_pgvector() and len(query_vec) == EMBED_DIM:
        lit = _vec_literal(query_vec)
        type_clause = "AND item_type = :item_type" if item_type else ""
        params: dict = {
            "tenant_id": tenant_id,
            "kb_id": knowledge_base_id,
            "embedding": lit,
            "top_k": top_k,
        }
        if item_type:
            params["item_type"] = item_type
        rows = (
            await session.execute(
                text(
                    f"""
                    SELECT item_id,
                           1 - (embedding <=> CAST(:embedding AS vector)) AS score
                    FROM knowledge_vectors
                    WHERE tenant_id = :tenant_id
                      AND knowledge_base_id = :kb_id
                      {type_clause}
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :top_k
                    """,
                ),
                params,
            )
        ).all()
        return [(str(r[0]), float(r[1])) for r in rows]

    return None


def score_rows_json(
    rows: list,
    query_vec: list[float],
) -> list[tuple[object, float]]:
    """SQLite / 回退：对 ORM 行用 embedding_json 算余弦相似。"""
    scored: list[tuple[object, float]] = []
    for item in rows:
        item_vec = loads_embedding(getattr(item, "embedding_json", None))
        if not item_vec:
            continue
        scored.append((item, cosine_similarity(query_vec, item_vec)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

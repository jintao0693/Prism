"""数据库引擎与会话。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """ORM 基类。"""


def _make_engine():
    settings = get_settings()
    connect_args = {}
    # SQLite 需要关闭同线程检查
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_async_engine(
        settings.database_url,
        # 默认关闭 SQL 回显，避免刷屏；需要时设 SQL_ECHO=true
        echo=False,
        connect_args=connect_args,
    )


engine = _make_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：请求级异步会话（由业务显式 commit）。"""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """创建全部表（开发期便捷；生产请走 Alembic）。"""
    # 导入模型以注册 metadata
    from app import models  # noqa: F401
    from app.core.schema_migrate import ensure_runtime_schema

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_runtime_schema(engine)

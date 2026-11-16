"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.bootstrap.seed import seed_demo_data
from app.core.config import get_settings
from app.core.db import SessionLocal, init_db
from app.core.logging import setup_logging
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """启动：建表 + 种子；关闭：清理 Redis。"""
    settings = get_settings()
    setup_logging(settings.debug)

    # 确保本地数据目录存在
    Path("./data").mkdir(parents=True, exist_ok=True)
    Path(settings.local_storage_dir).mkdir(parents=True, exist_ok=True)

    await init_db()
    async with SessionLocal() as session:
        await seed_demo_data(session)

    yield
    await close_redis()


def create_app() -> FastAPI:
    """应用工厂。"""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    # 本地存储静态访问（演示）
    media_root = Path(settings.local_storage_dir)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media_root)), name="media")

    @app.get("/health")
    async def health() -> dict:
        """健康检查（含数据库探测）。"""
        db_ok = False
        try:
            from sqlalchemy import text

            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
                db_ok = True
        except Exception:
            db_ok = False
        return {
            "ok": db_ok,
            "db": db_ok,
            "env": settings.app_env,
            "agentDemoMode": settings.agent_demo_mode,
        }

    return app


app = create_app()

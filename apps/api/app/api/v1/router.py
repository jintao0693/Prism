"""API v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import assets, auth, conversations, jobs, knowledge, settings, workspaces

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(conversations.router)
api_router.include_router(knowledge.router)
api_router.include_router(assets.router)
api_router.include_router(jobs.router)
api_router.include_router(settings.router)

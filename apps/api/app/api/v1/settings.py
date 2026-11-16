"""设置与用量、火山模型配置。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, get_current_context
from app.core.config import get_settings
from app.core.db import get_db
from app.schemas.common import UsageSummaryOut
from app.schemas.settings import (
    ProviderTestResult,
    VolcengineProviderOut,
    VolcengineProviderUpdate,
)
from app.services.providers.registry import (
    build_volcengine_client,
    get_or_create_volcengine_config,
    save_volcengine_config,
    to_snapshot,
)
from app.services.providers.volcengine.client import VolcengineArkError
from app.services.quota.usage import sync_quota_usage

router = APIRouter(prefix="/settings", tags=["设置"])


def _to_out(snap) -> VolcengineProviderOut:
    return VolcengineProviderOut(
        provider=snap.provider,
        enabled=snap.enabled,
        base_url=snap.base_url,
        chatModel=snap.chat_model,
        imageModel=snap.image_model,
        videoModel=snap.video_model,
        embeddingModel=snap.embedding_model,
        apiKeyMasked=snap.api_key_masked,
        hasApiKey=snap.has_api_key,
        note=snap.note,
    )


@router.get("/usage", response_model=UsageSummaryOut)
async def usage_summary(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryOut:
    """本月用量（按生成资产实算，排除上传与种子画廊）。"""
    row = await sync_quota_usage(db, ctx.tenant_id)
    await db.commit()
    return UsageSummaryOut(
        imagesThisMonth=row.images_count,
        videosThisMonth=row.videos_count,
    )


@router.get("/providers")
async def list_providers(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """供应商总览（兼容旧前端字段）。"""
    row = await get_or_create_volcengine_config(db, ctx.tenant_id)
    await db.commit()
    snap = to_snapshot(row)
    settings = get_settings()
    return {
        "agentModel": snap.chat_model or settings.prism_agent_model,
        "agentDemoMode": settings.agent_demo_mode and not (snap.enabled and snap.has_api_key),
        "mediaProvider": "volcengine_ark" if snap.enabled and snap.has_api_key else "demo",
        "volcengine": _to_out(snap).model_dump(by_alias=True),
    }


@router.get("/providers/volcengine", response_model=VolcengineProviderOut)
async def get_volcengine(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> VolcengineProviderOut:
    """读取火山方舟配置。"""
    row = await get_or_create_volcengine_config(db, ctx.tenant_id)
    await db.commit()
    return _to_out(to_snapshot(row))


@router.put("/providers/volcengine", response_model=VolcengineProviderOut)
async def update_volcengine(
    body: VolcengineProviderUpdate,
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> VolcengineProviderOut:
    """保存火山方舟配置（可在前端设置页提交）。"""
    row = await save_volcengine_config(
        db,
        ctx.tenant_id,
        api_key=body.api_key,
        enabled=body.enabled,
        base_url=body.base_url,
        chat_model=body.chat_model,
        image_model=body.image_model,
        video_model=body.video_model,
        embedding_model=body.embedding_model,
        note=body.note,
    )
    await db.commit()
    await db.refresh(row)
    return _to_out(to_snapshot(row))


@router.post("/providers/volcengine/test", response_model=ProviderTestResult)
async def test_volcengine(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> ProviderTestResult:
    """用当前配置测对话接口连通性。"""
    client = await build_volcengine_client(db, ctx.tenant_id)
    if not client:
        return ProviderTestResult(
            ok=False,
            message="未启用或未配置 API Key",
            detail="请先在设置中填写火山方舟 Key 并开启启用开关",
        )
    try:
        text = await client.chat(
            [{"role": "user", "content": "用五个字内回复：连通成功"}],
        )
        return ProviderTestResult(ok=True, message="对话接口连通成功", detail=text[:200])
    except VolcengineArkError as exc:
        return ProviderTestResult(ok=False, message="调用失败", detail=str(exc))

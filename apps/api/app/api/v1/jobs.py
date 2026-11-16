"""异步任务查询。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.models.job import GenerationJob

router = APIRouter(prefix="/jobs", tags=["任务"])


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """查询生成任务状态。"""
    job = await db.get(GenerationJob, job_id)
    if not job or job.tenant_id != ctx.tenant_id or job.workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "id": job.id,
        "jobType": job.job_type,
        "status": job.status,
        "resultAssetId": job.result_asset_id,
        "errorMessage": job.error_message,
    }

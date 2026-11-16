"""异步任务查询。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.models.job import GenerationJob

router = APIRouter(prefix="/jobs", tags=["任务"])


def _prompt_snippet(prompt: str, *, full: bool = False) -> str:
    if full:
        return prompt
    text = (prompt or "").strip()
    if len(text) <= 120:
        return text
    return text[:120] + "…"


def _job_payload(job: GenerationJob, *, full_prompt: bool = False) -> dict:
    return {
        "id": job.id,
        "jobType": job.job_type,
        "status": job.status,
        "prompt": _prompt_snippet(job.prompt, full=full_prompt),
        "resultAssetId": job.result_asset_id,
        "errorMessage": job.error_message,
        "conversationId": job.conversation_id,
        "progressStatus": job.progress_status,
        "progressElapsed": job.progress_elapsed,
        "createdAt": job.created_at.isoformat(),
    }


@router.get("")
async def list_jobs(
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """最近生成任务（工作空间内）。"""
    assert ctx.workspace_id
    rows = (
        await db.scalars(
            select(GenerationJob)
            .where(
                GenerationJob.tenant_id == ctx.tenant_id,
                GenerationJob.workspace_id == ctx.workspace_id,
            )
            .order_by(GenerationJob.created_at.desc())
            .limit(30),
        )
    ).all()
    return [_job_payload(j) for j in rows]


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
    return _job_payload(job, full_prompt=True)
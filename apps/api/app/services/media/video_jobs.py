"""后台视频生成任务（SSE 断开后仍继续跑）。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.core.db import SessionLocal
from app.models.asset import Asset
from app.models.job import GenerationJob
from app.services.agent.asset_memory import dumps_asset_meta
from app.services.media.gateway import MediaGateway
from app.services.media.prompt_compiler import format_ark_error
from app.services.quota.usage import record_media_generation

# 持有 Task 引用，避免 SSE 断开时被 GC 取消
_RUNNING: set[asyncio.Task[Any]] = set()


async def get_job_snapshot(job_id: str) -> dict[str, Any] | None:
    """读取任务当前状态（独立会话）。"""
    async with SessionLocal() as session:
        job = await session.get(GenerationJob, job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "status": job.status,
            "jobType": job.job_type,
            "prompt": job.prompt,
            "resultAssetId": job.result_asset_id,
            "errorMessage": job.error_message,
            "conversationId": job.conversation_id,
            "progressStatus": job.progress_status,
            "progressElapsed": job.progress_elapsed,
            "externalTaskId": job.external_task_id,
            "mode": job.mode,
        }


async def start_video_job(
    *,
    tenant_id: str,
    workspace_id: str,
    conversation_id: str,
    prompt: str,
    mode: str,
    image_bytes: bytes | None,
    parent_id: str | None,
) -> str:
    """创建 GenerationJob 并后台执行；不写 assistant Message。"""
    job_id = f"j_{uuid.uuid4().hex[:12]}"
    async with SessionLocal() as session:
        job = GenerationJob(
            id=job_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            job_type="video",
            status="running",
            prompt=prompt,
            conversation_id=conversation_id,
            mode=mode,
        )
        session.add(job)
        await session.commit()

    task = asyncio.create_task(
        _execute_video_job(
            job_id=job_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            prompt=prompt,
            mode=mode,
            image_bytes=image_bytes,
            parent_id=parent_id,
        ),
    )
    _RUNNING.add(task)
    task.add_done_callback(_RUNNING.discard)
    return job_id


async def _execute_video_job(
    *,
    job_id: str,
    tenant_id: str,
    workspace_id: str,
    conversation_id: str,
    prompt: str,
    mode: str,
    image_bytes: bytes | None,
    parent_id: str | None,
) -> None:
    async with SessionLocal() as session:
        try:
            media = await MediaGateway.for_tenant(session, tenant_id)

            async def on_progress(status: str, elapsed: float, task_id: str) -> None:
                async with SessionLocal() as prog:
                    row = await prog.get(GenerationJob, job_id)
                    if not row:
                        return
                    row.progress_status = status
                    row.progress_elapsed = elapsed
                    row.external_task_id = task_id
                    await prog.commit()

            asset_id, result, key = await media.generate_video(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                prompt=prompt,
                mode=mode,
                image_bytes=image_bytes,
                on_progress=on_progress,
            )
            compiled = media.last_compiled
            meta = dumps_asset_meta(
                prompt=prompt,
                mode=mode,
                parent_asset_id=parent_id,
                provider=media.provider.name,
                extra={
                    "compiled_prompt": (compiled.text[:800] if compiled else ""),
                    "compiler": compiled.extras if compiled else {},
                },
            )
            asset = Asset(
                id=asset_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                name=result.filename,
                kind="video",
                storage_key=key,
                mime_type=result.mime_type,
                meta=meta,
                source_conversation_id=conversation_id,
                source_job_id=job_id,
            )
            session.add(asset)
            await record_media_generation(session, tenant_id, kind="video")

            job = await session.get(GenerationJob, job_id)
            if job:
                job.status = "succeeded"
                job.result_asset_id = asset_id
            await session.commit()
        except Exception as exc:
            async with SessionLocal() as fail:
                job = await fail.get(GenerationJob, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = format_ark_error(exc)
                await fail.commit()
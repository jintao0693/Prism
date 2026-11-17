"""生视频任务定义（进程内后台）。"""

from __future__ import annotations

from app.services.media.video_jobs import start_video_job


async def enqueue_generate_video(
    *,
    tenant_id: str,
    workspace_id: str,
    conversation_id: str,
    prompt: str,
    mode: str = "text_to_video",
    image_bytes: bytes | None = None,
    parent_id: str | None = None,
) -> str:
    """投递生视频任务（当前走 asyncio 后台 Job）。"""
    return await start_video_job(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        prompt=prompt,
        mode=mode,
        image_bytes=image_bytes,
        parent_id=parent_id,
    )
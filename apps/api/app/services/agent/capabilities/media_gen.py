"""媒体生成能力：注册到 Pydantic AI Agent 的工具。"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.core.storage import get_storage
from app.models.asset import Asset
from app.services.agent.asset_memory import (
    dumps_asset_meta,
    read_asset_bytes,
    resolve_last_image_asset,
)
from app.services.agent.deps import PrismDeps


def register_media_tools(agent: Agent[PrismDeps, str]) -> None:
    """把生图/生视频工具挂到 Agent 上。"""

    @agent.tool
    async def text_to_image(ctx: RunContext[PrismDeps], prompt: str) -> str:
        """根据文本描述生成图片，返回资产 ID。"""
        return await _gen_image(ctx.deps, prompt, mode="text_to_image")

    @agent.tool
    async def image_to_image(ctx: RunContext[PrismDeps], prompt: str) -> str:
        """基于本会话上一张图做图生图编辑。"""
        return await _gen_image(ctx.deps, prompt, mode="image_to_image")

    @agent.tool
    async def text_to_video(
        ctx: RunContext[PrismDeps],
        prompt: str,
        duration: int = 5,
    ) -> str:
        """根据文本生成短视频，返回资产 ID。"""
        return await _gen_video(ctx.deps, prompt, mode="text_to_video", duration=duration)

    @agent.tool
    async def image_to_video(
        ctx: RunContext[PrismDeps],
        prompt: str,
        duration: int = 5,
    ) -> str:
        """基于本会话上一张图生成视频。"""
        return await _gen_video(ctx.deps, prompt, mode="image_to_video", duration=duration)


async def _gen_image(deps: PrismDeps, prompt: str, *, mode: str) -> str:
    parent = None
    image_bytes = None
    if mode == "image_to_image":
        parent = await resolve_last_image_asset(
            deps.db,
            conversation_id=deps.conversation_id,
            tenant_id=deps.tenant_id,
        )
        if parent:
            image_bytes = read_asset_bytes(parent)
        if not image_bytes:
            mode = "text_to_image"
            parent = None

    asset_id, result, key = await deps.media.generate_image(
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        prompt=prompt,
        mode=mode,
        image_bytes=image_bytes,
    )
    asset = Asset(
        id=asset_id,
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        name=result.filename,
        kind="image",
        storage_key=key,
        mime_type=result.mime_type,
        meta=dumps_asset_meta(
            prompt=prompt,
            mode=mode,
            parent_asset_id=parent.id if parent else None,
            provider=deps.media.provider.name,
        ),
        source_conversation_id=deps.conversation_id,
    )
    deps.db.add(asset)
    url = get_storage().public_url(key)
    deps.generated_assets.append(
        {
            "id": asset_id,
            "label": "图生图" if mode == "image_to_image" else "生成图",
            "tone": "a",
            "kind": "image",
            "url": url,
            "parentAssetId": parent.id if parent else None,
        },
    )
    await deps.db.flush()
    return f"已生成图片资产 {asset_id}（{mode}）"


async def _gen_video(
    deps: PrismDeps,
    prompt: str,
    *,
    mode: str,
    duration: int,
) -> str:
    parent = None
    image_bytes = None
    if mode == "image_to_video":
        parent = await resolve_last_image_asset(
            deps.db,
            conversation_id=deps.conversation_id,
            tenant_id=deps.tenant_id,
        )
        if parent:
            image_bytes = read_asset_bytes(parent)
        if not image_bytes:
            mode = "text_to_video"
            parent = None

    asset_id, result, key = await deps.media.generate_video(
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        prompt=prompt,
        mode=mode,
        image_bytes=image_bytes,
        duration=duration,
    )
    asset = Asset(
        id=asset_id,
        tenant_id=deps.tenant_id,
        workspace_id=deps.workspace_id,
        name=result.filename,
        kind="video",
        storage_key=key,
        mime_type=result.mime_type,
        meta=dumps_asset_meta(
            prompt=prompt,
            mode=mode,
            parent_asset_id=parent.id if parent else None,
            provider=deps.media.provider.name,
        ),
        source_conversation_id=deps.conversation_id,
    )
    deps.db.add(asset)
    url = get_storage().public_url(key)
    deps.generated_assets.append(
        {
            "id": asset_id,
            "label": "图生视频" if mode == "image_to_video" else "生成视频",
            "tone": "c",
            "kind": "video",
            "url": url,
            "parentAssetId": parent.id if parent else None,
        },
    )
    await deps.db.flush()
    return f"已生成视频资产 {asset_id}（{mode}）"

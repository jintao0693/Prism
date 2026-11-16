"""媒体生成能力：注册到 Pydantic AI Agent 的工具。"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.models.asset import Asset
from app.services.agent.deps import PrismDeps


def register_media_tools(agent: Agent[PrismDeps, str]) -> None:
    """把生图/生视频工具挂到 Agent 上。"""

    @agent.tool
    async def text_to_image(ctx: RunContext[PrismDeps], prompt: str) -> str:
        """根据文本描述生成图片，返回资产 ID。"""
        deps = ctx.deps
        asset_id, result, key = await deps.media.generate_image(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=prompt,
            mode="text_to_image",
        )
        asset = Asset(
            id=asset_id,
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            name=result.filename,
            kind="image",
            storage_key=key,
            mime_type=result.mime_type,
            meta=result.meta,
            source_conversation_id=deps.conversation_id,
        )
        deps.db.add(asset)
        deps.generated_assets.append(
            {"id": asset_id, "label": "生成图", "tone": "a", "kind": "image"},
        )
        await deps.db.flush()
        return f"已生成图片资产 {asset_id}"

    @agent.tool
    async def text_to_video(ctx: RunContext[PrismDeps], prompt: str, duration: int = 5) -> str:
        """根据文本生成短视频，返回资产 ID。"""
        deps = ctx.deps
        asset_id, result, key = await deps.media.generate_video(
            tenant_id=deps.tenant_id,
            workspace_id=deps.workspace_id,
            prompt=prompt,
            mode="text_to_video",
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
            meta=result.meta,
            source_conversation_id=deps.conversation_id,
        )
        deps.db.add(asset)
        deps.generated_assets.append(
            {"id": asset_id, "label": "生成视频", "tone": "c", "kind": "video"},
        )
        await deps.db.flush()
        return f"已生成视频资产 {asset_id}"

"""Agent 运行依赖注入对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.media.gateway import MediaGateway


@dataclass
class PrismDeps:
    """一次 Agent 运行所需的上下文。"""

    tenant_id: str
    workspace_id: str
    conversation_id: str
    db: AsyncSession
    media: MediaGateway = field(default_factory=MediaGateway)
    knowledge_base_ids: list[str] = field(default_factory=list)
    # 运行过程中收集到的产物，供 SSE 回传
    generated_assets: list[dict] = field(default_factory=list)

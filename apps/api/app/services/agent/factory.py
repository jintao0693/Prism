"""组装 Pydantic AI Agent（轻量 harness：自研 tools + 可选官方模型）。"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.services.agent.instructions import PRISM_SYSTEM_INSTRUCTIONS

logger = logging.getLogger(__name__)


def build_prism_agent() -> Any | None:
    """
    创建 Prism Agent。
    演示模式下返回 None，由上层走本地启发式回复，避免强依赖外网模型。
    """
    settings = get_settings()
    if settings.agent_demo_mode:
        logger.info("AGENT_DEMO_MODE=true，跳过真实 Pydantic AI 模型调用")
        return None

    # 延迟导入：演示环境可不装齐全部模型 Provider 依赖
    from pydantic_ai import Agent

    from app.services.agent.capabilities import (
        register_knowledge_tools,
        register_media_tools,
    )
    from app.services.agent.deps import PrismDeps

    agent = Agent(
        settings.prism_agent_model,
        deps_type=PrismDeps,
        instructions=PRISM_SYSTEM_INSTRUCTIONS,
    )
    register_media_tools(agent)
    register_knowledge_tools(agent)
    # 说明：pydantic-ai-harness 的 memory/context 等可在此按需 capabilities=[...] 挂载
    return agent

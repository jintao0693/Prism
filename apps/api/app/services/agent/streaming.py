"""Agent 运行 → SSE 事件映射。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.demo_runner import run_demo_agent
from app.services.agent.deps import PrismDeps
from app.services.agent.factory import build_prism_agent
from app.services.providers.registry import build_volcengine_client


async def iter_agent_events(
    deps: PrismDeps,
    user_text: str,
    *,
    session: AsyncSession | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """统一入口：火山配置 / Pydantic AI / 本地演示。"""
    db = session or deps.db
    ark = await build_volcengine_client(db, deps.tenant_id)

    # 有火山 Key 时，优先走火山链路（对话+工具启发式）
    if ark:
        async for event in run_demo_agent(deps, user_text, ark=ark):
            yield event
        return

    agent = build_prism_agent()
    if agent is None:
        async for event in run_demo_agent(deps, user_text, ark=None):
            yield event
        return

    yield {"type": "text.delta", "data": {"text": ""}}
    result = await agent.run(user_text, deps=deps)
    content = result.output if isinstance(result.output, str) else str(result.output)
    yield {"type": "text.delta", "data": {"text": content}}
    yield {
        "type": "message.done",
        "data": {
            "content": content,
            "results": deps.generated_assets,
            "toolLabel": "agent · 完成" if deps.generated_assets else None,
        },
    }


def encode_sse(event: dict[str, Any]) -> str:
    """编码为 SSE 文本帧。"""
    return f"event: {event['type']}\ndata: {json.dumps(event.get('data', {}), ensure_ascii=False)}\n\n"

"""会话媒体记忆：上一张图、血缘 meta、注入模型上下文。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.asset import Asset

_REFINE_RE = re.compile(r"再|改|偏|换成|上一张|这张|基于|在此基础上|微调|更")
_TO_VIDEO_RE = re.compile(r"视频|短片|出片|动起来|做成片|图生视频")


def dumps_asset_meta(
    *,
    prompt: str,
    mode: str,
    parent_asset_id: str | None = None,
    provider: str = "",
    extra: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "prompt": prompt[:500],
        "mode": mode,
        "provider": provider,
    }
    if parent_asset_id:
        payload["parent_asset_id"] = parent_asset_id
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False)


def loads_asset_meta(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"legacy": raw}
    except json.JSONDecodeError:
        return {"legacy": raw}


async def list_conversation_assets(
    session: AsyncSession,
    *,
    conversation_id: str,
    tenant_id: str,
    limit: int = 8,
) -> list[Asset]:
    rows = (
        await session.scalars(
            select(Asset)
            .where(
                Asset.source_conversation_id == conversation_id,
                Asset.tenant_id == tenant_id,
                Asset.is_deleted.is_(False),
            )
            .order_by(Asset.created_at.desc())
            .limit(limit),
        )
    ).all()
    return list(rows)


async def resolve_last_image_asset(
    session: AsyncSession,
    *,
    conversation_id: str,
    tenant_id: str,
) -> Asset | None:
    rows = await list_conversation_assets(
        session,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        limit=20,
    )
    for asset in rows:
        if asset.kind == "image" and asset.storage_key:
            return asset
    return None


async def resolve_reference_image(
    session: AsyncSession,
    *,
    asset_ids: list[str],
    tenant_id: str,
    workspace_id: str,
) -> Asset | None:
    """按本轮显式 referenceAssetIds 取第一张可用图片。"""
    for asset_id in asset_ids:
        if not asset_id:
            continue
        asset = await session.get(Asset, asset_id)
        if (
            asset
            and asset.tenant_id == tenant_id
            and asset.workspace_id == workspace_id
            and not asset.is_deleted
            and asset.kind == "image"
            and asset.storage_key
        ):
            return asset
    return None


def read_asset_bytes(asset: Asset) -> bytes | None:
    if not asset.storage_key:
        return None
    path = get_storage().resolve_path(asset.storage_key)
    if not path.exists():
        return None
    return path.read_bytes()


def public_asset_url(asset: Asset) -> str | None:
    if not asset.storage_key:
        return None
    return get_storage().public_url(asset.storage_key)


def format_media_context(assets: list[Asset]) -> str:
    """写入模型可见的媒体记忆（文本描述，不塞大图）。"""
    if not assets:
        return ""
    lines = ["【本会话近期生成资产】"]
    for asset in assets[:6]:
        meta = loads_asset_meta(asset.meta)
        mode = meta.get("mode") or asset.kind
        prompt = meta.get("prompt") or ""
        url = public_asset_url(asset) or ""
        lines.append(
            f"- {asset.id} · {asset.kind} · mode={mode}"
            + (f" · prompt={prompt[:60]}" if prompt else "")
            + (f" · url={url}" if url else ""),
        )
    lines.append(
        "若用户附带了参考图，或说「上一张/这张/再改一点」，优先对参考/最近一张 image 做 image_to_image；"
        "若说「做成视频」，优先 image_to_video。",
    )
    return "\n".join(lines)


def wants_image_refine(user_text: str) -> bool:
    return bool(_REFINE_RE.search(user_text))


def wants_image_to_video(user_text: str) -> bool:
    return bool(_TO_VIDEO_RE.search(user_text))

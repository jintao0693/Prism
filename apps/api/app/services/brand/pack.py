"""工作空间 Brand Pack：可编辑品牌约束，注入提示词编译。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace

DEFAULT_BRAND_PACK = {
    "name": "默认品牌包",
    "primaryColor": "#1B1F3B",
    "accentColor": "#F0C75E",
    "primaryColorName": "深空靛",
    "accentColorName": "星辉金",
    "keywords": ["安静", "干净留白", "开放世界探索"],
    "forbidden": ["高饱和霓虹紫", "赛博霓虹边框", "过曝金光"],
    "toneHint": "气质安静、有召唤感，适合商店页与社媒主视觉。",
}


@dataclass(frozen=True)
class BrandPack:
    name: str
    primary_color: str
    accent_color: str
    primary_color_name: str
    accent_color_name: str
    keywords: list[str]
    forbidden: list[str]
    tone_hint: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "primaryColor": self.primary_color,
            "accentColor": self.accent_color,
            "primaryColorName": self.primary_color_name,
            "accentColorName": self.accent_color_name,
            "keywords": self.keywords,
            "forbidden": self.forbidden,
            "toneHint": self.tone_hint,
        }

    def prompt_hint(self) -> str:
        keys = "、".join(self.keywords[:6]) if self.keywords else ""
        bans = "、".join(self.forbidden[:6]) if self.forbidden else ""
        parts = [
            f"品牌「{self.name}」：主色 {self.primary_color_name} {self.primary_color}，"
            f"点缀 {self.accent_color_name} {self.accent_color}。",
        ]
        if keys:
            parts.append(f"关键词：{keys}。")
        if bans:
            parts.append(f"禁用：{bans}。")
        if self.tone_hint:
            parts.append(self.tone_hint)
        return "".join(parts)


def pack_from_dict(data: dict | None) -> BrandPack:
    raw = {**DEFAULT_BRAND_PACK, **(data or {})}
    return BrandPack(
        name=str(raw.get("name") or DEFAULT_BRAND_PACK["name"]),
        primary_color=str(raw.get("primaryColor") or DEFAULT_BRAND_PACK["primaryColor"]),
        accent_color=str(raw.get("accentColor") or DEFAULT_BRAND_PACK["accentColor"]),
        primary_color_name=str(
            raw.get("primaryColorName") or DEFAULT_BRAND_PACK["primaryColorName"],
        ),
        accent_color_name=str(
            raw.get("accentColorName") or DEFAULT_BRAND_PACK["accentColorName"],
        ),
        keywords=[str(x) for x in (raw.get("keywords") or [])][:12],
        forbidden=[str(x) for x in (raw.get("forbidden") or [])][:12],
        tone_hint=str(raw.get("toneHint") or DEFAULT_BRAND_PACK["toneHint"]),
    )


def _read_brand_json(ws: Workspace) -> dict | None:
    raw = getattr(ws, "brand_pack_json", None) or ""
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


async def get_workspace_brand_pack(
    session: AsyncSession,
    workspace_id: str,
) -> BrandPack:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        return pack_from_dict(None)
    return pack_from_dict(_read_brand_json(ws))


async def save_workspace_brand_pack(
    session: AsyncSession,
    workspace_id: str,
    data: dict,
) -> BrandPack:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise ValueError("工作空间不存在")
    pack = pack_from_dict(data)
    ws.brand_pack_json = json.dumps(pack.to_dict(), ensure_ascii=False)
    await session.flush()
    return pack

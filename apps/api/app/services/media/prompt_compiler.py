"""Seedream / Seedance 提示词编译：补品牌约束、负面词与成片规格。"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.brand.pack import BrandPack


@dataclass(frozen=True)
class CompiledPrompt:
    text: str
    raw: str
    extras: dict[str, str]


_IMAGE_NEGATIVES = (
    "高饱和霓虹紫, 赛博霓虹边框, 脏乱噪点, 扭曲手指, 多余肢体, "
    "低清晰度, 文字水印, logo 乱入, 过度曝光"
)

_VIDEO_NEGATIVES = (
    "剧烈甩镜, 过曝金光, 闪烁频闪, 画面撕裂, 字幕乱入, "
    "高饱和霓虹紫, 低帧卡顿"
)

_DEFAULT_BRAND_HINTS = (
    "若涉及《幻境：星落传说》或同类二次元开放世界："
    "主色深空靛 #1B1F3B，点缀星辉金 #F0C75E；气质安静、干净留白。"
)


def compile_media_prompt(
    raw: str,
    *,
    kind: str,
    mode: str = "",
    brand_pack: BrandPack | None = None,
    size_hint: str = "",
    ratio_hint: str = "",
) -> CompiledPrompt:
    """
    在用户原话上追加成片约束，不覆盖用户明确指令。
    kind: image | video
    """
    text = (raw or "").strip()
    if not text:
        text = "高质量商业视觉创作" if kind == "image" else "高质量氛围短视频"

    extras: dict[str, str] = {}
    parts = [text]

    brand_text = brand_pack.prompt_hint() if brand_pack else _DEFAULT_BRAND_HINTS
    color_tokens = []
    if brand_pack:
        color_tokens = [
            brand_pack.primary_color,
            brand_pack.accent_color,
            brand_pack.primary_color_name,
            brand_pack.accent_color_name,
        ]
    else:
        color_tokens = ["#1B1F3B", "深空靛", "星辉金", "#F0C75E"]
    if not any(x and x in text for x in color_tokens):
        parts.append(brand_text)
        extras["brandHints"] = brand_pack.name if brand_pack else "default"

    if kind == "image":
        if ratio_hint:
            parts.append(f"画面比例约 {ratio_hint}。")
            extras["ratio"] = ratio_hint
        elif "横版" not in text and "竖版" not in text and "比例" not in text:
            parts.append("构图适合横版商店页 / KV，主体清晰，背景干净。")
            extras["layout"] = "landscape_kv"
        if size_hint:
            parts.append(f"输出清晰度偏好 {size_hint}。")
            extras["size"] = size_hint
        if mode == "image_to_image":
            parts.append("在参考图基础上微调，保留构图与人物位置，不要大幅改构图。")
            extras["refine"] = "keep_composition"
        bans = (
            "、".join(brand_pack.forbidden)
            if brand_pack and brand_pack.forbidden
            else _IMAGE_NEGATIVES
        )
        parts.append(f"避免：{bans}。")
        extras["negatives"] = "image"
    else:
        if "15" in text or "十五秒" in text:
            parts.append("时长约 15 秒，分镜清晰，镜头缓慢推进，节奏克制。")
            extras["duration"] = "15s"
        elif "秒" not in text and "时长" not in text:
            parts.append("时长约 5 秒，镜头缓慢推进，节奏克制。")
            extras["duration"] = "5s"
        if mode == "reference_to_video":
            parts.append(
                "综合多张参考图的角色外形、服装与场景气质生成连贯成片，"
                "主体一致性优先，运镜优雅，避免跳切崩人设。",
            )
            extras["r2v"] = "multimodal_refs"
        elif mode == "image_to_video":
            parts.append("严格承接首帧图气质与构图，环境轻微动态即可。")
            extras["i2v"] = "follow_first_frame"
        bans = (
            "、".join(brand_pack.forbidden)
            if brand_pack and brand_pack.forbidden
            else _VIDEO_NEGATIVES
        )
        parts.append(f"避免：{bans}。")
        extras["negatives"] = "video"

    compiled = "\n".join(parts)
    return CompiledPrompt(text=compiled, raw=raw or "", extras=extras)


def format_ark_error(exc: BaseException) -> str:
    """把方舟 / 媒体异常收成用户可读短句。"""
    msg = str(exc).strip() or exc.__class__.__name__
    lower = msg.lower()
    if "timeout" in lower or "超时" in msg:
        return "生成超时了，请稍后重试；视频任务通常需要 1–3 分钟。"
    if "401" in msg or "unauthorized" in lower or "api key" in lower:
        return "火山方舟鉴权失败，请到「设置」检查 API Key 是否有效并已启用。"
    if "429" in msg or "rate" in lower or "quota" in lower:
        return "方舟调用过于频繁或额度不足，请稍后再试。"
    if "ratio" in lower and "valid" in lower:
        return "图生视频参数冲突（比例需跟随首帧图），请重试或换一张参考图。"
    if "InvalidParameter" in msg or "400" in msg:
        return f"参数不被方舟接受：{msg[:180]}"
    if len(msg) > 220:
        return msg[:220] + "…"
    return msg

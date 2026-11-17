"""计费雏形：按本月生成量估算用量（为硬配额铺路）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, get_current_context
from app.core.db import get_db
from app.services.quota.usage import count_generated_media, current_year_month

router = APIRouter(prefix="/billing", tags=["计费"])

_PRICE_IMAGE_CENTS = 8
_PRICE_VIDEO_CENTS = 120


@router.get("/summary")
async def billing_summary(
    ctx: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """本月用量与粗估费用（非真实扣款）。"""
    images, videos = await count_generated_media(db, ctx.tenant_id)
    estimate_cents = images * _PRICE_IMAGE_CENTS + videos * _PRICE_VIDEO_CENTS
    return {
        "period": current_year_month(),
        "imagesThisMonth": images,
        "videosThisMonth": videos,
        "unitPrice": {
            "imageCents": _PRICE_IMAGE_CENTS,
            "videoCents": _PRICE_VIDEO_CENTS,
        },
        "estimateCents": estimate_cents,
        "currency": "CNY",
        "billingMode": "estimate_only",
        "note": "计费雏形：仅估算，不扣款；硬配额与套餐后续接入。",
    }

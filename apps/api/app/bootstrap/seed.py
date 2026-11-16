"""演示数据种子：与前端 mock 对齐，便于联调。"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.asset import Asset
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeBase, KnowledgeItem
from app.models.quota import QuotaUsage
from app.models.tenant import Membership, Tenant
from app.models.user import User
from app.models.workspace import Workspace

logger = logging.getLogger(__name__)

# 固定 ID，方便前端硬编码联调
TENANT_ID = "t_1"
USER_ID = "u_1"
WS_SPRING = "ws_spring"
WS_BRAND = "ws_brand"


async def seed_demo_data(session: AsyncSession) -> None:
    """若库为空则写入演示租户 / 用户 / 空间 / 对话等。"""
    exists = await session.scalar(select(func.count()).select_from(Tenant))
    if exists and exists > 0:
        logger.info("已有数据，跳过种子")
        return

    logger.info("写入演示种子数据…")

    tenant = Tenant(id=TENANT_ID, name="品牌星云")
    user = User(
        id=USER_ID,
        email="linqing@prism.demo",
        name="林清",
        hashed_password=hash_password("prism123"),
        avatar_text="林",
    )
    membership = Membership(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        role="owner",
    )

    workspaces = [
        Workspace(
            id=WS_SPRING,
            tenant_id=TENANT_ID,
            name="春季大促 2026",
            description="主视觉、种草短视频与知识库素材集中在此空间。",
            status="active",
        ),
        Workspace(
            id=WS_BRAND,
            tenant_id=TENANT_ID,
            name="品牌常青",
            description="VI 规范、历史主视觉与可复用分镜库。",
            status="evergreen",
        ),
    ]

    conv = Conversation(
        id="c_spring",
        tenant_id=TENANT_ID,
        workspace_id=WS_SPRING,
        title="春季主视觉 · 青橙光谱",
        kind="image",
    )
    messages = [
        Message(
            id="m1",
            conversation_id=conv.id,
            role="user",
            content="用品牌青石色和暖橙高光，做 3 张春季大促主视觉，横版，干净留白，适合电商首页。",
        ),
        Message(
            id="m2",
            conversation_id=conv.id,
            role="assistant",
            content="已结合「品牌常青」知识库中的主色规范，生成 3 个变体。可点选后继续改构图或出短视频。",
            tool_label="text_to_image · 完成",
            results_json='[{"id":"r1","label":"变体 A","tone":"a"},{"id":"r2","label":"变体 B","tone":"b"},{"id":"r3","label":"变体 C","tone":"c"}]',
        ),
    ]

    # 补充另外两条会话摘要
    extra_convs = [
        Conversation(
            id="c_teaser",
            tenant_id=TENANT_ID,
            workspace_id=WS_SPRING,
            title="种草短视频分镜",
            kind="video",
        ),
        Conversation(
            id="c_pack",
            tenant_id=TENANT_ID,
            workspace_id=WS_SPRING,
            title="包装静物三视图",
            kind="image",
        ),
    ]

    kb = KnowledgeBase(
        id="kb_brand",
        tenant_id=TENANT_ID,
        workspace_id=WS_SPRING,
        name="品牌视觉规范",
        description="VI、主色、禁用示例与历史主视觉。",
    )
    kb_items = [
        KnowledgeItem(
            id="ki_1",
            knowledge_base_id=kb.id,
            tenant_id=TENANT_ID,
            item_type="document",
            title="主色规范",
            content="主色为青石色 #0F6E6A，点缀暖橙 #E8A838，背景保持冷雾白留白，避免使用高饱和紫色。",
            tone="a",
        ),
        KnowledgeItem(
            id="ki_2",
            knowledge_base_id=kb.id,
            tenant_id=TENANT_ID,
            item_type="image",
            title="spring_hero_v3.png",
            content="春季主视觉历史版本，青石色与暖橙高光。",
            tone="a",
        ),
        KnowledgeItem(
            id="ki_3",
            knowledge_base_id=kb.id,
            tenant_id=TENANT_ID,
            item_type="image",
            title="kv_storefront.jpg",
            content="门店 KV，留白比例较大。",
            tone="b",
        ),
    ]

    kb2 = KnowledgeBase(
        id="kb_ads",
        tenant_id=TENANT_ID,
        workspace_id=WS_SPRING,
        name="投放历史素材",
        description="过往投放图与成片封面，支持图搜复用。",
    )

    assets = [
        Asset(
            id="a1",
            tenant_id=TENANT_ID,
            workspace_id=WS_SPRING,
            name="hero_01.png",
            kind="image",
            meta="对话生成 · 今天",
            storage_key="",
        ),
        Asset(
            id="a2",
            tenant_id=TENANT_ID,
            workspace_id=WS_SPRING,
            name="hero_02.png",
            kind="image",
            meta="对话生成 · 今天",
            storage_key="",
        ),
        Asset(
            id="a3",
            tenant_id=TENANT_ID,
            workspace_id=WS_SPRING,
            name="teaser.mp4",
            kind="video",
            meta="15s · 图生视频",
            storage_key="",
        ),
    ]

    from datetime import datetime

    ym = datetime.utcnow().strftime("%Y-%m")
    quota = QuotaUsage(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        year_month=ym,
        images_count=128,
        videos_count=14,
    )

    session.add_all(
        [
            tenant,
            user,
            membership,
            *workspaces,
            conv,
            *messages,
            *extra_convs,
            kb,
            kb2,
            *kb_items,
            *assets,
            quota,
        ],
    )
    await session.commit()
    logger.info("种子数据完成：账号 linqing@prism.demo / prism123")

"""知识库接口。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.models.knowledge import KnowledgeBase, KnowledgeItem
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
    KnowledgeHitOut,
    SearchImageRequest,
    SearchTextRequest,
)
from app.services.knowledge.ingest import ingest_text_document
from app.services.knowledge.search_image import search_image
from app.services.knowledge.search_text import search_text

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBaseOut]:
    """知识库列表。"""
    assert ctx.workspace_id
    rows = (
        await db.scalars(
            select(KnowledgeBase).where(
                KnowledgeBase.tenant_id == ctx.tenant_id,
                KnowledgeBase.workspace_id == ctx.workspace_id,
            ),
        )
    ).all()

    out: list[KnowledgeBaseOut] = []
    for kb in rows:
        doc_count = await db.scalar(
            select(func.count())
            .select_from(KnowledgeItem)
            .where(
                KnowledgeItem.knowledge_base_id == kb.id,
                KnowledgeItem.item_type == "document",
            ),
        )
        img_count = await db.scalar(
            select(func.count())
            .select_from(KnowledgeItem)
            .where(
                KnowledgeItem.knowledge_base_id == kb.id,
                KnowledgeItem.item_type == "image",
            ),
        )
        out.append(
            KnowledgeBaseOut(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                documentCount=int(doc_count or 0),
                imageCount=int(img_count or 0),
            ),
        )
    return out


@router.post("", response_model=KnowledgeBaseOut)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseOut:
    """新建知识库。"""
    import uuid

    assert ctx.workspace_id
    kb = KnowledgeBase(
        id=f"kb_{uuid.uuid4().hex[:10]}",
        tenant_id=ctx.tenant_id,
        workspace_id=ctx.workspace_id,
        name=body.name,
        description=body.description,
    )
    db.add(kb)
    await db.commit()
    return KnowledgeBaseOut(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        documentCount=0,
        imageCount=0,
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseOut:
    """知识库详情。"""
    kb = await _get_kb_or_404(db, ctx, kb_id)
    return KnowledgeBaseOut(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        documentCount=0,
        imageCount=0,
    )


@router.post("/{kb_id}/search", response_model=list[KnowledgeHitOut])
async def search_kb_text(
    kb_id: str,
    body: SearchTextRequest,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeHitOut]:
    """文本检索。"""
    await _get_kb_or_404(db, ctx, kb_id)
    return await search_text(
        db,
        tenant_id=ctx.tenant_id,
        knowledge_base_id=kb_id,
        query=body.query,
        top_k=body.top_k,
    )


@router.post("/{kb_id}/search/image", response_model=list[KnowledgeHitOut])
async def search_kb_image(
    kb_id: str,
    body: SearchImageRequest,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeHitOut]:
    """以图搜图（演示）。"""
    await _get_kb_or_404(db, ctx, kb_id)
    return await search_image(
        db,
        tenant_id=ctx.tenant_id,
        knowledge_base_id=kb_id,
        query_hint=body.query_hint,
        top_k=body.top_k,
    )


@router.post("/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    title: str,
    content: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """上传/写入文本文档条目。"""
    await _get_kb_or_404(db, ctx, kb_id)
    item = await ingest_text_document(
        db,
        tenant_id=ctx.tenant_id,
        knowledge_base_id=kb_id,
        title=title,
        content=content,
    )
    await db.commit()
    return {"id": item.id, "title": item.title}


async def _get_kb_or_404(
    db: AsyncSession,
    ctx: RequestContext,
    kb_id: str,
) -> KnowledgeBase:
    """校验知识库归属。"""
    kb = await db.get(KnowledgeBase, kb_id)
    if (
        not kb
        or kb.tenant_id != ctx.tenant_id
        or kb.workspace_id != ctx.workspace_id
    ):
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb

"""知识库接口：列表、入库、文本/图片检索。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestContext, require_workspace
from app.core.db import get_db
from app.core.storage import get_storage
from app.models.knowledge import KnowledgeBase, KnowledgeItem
from app.schemas.knowledge import (
    DocumentIngestRequest,
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
    KnowledgeHitOut,
    KnowledgeItemOut,
    SearchImageRequest,
    SearchTextRequest,
)
from app.services.knowledge.ingest import ingest_image, ingest_text_document
from app.services.knowledge.reembed import reembed_item
from app.services.knowledge.search_image import search_image
from app.services.knowledge.search_text import search_text

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])

_ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}


async def _counts(db: AsyncSession, kb_id: str) -> tuple[int, int]:
    doc_count = await db.scalar(
        select(func.count())
        .select_from(KnowledgeItem)
        .where(
            KnowledgeItem.knowledge_base_id == kb_id,
            KnowledgeItem.item_type == "document",
        ),
    )
    img_count = await db.scalar(
        select(func.count())
        .select_from(KnowledgeItem)
        .where(
            KnowledgeItem.knowledge_base_id == kb_id,
            KnowledgeItem.item_type == "image",
        ),
    )
    return int(doc_count or 0), int(img_count or 0)


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
        docs, imgs = await _counts(db, kb.id)
        out.append(
            KnowledgeBaseOut(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                documentCount=docs,
                imageCount=imgs,
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
    docs, imgs = await _counts(db, kb.id)
    return KnowledgeBaseOut(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        documentCount=docs,
        imageCount=imgs,
    )


@router.get("/{kb_id}/items", response_model=list[KnowledgeItemOut])
async def list_knowledge_items(
    kb_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeItemOut]:
    """列出知识库条目（最近入库优先）。"""
    await _get_kb_or_404(db, ctx, kb_id)
    rows = (
        await db.scalars(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.knowledge_base_id == kb_id,
                KnowledgeItem.tenant_id == ctx.tenant_id,
            )
            .order_by(KnowledgeItem.created_at.desc())
            .limit(100),
        )
    ).all()
    storage = get_storage()
    out: list[KnowledgeItemOut] = []
    for item in rows:
        url = storage.public_url(item.storage_key) if item.storage_key else None
        thumb = None
        if item.item_type == "image" and item.storage_key:
            thumb = storage.public_thumb_url(item.storage_key, mime_type="image/png")
        out.append(
            KnowledgeItemOut(
                id=item.id,
                title=item.title,
                itemType=item.item_type,
                summary=(item.content or "")[:120],
                url=url,
                thumbUrl=thumb or url,
                hasEmbedding=bool(item.embedding_json),
            ),
        )
    return out


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
    """以文搜图（JSON）。"""
    await _get_kb_or_404(db, ctx, kb_id)
    return await search_image(
        db,
        tenant_id=ctx.tenant_id,
        knowledge_base_id=kb_id,
        query_hint=body.query_hint,
        top_k=body.top_k,
    )


@router.post("/{kb_id}/search/by-image", response_model=list[KnowledgeHitOut])
async def search_kb_by_image_file(
    kb_id: str,
    file: UploadFile = File(...),
    query_hint: str | None = Form(default=None),
    top_k: int = Form(default=5),
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeHitOut]:
    """真·以图搜图：上传参考图做相似召回。"""
    await _get_kb_or_404(db, ctx, kb_id)
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPG / WEBP / GIF")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件")
    try:
        return await search_image(
            db,
            tenant_id=ctx.tenant_id,
            knowledge_base_id=kb_id,
            query_hint=query_hint,
            image_bytes=data,
            image_mime=content_type or "image/png",
            top_k=max(1, min(top_k, 50)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{kb_id}/items/{item_id}/reembed", response_model=KnowledgeItemOut)
async def reembed_knowledge_item(
    kb_id: str,
    item_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeItemOut:
    """对单条条目重新向量化。"""
    await _get_kb_or_404(db, ctx, kb_id)
    item = await db.get(KnowledgeItem, item_id)
    if (
        not item
        or item.knowledge_base_id != kb_id
        or item.tenant_id != ctx.tenant_id
    ):
        raise HTTPException(status_code=404, detail="条目不存在")
    try:
        item = await reembed_item(db, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    storage = get_storage()
    url = storage.public_url(item.storage_key) if item.storage_key else None
    thumb = (
        storage.public_thumb_url(item.storage_key, mime_type="image/png")
        if item.item_type == "image" and item.storage_key
        else None
    )
    return KnowledgeItemOut(
        id=item.id,
        title=item.title,
        itemType=item.item_type,
        summary=(item.content or "")[:120],
        url=url,
        thumbUrl=thumb or url,
        hasEmbedding=bool(item.embedding_json),
    )


@router.post("/{kb_id}/reembed-missing")
async def reembed_missing_items(
    kb_id: str,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """批量重试库内无向量条目（最多 20 条）。"""
    await _get_kb_or_404(db, ctx, kb_id)
    rows = (
        await db.scalars(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.knowledge_base_id == kb_id,
                KnowledgeItem.tenant_id == ctx.tenant_id,
                KnowledgeItem.embedding_json.is_(None),
            )
            .limit(20),
        )
    ).all()
    ok = 0
    failed: list[dict[str, str]] = []
    for item in rows:
        try:
            await reembed_item(db, item)
            ok += 1
        except ValueError as exc:
            failed.append({"id": item.id, "error": str(exc)})
    await db.commit()
    return {"attempted": len(rows), "ok": ok, "failed": failed}


@router.post("/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    body: DocumentIngestRequest,
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """写入文本文档条目。"""
    await _get_kb_or_404(db, ctx, kb_id)
    item = await ingest_text_document(
        db,
        tenant_id=ctx.tenant_id,
        knowledge_base_id=kb_id,
        title=body.title,
        content=body.content,
    )
    await db.commit()
    return {
        "id": item.id,
        "title": item.title,
        "hasEmbedding": bool(item.embedding_json),
    }


@router.post("/{kb_id}/images", response_model=KnowledgeItemOut)
async def upload_image(
    kb_id: str,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    caption: str = Form(default=""),
    ctx: RequestContext = Depends(require_workspace),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeItemOut:
    """上传图片入库（多模态向量）。"""
    kb = await _get_kb_or_404(db, ctx, kb_id)
    assert ctx.workspace_id
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPG / WEBP / GIF")
    data = await file.read()
    try:
        item = await ingest_image(
            db,
            tenant_id=ctx.tenant_id,
            workspace_id=ctx.workspace_id or kb.workspace_id,
            knowledge_base_id=kb_id,
            filename=file.filename or "upload.png",
            data=data,
            content_type=content_type or "image/png",
            title=title,
            caption=caption,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    storage = get_storage()
    url = storage.public_url(item.storage_key) if item.storage_key else None
    thumb = (
        storage.public_thumb_url(item.storage_key, mime_type=content_type or "image/png")
        if item.storage_key
        else None
    )
    return KnowledgeItemOut(
        id=item.id,
        title=item.title,
        itemType=item.item_type,
        summary=(item.content or "")[:120],
        url=url,
        thumbUrl=thumb or url,
        hasEmbedding=bool(item.embedding_json),
    )


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

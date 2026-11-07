from fastapi import APIRouter, Depends

from app.deps import admin_user
from app.models import KnowledgeChunk, KnowledgeDoc
from app.rag.embeddings import rebuild_index
from app.rag.retriever import hybrid_search
from app.result import BizError, Result
from app.schemas import Account, KnowledgeIn, SearchTestIn

router = APIRouter(prefix="/knowledge", tags=["知识库"])


def doc_dict(d: KnowledgeDoc) -> dict:
    return {"id": d.id, "title": d.title, "filename": d.filename,
            "chunk_count": d.chunk_count, "status": d.status,
            "size": len(d.content or ""),
            "created_at": d.created_at.isoformat()}


@router.get("/docs")
async def list_docs(_: Account = Depends(admin_user)):
    rows = await KnowledgeDoc.all().order_by("-id")
    return Result.success([doc_dict(d) for d in rows])


@router.get("/docs/{did}")
async def get_doc(did: int, _: Account = Depends(admin_user)):
    d = await KnowledgeDoc.get_or_none(id=did)
    if not d:
        raise BizError("文档不存在", 404)
    return Result.success({**doc_dict(d), "content": d.content})


@router.post("/docs")
async def create_doc(body: KnowledgeIn, _: Account = Depends(admin_user)):
    d = await KnowledgeDoc.create(title=body.title, filename=body.filename,
                                  content=body.content, status="indexing")
    info = await rebuild_index(d)
    return Result.success({**doc_dict(d), **info})


@router.put("/docs/{did}")
async def update_doc(did: int, body: KnowledgeIn, _: Account = Depends(admin_user)):
    d = await KnowledgeDoc.get_or_none(id=did)
    if not d:
        raise BizError("文档不存在", 404)
    d.title, d.filename, d.content, d.status = body.title, body.filename, body.content, "indexing"
    await d.save()
    info = await rebuild_index(d)
    return Result.success({**doc_dict(d), **info})


@router.delete("/docs/{did}")
async def delete_doc(did: int, _: Account = Depends(admin_user)):
    await KnowledgeChunk.filter(doc_id=did).delete()
    await KnowledgeDoc.filter(id=did).delete()
    return Result.success()


@router.get("/docs/{did}/chunks")
async def list_chunks(did: int, _: Account = Depends(admin_user)):
    rows = await KnowledgeChunk.filter(doc_id=did).order_by("idx")
    return Result.success([{"id": c.id, "idx": c.idx, "content": c.content,
                            "start": c.start_char, "end": c.end_char,
                            "has_vector": bool(c.embedding)} for c in rows])


@router.post("/docs/{did}/reindex")
async def reindex(did: int, _: Account = Depends(admin_user)):
    d = await KnowledgeDoc.get_or_none(id=did)
    if not d:
        raise BizError("文档不存在", 404)
    return Result.success(await rebuild_index(d))


@router.post("/search-test")
async def search_test(body: SearchTestIn, _: Account = Depends(admin_user)):
    if not body.query.strip():
        raise BizError("查询不能为空")
    return Result.success(await hybrid_search(body.query, body.top_k))

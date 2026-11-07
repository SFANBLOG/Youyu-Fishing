"""知识库索引：MySQL 存切片文本与位置，Milvus 存向量。

LangChain OpenAIEmbeddings 生成向量 → pymilvus 写入 Milvus 集合；
没有 embedding 模型 / 维度不匹配 / Milvus 不可用时，仍完成切片，检索层降级为纯 BM25。
"""
import asyncio
import logging

from app.config import settings
from app.infra.milvus_client import milvus_store
from app.llm.factory import embed, get_model
from app.models import KnowledgeChunk, KnowledgeDoc
from app.rag.chunker import split_text

logger = logging.getLogger("youyu.index")


async def rebuild_index(doc: KnowledgeDoc) -> dict:
    chunks = split_text(doc.content)
    model = await get_model("embedding")
    vectors = await embed([c["content"] for c in chunks], model) if model else []

    # 维度必须与 Milvus 集合一致，不一致就不写向量（避免 insert 报错）
    expected = settings.EMBED_DIM
    mismatch = bool(vectors) and any(len(v) != expected for v in vectors)
    usable = [] if mismatch else vectors

    await KnowledgeChunk.filter(doc_id=doc.id).delete()
    rows: list[dict] = []
    for i, c in enumerate(chunks):
        chunk = await KnowledgeChunk.create(
            doc_id=doc.id, idx=c["idx"], content=c["content"],
            start_char=c["start"], end_char=c["end"], embedding=[],  # 向量统一放 Milvus
        )
        if i < len(usable) and usable[i]:
            rows.append({"id": chunk.id, "idx": c["idx"],
                         "content": c["content"], "vector": usable[i]})

    vector_count = 0
    if rows:
        vector_count = await asyncio.to_thread(milvus_store.upsert_doc, doc.id, rows)
    else:
        await asyncio.to_thread(milvus_store.delete_doc, doc.id)

    doc.chunk_count = len(chunks)
    doc.status = "ready"
    await doc.save()
    if mismatch:
        logger.warning("embedding 维度 %s != EMBED_DIM %s，本次不写 Milvus",
                       len(vectors[0]) if vectors else "?", expected)

    return {
        "chunk_count": len(chunks),
        "vector_count": vector_count,
        "degraded": vector_count != len(chunks),
        "engine": model.model_name if model else "keyword-only",
        "backend": "milvus" if vector_count else "bm25-only",
        "dimension_mismatch": mismatch,
    }

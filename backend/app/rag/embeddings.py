"""知识库索引：有 embedding 模型就写向量，没有就保持空向量并标记降级。"""
from app.llm.factory import embed, get_model
from app.models import KnowledgeChunk, KnowledgeDoc
from app.rag.chunker import split_text


async def rebuild_index(doc: KnowledgeDoc) -> dict:
    await KnowledgeChunk.filter(doc_id=doc.id).delete()
    chunks = split_text(doc.content)
    model = await get_model("embedding")
    vectors = await embed([c["content"] for c in chunks], model) if model else []

    for i, c in enumerate(chunks):
        vector = vectors[i] if i < len(vectors) else []
        await KnowledgeChunk.create(doc_id=doc.id, idx=c["idx"], content=c["content"],
                                    start_char=c["start"], end_char=c["end"],
                                    embedding=vector)
    doc.chunk_count = len(chunks)
    doc.status = "ready"
    await doc.save()
    return {
        "chunk_count": len(chunks),
        "vector_count": len(vectors),
        "degraded": len(vectors) != len(chunks),
        "engine": model.model_name if model else "keyword-only",
    }

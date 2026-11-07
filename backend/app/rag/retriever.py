"""混合检索：Milvus(HNSW/COSINE) 向量召回 + BM25 关键词召回 → RRF 名次融合。

- 切片文本与金标仍在 MySQL，用于 BM25 与引用回链
- 向量由 LangChain Embeddings 生成、存 Milvus，不在 MySQL 里存数组
- Milvus / embedding 任一不可用 → 自动降级纯 BM25，并标记 degraded
"""
import asyncio
import math
import re
from collections import Counter

from app.config import settings
from app.infra.milvus_client import milvus_store
from app.llm.factory import embed, get_model
from app.models import KnowledgeChunk


def tokenize(text: str) -> list[str]:
    s = re.sub(r"\s+", "", text.lower())
    chars = list(s)
    bigrams = [s[i:i + 2] for i in range(len(s) - 1)]
    return chars + bigrams


def bm25_scores(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    q_terms = tokenize(query)
    if not q_terms or not docs:
        return [0.0] * len(docs)
    doc_tokens = [tokenize(d) for d in docs]
    lens = [len(t) for t in doc_tokens] or [1]
    avgdl = sum(lens) / len(lens) or 1
    df = Counter()
    for toks in doc_tokens:
        for t in set(toks):
            df[t] += 1
    n = len(docs)
    scores = []
    for toks, length in zip(doc_tokens, lens):
        tf = Counter(toks)
        score = 0.0
        for term, qtf in Counter(q_terms).items():
            if term not in tf or not df[term]:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            denom = tf[term] + k1 * (1 - b + b * length / avgdl)
            score += qtf * idf * tf[term] * (k1 + 1) / denom
        scores.append(score)
    return scores


def rrf(*rankings: list[int], k: int = 60, weights: list[float] | None = None) -> dict[int, float]:
    weights = weights or [1.0] * len(rankings)
    fused: dict[int, float] = {}
    for ranking, w in zip(rankings, weights):
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + w / (k + rank + 1)
    return fused


async def hybrid_search(query: str, top_k: int = 5) -> dict:
    backend = "milvus" if milvus_store.enabled else "off"
    rows = await KnowledgeChunk.all().prefetch_related("doc")
    if not rows:
        return {"hits": [], "degraded": True, "engine": "empty-kb",
                "vector_count": 0, "total_chunks": 0, "backend": backend}

    by_id = {r.id: r for r in rows}
    index_of = {r.id: i for i, r in enumerate(rows)}
    texts = [r.content for r in rows]
    kw_scores = bm25_scores(query, texts)
    kw_rank = [i for i, _ in sorted(enumerate(kw_scores), key=lambda x: -x[1]) if kw_scores[i] > 0]

    model = await get_model("embedding")
    q_vec = await embed([query], model) if model else []
    vec_hits: list[dict] = []
    if q_vec and len(q_vec[0]) == settings.EMBED_DIM:
        vec_hits = await asyncio.to_thread(milvus_store.search, q_vec[0], settings.MILVUS_TOPK)

    vec_score_by_idx: dict[int, float] = {}
    vec_rank: list[int] = []
    for h in vec_hits:
        idx = index_of.get(int(h["id"]))
        if idx is None:
            continue
        vec_score_by_idx[idx] = h["score"]
        vec_rank.append(idx)

    degraded = not vec_rank
    if degraded:
        fused = {idx: 1 / (60 + rank + 1) for rank, idx in enumerate(kw_rank)}
        engine = "bm25-only (Milvus/embedding 未命中)"
    else:
        fused = rrf(vec_rank, kw_rank, weights=[0.6, 0.4])
        engine = "milvus(HNSW/COSINE) + bm25 + RRF"

    hits = []
    for idx, score in sorted(fused.items(), key=lambda x: -x[1])[:top_k]:
        r = rows[idx]
        hits.append({
            "chunk_id": r.id,
            "doc_id": r.doc_id,
            "doc_title": r.doc.title if r.doc else "",
            "idx": r.idx,
            "content": r.content,
            "score": round(float(score), 6),
            "vector_score": round(vec_score_by_idx.get(idx, 0.0), 4),
            "keyword_score": round(kw_scores[idx], 4),
        })
    return {"hits": hits, "degraded": degraded, "engine": engine,
            "vector_count": len(vec_hits), "total_chunks": len(rows),
            "backend": backend}

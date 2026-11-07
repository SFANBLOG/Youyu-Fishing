"""混合检索：向量余弦 + BM25 → RRF 名次融合。

零外部依赖：中文用「单字 + 相邻二元组」做词项，向量用 numpy 余弦。
没有 embedding 模型 / 没有向量时自动降级为纯关键词，并在结果里标记 degraded。
"""
import math
import re
from collections import Counter

import numpy as np

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


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


def rrf(*rankings: list[int], k: int = 60, weights: list[float] | None = None) -> dict[int, float]:
    """rankings: 每路按优劣排序的候选下标列表。"""
    weights = weights or [1.0] * len(rankings)
    fused: dict[int, float] = {}
    for ranking, w in zip(rankings, weights):
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + w / (k + rank + 1)
    return fused


async def hybrid_search(query: str, top_k: int = 5) -> dict:
    rows = await KnowledgeChunk.all().prefetch_related("doc")
    if not rows:
        return {"hits": [], "degraded": True, "engine": "empty-kb", "vector_count": 0}

    texts = [r.content for r in rows]
    kw_scores = bm25_scores(query, texts)
    kw_rank = [i for i, _ in sorted(enumerate(kw_scores), key=lambda x: -x[1]) if kw_scores[i] > 0]

    model = await get_model("embedding")
    q_vec = await embed([query], model) if model else []
    vec_scores = [cosine(q_vec[0] if q_vec else [], r.embedding or []) for r in rows]
    vec_rank = [i for i, _ in sorted(enumerate(vec_scores), key=lambda x: -x[1]) if vec_scores[i] > 0]

    vector_count = sum(1 for r in rows if r.embedding)
    degraded = not vec_rank
    if degraded:
        fused = {idx: 1 / (60 + rank + 1) for rank, idx in enumerate(kw_rank)}
        engine = "bm25-only (no embedding)"
    else:
        fused = rrf(vec_rank, kw_rank, weights=[0.6, 0.4])
        engine = "vector + bm25 + RRF"

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
            "vector_score": round(vec_scores[idx], 4),
            "keyword_score": round(kw_scores[idx], 4),
        })
    return {"hits": hits, "degraded": degraded, "engine": engine,
            "vector_count": vector_count, "total_chunks": len(rows)}

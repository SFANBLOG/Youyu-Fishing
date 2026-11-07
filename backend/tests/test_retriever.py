from app.rag.retriever import bm25_scores, cosine, rrf, tokenize


def test_bm25_relevant_first():
    docs = [
        "竞业限制条款适用于高级技术人员，期限不得超过二年",
        "今天天气不错，适合去水库钓鱼",
        "经济补偿金按劳动者工作年限计算",
    ]
    scores = bm25_scores("竞业限制 期限", docs)
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]
    assert scores[1] >= 0


def test_cosine():
    assert cosine([1, 0], [1, 0]) > 0.99
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([], [1, 2]) == 0
    assert cosine([1, 2], [1]) == 0  # 维度不一致


def test_rrf_fusion():
    vector_rank = [2, 0, 1]
    keyword_rank = [0, 2, 3]
    fused = rrf(vector_rank, keyword_rank)
    assert 0 in fused and 2 in fused
    # 两路都靠前的 0 / 2 应优于只在单路出现的 1 / 3
    assert fused[0] > fused[1]
    assert fused[2] > fused[3]


def test_tokenize_chinese():
    tokens = tokenize("高血糖 饮食")
    assert "高" in tokens
    assert "高血" in tokens

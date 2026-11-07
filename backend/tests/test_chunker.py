from app.rag.chunker import split_text


def test_overlap_and_order():
    text = "选竿要看调性。" * 120
    chunks = split_text(text, chunk_size=300, overlap=60)
    assert len(chunks) > 3
    assert [c["idx"] for c in chunks] == list(range(len(chunks)))
    assert all(c["content"] for c in chunks)
    assert all(c["start"] < c["end"] for c in chunks)
    # 相邻块有重叠区间
    assert any(a["end"] > b["start"] for a, b in zip(chunks, chunks[1:]))


def test_empty_and_short():
    assert split_text("") == []
    assert split_text("   ") == []
    one = split_text("新手优先 4.5 米 28 调", chunk_size=300, overlap=60)
    assert len(one) == 1
    assert one[0]["content"] == "新手优先 4.5 米 28 调"


def test_invalid_params():
    try:
        split_text("x", chunk_size=50, overlap=50)
        assert False, "overlap >= chunk_size 应抛错"
    except ValueError:
        pass

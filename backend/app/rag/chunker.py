"""文档切片：300 字窗口 + 60 字重叠，优先在句末断开。"""
import re

from app.config import settings

_SENT_END = re.compile(r"[。！？!?；;\n]")


def split_text(text: str, chunk_size: int | None = None,
               overlap: int | None = None) -> list[dict]:
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    text = re.sub(r"\r\n?", "\n", (text or "")).strip()
    n = len(text)
    chunks: list[dict] = []
    start = 0
    idx = 0
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            window = text[start:end]
            search_from = max(chunk_size - overlap - 80, 1)
            cut = None
            for m in _SENT_END.finditer(window, search_from):
                cut = m.end()
            if cut and cut >= chunk_size * 0.5:
                end = start + cut

        piece = text[start:end]
        if piece.strip():
            lead = len(piece) - len(piece.lstrip())
            chunks.append({
                "idx": idx,
                "content": piece.strip(),
                "start": start + lead,
                "end": end,
            })
            idx += 1
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks

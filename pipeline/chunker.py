from typing import List, Tuple

Page = Tuple[int, str]
Chunk = Tuple[str, int, int]  # (text, page_start, page_end)

def chunk_pages(pages: List[Page], max_chars: int = 6000, overlap: int = 400) -> List[Chunk]:
    """Greedy page-concatenation chunker with char budget and soft overlap."""
    if max_chars <= 1000:
        raise ValueError("max_chars too small; recommend >= 3000")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be >=0 and < max_chars")

    chunks: List[Chunk] = []
    buf, start_p, end_p = [], None, None
    size = 0

    for pnum, text in pages:
        part = f"\n[p.{pnum}]\n{text}\n"
        part_len = len(part)
        if not buf:
            start_p = pnum
        if size + part_len > max_chars and buf:
            joined = "".join(buf)
            chunks.append((joined, start_p, end_p or start_p))
            tail = joined[-overlap:] if overlap else ""
            buf, size = ([tail] if tail else []), len(tail)
            start_p = pnum if not tail else start_p
        buf.append(part)
        size += part_len
        end_p = pnum

    if buf:
        joined = "".join(buf)
        chunks.append((joined, start_p or 1, end_p or (start_p or 1)))

    return chunks

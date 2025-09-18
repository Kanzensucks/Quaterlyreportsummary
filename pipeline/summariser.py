"""
pipeline/summariser.py
----------------------
Loads prompts and summarises chunked text via Ollama, returning bullet lines.
Parser is robust to '-', '•', '*', '–', and numbered lists. Falls back to
sentence extraction if the model ignores the requested bullet format.
"""

from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Tuple
import re

from .ollama_client import OllamaClient


# ---------- Prompt loading ----------

def load_prompt(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Prompt file not found: {p.resolve()}")
    return p.read_text(encoding="utf-8")


def _format_prompt(template: str, text: str, start_page: int, end_page: int) -> str:
    return (
        template
        .replace("{{TEXT}}", text)
        .replace("{{START_PAGE}}", str(start_page))
        .replace("{{END_PAGE}}", str(end_page))
    )


# ---------- Bullet parsing ----------

_BULLET_LINE = re.compile(
    r"""^\s*(?:[-–•*]|\d{1,3}[.)])\s+(?P<pt>.+?)\s*$""",
    re.IGNORECASE,
)

def _extract_bullets(raw: str) -> List[str]:
    """
    Extract bullet-like lines from model output.
    Accepts: -, –, •, *, '1.' '2)' etc. Trims trailing whitespace.
    """
    lines = raw.splitlines()
    out: List[str] = []
    for ln in lines:
        m = _BULLET_LINE.match(ln)
        if m:
            pt = m.group("pt").strip()
            # collapse inner spaces
            pt = re.sub(r"\s+", " ", pt)
            if pt:
                out.append(f"- {pt}")
    return out


# ---------- Fallback sentence picker ----------

_SENTENCE = re.compile(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s")

def _top_sentences(text: str, k: int = 6) -> List[str]:
    """
    Extremely light fallback: take up to k reasonably short sentences that look
    decision-useful (contain %, pp, $ or common KPI words).
    """
    candidates = re.split(_SENTENCE, text)
    scored: List[Tuple[float, str]] = []
    for s in candidates:
        s = s.strip()
        if not s:
            continue
        tokens = s.lower()
        score = 0.0
        if re.search(r"\d%\b|\bpp\b|%\b", s): score += 3
        if re.search(r"\$\s*\d", s): score += 2
        if any(w in tokens for w in ("yoy", "qoq", "guidance", "revenue", "retention", "market share", "pricing", "margin")):
            score += 2
        score += min(len(re.findall(r"\d", s)), 5) * 0.3
        scored.append((score, s))
    scored.sort(key=lambda x: x[1])  # stable for similar scores
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[str] = []
    for _, s in scored[:k]:
        s = re.sub(r"\s+", " ", s)
        out.append(f"- {s}")
    return out


# ---------- Core summarisation ----------

def summarise_chunks(
    client: OllamaClient,
    model: str,
    prompt_template: str,
    chunks: Iterable[Tuple[str, int, int]],
    temperature: float = 0.1,
    verbose: bool = False,
    parse_mode: str = "bullets",
) -> List[str]:
    """
    chunks: iterable of (chunk_text, start_page, end_page)
    Returns list of bullet lines.
    """
    options = {"temperature": float(temperature)}
    bullets: List[str] = []

    for idx, (chunk_text, start_page, end_page) in enumerate(chunks, start=1):
        text_in = (chunk_text or "").strip()
        if not text_in:
            if verbose:
                print(f"[summariser] Chunk {idx} is empty; skipping.")
            continue

        prompt = _format_prompt(prompt_template, text_in, start_page, end_page)

        try:
            raw = client.generate(model=model, prompt=prompt, options=options) or ""
        except Exception as e:
            if verbose:
                print(f"[summariser] Error on chunk {idx}: {e}")
            raw = ""

        if verbose:
            print(f"[summariser] Chunk {idx} raw length: {len(raw)}")

        pts = _extract_bullets(raw)
        if not pts:
            if verbose:
                print(f"[summariser] Chunk {idx} yielded 0 bullets; using fallback sentences.")
            pts = _top_sentences(text_in, k=6)

        # Ensure page tag at end if missing
        tag = f" [p.{start_page if start_page == end_page else f'{start_page}-{end_page}'}]"
        def _ensure_tag(s: str) -> str:
            return s if re.search(r"\[p\.\d", s) else (s.rstrip(".") + tag)

        pts = [_ensure_tag(p) for p in pts]
        bullets.extend(pts)

        if verbose:
            print(f"[summariser] Chunk {idx}: +{len(pts)} bullet(s)")

    return bullets

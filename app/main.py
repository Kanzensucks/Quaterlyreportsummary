import argparse
from glob import glob
from datetime import datetime
from pathlib import Path
import hashlib
import re
import sys
from typing import Any

from pipeline.pdf_reader import extract_pages
from pipeline.chunker import chunk_pages
from pipeline.ollama_client import OllamaClient
from pipeline.summariser import load_prompt, summarise_chunks

from .config import (
    OLLAMA_HOST,
    MODEL_DEFAULT,
    MAX_CHARS_DEFAULT,
    OVERLAP_DEFAULT,
    TEMPERATURE_DEFAULT,
    TIMEOUT_DEFAULT,
    PROMPT_PATH,
)


# ---------------------------
# Helpers
# ---------------------------

def ensure_pdf(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    if p.suffix.lower() != ".pdf":
        raise ValueError("Input must be a .pdf file")
    return str(p)

def ensure_positive_int(name: str, val: int, min_val: int = 1) -> int:
    try:
        v = int(val)
    except Exception:
        raise ValueError(f"{name} must be an integer")
    if v < min_val:
        raise ValueError(f"{name} must be >= {min_val}")
    return v

def find_latest_pdf() -> str:
    pdfs = sorted(
        glob("reports/*.pdf"),
        key=lambda p: Path(p).stat().st_mtime if Path(p).exists() else 0,
        reverse=True,
    )
    if not pdfs:
        raise FileNotFoundError("No PDF found in ./reports.")
    return pdfs[0]

def _build_titles(pdf_path: Path, pages: list[Any]) -> str:
    company = pdf_path.stem
    company = re.sub(r"[^\w\-]+", "_", company).strip("_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    points_base = f"{company}_POINTS_{ts}"
    return points_base


# ---------------------------
# Main runner
# ---------------------------

def run():
    ap = argparse.ArgumentParser(description="Summarise brand health PDF with Ollama")
    ap.add_argument("--pdf", required=False, help="Path to input PDF (defaults to latest in ./reports if omitted)")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--max-chars", type=int, default=MAX_CHARS_DEFAULT)
    ap.add_argument("--overlap", type=int, default=OVERLAP_DEFAULT)
    ap.add_argument("--temperature", type=float, default=TEMPERATURE_DEFAULT)
    ap.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--show-chunks", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Resolve PDF
    pdf_path_str = args.pdf or find_latest_pdf()
    pdf_path_str = ensure_pdf(pdf_path_str)
    pdf_path = Path(pdf_path_str)

    # Validate numbers
    max_chars = ensure_positive_int("max-chars", args.max_chars, 1000)
    overlap   = ensure_positive_int("overlap", args.overlap, 0)

    # Output dirs
    points_outdir = Path("points_output"); points_outdir.mkdir(parents=True, exist_ok=True)

    # Client
    client = OllamaClient(host=OLLAMA_HOST, timeout=args.timeout)

    # Extract pages
    print("\n=== Extracting PDF Pages ===")
    pages = extract_pages(pdf_path)
    print(f"Pages extracted: {len(pages)}")

    # Chunk
    chunks = chunk_pages(pages, max_chars=max_chars, overlap=overlap)
    print(f"Chunks created: {len(chunks)} (max_chars={max_chars}, overlap={overlap})")

    if args.show_chunks or args.dry_run:
        for i, (_, a, b) in enumerate(chunks, start=1):
            rng = f"{a}-{b}" if a != b else f"{a}"
            print(f"  - Chunk {i}: pages {rng}")
        if args.dry_run:
            print("Dry run complete. No generation performed.")
            return

    # Smart file names
    points_base = _build_titles(pdf_path, pages)

    # ── Points summarisation ──
    print("\n=== Summarising Points ===")
    prompt_points = load_prompt("prompts/points_prompt.txt")
    pieces = summarise_chunks(
        client=client,
        model=args.model,
        prompt_template=prompt_points,
        chunks=chunks,
        temperature=args.temperature,
        verbose=args.verbose,
        parse_mode="bullets",
    )
    points_text = "\n".join(pieces) + ("\n" if pieces else "")
    points_path = points_outdir / f"{points_base}.txt"
    points_path.write_text(points_text, encoding="utf-8")
    print(f"Saved points summary: {points_path.resolve()}")

    # ── Ranking step ──
    print("\n=== Ranking Points (Value Only) ===")
    try:
        from pipeline.ranker import rank_points
        rank_points()
    except Exception as e:
        print(f"Warning: ranking step failed ({e}).")

    print("\nAll done.")


if __name__ == "__main__":
    run()

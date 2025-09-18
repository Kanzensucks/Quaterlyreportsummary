"""
pipeline/ranker.py
-------------------
Ranks summarised points based only on Value score.
"""

import re
from pathlib import Path
from datetime import datetime


# --- Value scoring heuristic ---
def score_value(point: str) -> float:
    """Assign a value score based on presence of numbers, %, KPIs, etc."""
    score = 0.0
    text = point.lower()

    # Numeric signals
    nums = re.findall(r"\d+", point)
    score += min(len(nums), 5) * 5  # up to +25

    # Percentages and pp
    score += 10 * len(re.findall(r"\d+%|\+\d+pp|-\d+pp", point))

    # Currency ($, m, b)
    if re.search(r"\$\d+", point):
        score += 15

    # KPI terms
    kpis = ["revenue", "market share", "retention", "awareness", "guidance",
            "customers", "growth", "qoq", "yoy"]
    score += 5 * sum(1 for k in kpis if k in text)

    return round(score, 1)


# --- Main ranking function ---
def rank_points():
    points_dir = Path("points_output")
    out_dir = Path("ranker_output")
    out_dir.mkdir(parents=True, exist_ok=True)

    latest_file = max(points_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)
    raw = latest_file.read_text(encoding="utf-8").splitlines()

    # Collect non-empty points
    points = [ln.strip() for ln in raw if ln.strip()]
    scored = [(p, score_value(p)) for p in points]

    # Sort by Value only
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"Ranked_Points_{ts}.txt"

    with out_path.open("w", encoding="utf-8") as f:
        f.write("Ranked Points (Value Only)\n")
        f.write("===================================\n\n")
        f.write("Rank  Value  Point\n")
        f.write("-----------------------------------\n")
        for i, (pt, val) in enumerate(ranked, start=1):
            f.write(f"{i:>3}   {val:>5}  {pt}\n")

    print(f"Ranked points saved to: {out_path}")

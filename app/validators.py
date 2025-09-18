import os

def ensure_pdf(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not path.lower().endswith(".pdf"):
        raise ValueError("Input must be a .pdf file")
    return path

def ensure_positive_int(name: str, val: int, min_val: int = 1) -> int:
    if int(val) < min_val:
        raise ValueError(f"{name} must be >= {min_val}")
    return int(val)

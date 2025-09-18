from typing import List, Tuple
from pypdf import PdfReader

def extract_pages(pdf_path: str) -> List[Tuple[int, str]]:
    """Return list of (page_number, text). Raises FileNotFoundError/ValueError.
    Cleans control chars and collapses whitespace.
    """
    try:
        reader = PdfReader(pdf_path)
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}")

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        cleaned = " ".join(txt.split())
        pages.append((i, cleaned))
    if not pages:
        raise ValueError("PDF has no extractable text.")
    return pages

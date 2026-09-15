"""
DOCX Extraction Service — Phase 10
Extracts text from .docx files using python-docx.
Returns the same page-list format as pdf_service for pipeline compatibility.

Note: DOCX files do not have true page boundaries; we simulate pages
by grouping paragraphs (every ~TXT_LINES_PER_PAGE paragraphs = 1 page).
"""

import logging
from typing import List, Dict, Optional
from io import BytesIO

logger = logging.getLogger("lexora.docx_service")


def _has_docx_support() -> bool:
    try:
        import docx  # noqa: F401
        return True
    except ImportError:
        return False


def extract_text_from_docx(file_path: str) -> List[Dict]:
    """
    Extract text from a DOCX file, returning a list of page dicts
    compatible with pdf_service output format.

    Each dict:
      {
        "page_number": int,
        "text": str,
        "word_count": int,
        "has_text": bool,
      }
    """
    if not _has_docx_support():
        raise ImportError(
            "python-docx is not installed. Run: pip install python-docx"
        )

    import docx

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        raise ValueError(f"Could not open DOCX file: {e}") from e

    # Group paragraphs into simulated pages
    PARAS_PER_PAGE = 30
    pages = []
    page_number = 1
    current_paragraphs = []

    all_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    for i, para_text in enumerate(all_paragraphs):
        current_paragraphs.append(para_text)

        if len(current_paragraphs) >= PARAS_PER_PAGE or i == len(all_paragraphs) - 1:
            combined = "\n".join(current_paragraphs)
            word_count = len(combined.split())
            pages.append({
                "page_number": page_number,
                "text": combined,
                "word_count": word_count,
                "has_text": word_count > 0,
            })
            page_number += 1
            current_paragraphs = []

    if not pages:
        # Document has no extractable paragraphs
        pages.append({
            "page_number": 1,
            "text": "",
            "word_count": 0,
            "has_text": False,
        })

    logger.info("DOCX extraction complete: %d simulated pages", len(pages))
    return pages


def extract_text_from_docx_bytes(file_bytes: bytes) -> List[Dict]:
    """
    Extract from raw bytes (no temp file required).
    """
    if not _has_docx_support():
        raise ImportError("python-docx is not installed. Run: pip install python-docx")

    import docx

    try:
        doc = docx.Document(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Could not parse DOCX bytes: {e}") from e

    PARAS_PER_PAGE = 30
    pages = []
    page_number = 1
    current_paragraphs = []
    all_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    for i, para_text in enumerate(all_paragraphs):
        current_paragraphs.append(para_text)
        if len(current_paragraphs) >= PARAS_PER_PAGE or i == len(all_paragraphs) - 1:
            combined = "\n".join(current_paragraphs)
            word_count = len(combined.split())
            pages.append({
                "page_number": page_number,
                "text": combined,
                "word_count": word_count,
                "has_text": word_count > 0,
            })
            page_number += 1
            current_paragraphs = []

    if not pages:
        pages.append({"page_number": 1, "text": "", "word_count": 0, "has_text": False})

    return pages

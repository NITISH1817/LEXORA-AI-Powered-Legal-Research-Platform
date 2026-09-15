"""
TXT Extraction Service — Phase 10
Extracts text from plain .txt files.
Simulates page boundaries (every TXT_LINES_PER_PAGE lines = 1 page)
so downstream pipeline stages see consistent page-level data.
"""

import logging
from typing import List, Dict

from backend.config import settings

logger = logging.getLogger("lexora.txt_service")


def extract_text_from_txt(file_path: str) -> List[Dict]:
    """
    Read a TXT file and split into simulated pages.

    Each dict:
      {
        "page_number": int,
        "text": str,
        "word_count": int,
        "has_text": bool,
      }
    """
    lines_per_page = settings.TXT_LINES_PER_PAGE

    try:
        # Try UTF-8 first, fall back to latin-1 to handle legacy legal documents
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                all_lines = f.readlines()
    except OSError as e:
        raise ValueError(f"Could not read TXT file: {e}") from e

    return _lines_to_pages(all_lines, lines_per_page)


def extract_text_from_txt_bytes(file_bytes: bytes) -> List[Dict]:
    """
    Parse raw bytes directly (no temp file required).
    """
    lines_per_page = settings.TXT_LINES_PER_PAGE

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    all_lines = text.splitlines(keepends=True)
    return _lines_to_pages(all_lines, lines_per_page)


def _lines_to_pages(all_lines: List[str], lines_per_page: int) -> List[Dict]:
    """Group lines into simulated pages."""
    pages = []
    page_number = 1
    current_lines: List[str] = []

    for i, line in enumerate(all_lines):
        current_lines.append(line)
        if len(current_lines) >= lines_per_page or i == len(all_lines) - 1:
            combined = "".join(current_lines).strip()
            word_count = len(combined.split()) if combined else 0
            pages.append({
                "page_number": page_number,
                "text": combined,
                "word_count": word_count,
                "has_text": word_count > 0,
            })
            page_number += 1
            current_lines = []

    if not pages:
        pages.append({"page_number": 1, "text": "", "word_count": 0, "has_text": False})

    logger.info("TXT extraction complete: %d simulated pages", len(pages))
    return pages

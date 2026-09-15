import fitz  # PyMuPDF
import re
import nltk
import logging
from typing import List, Dict, Generator

logger = logging.getLogger("lexora.pdf_service")

# Ensure punkt is available
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    try:
        nltk.download("punkt_tab", quiet=True)
    except Exception:
        pass


def clean_text(text: str) -> str:
    """Removes excessive whitespace and standardizes text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Phase 10: Page-level extraction (new, backward-compatible)
# ---------------------------------------------------------------------------

def extract_text_with_pages(file_path: str) -> List[Dict]:
    """
    Extract text page-by-page from a PDF.
    Returns a list of dicts compatible with docx_service and txt_service output.

    Each dict:
      {
        "page_number": int,
        "text": str,
        "word_count": int,
        "has_text": bool,   # False for scanned/image-only pages
      }

    Memory efficiency: pages are processed one at a time via generator.
    """
    results = []
    for page_data in _stream_pages(file_path):
        results.append(page_data)
    return results


def _stream_pages(file_path: str) -> Generator[Dict, None, None]:
    """
    Generator: yields one page dict at a time.
    Avoids loading the entire document into memory.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Could not open PDF: {e}") from e

    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            raw_text = page.get_text("text")
            cleaned = clean_text(raw_text)
            word_count = len(cleaned.split()) if cleaned else 0

            yield {
                "page_number": page_num + 1,
                "text": cleaned,
                "word_count": word_count,
                "has_text": word_count > 5,  # threshold: >5 words = has extractable text
            }
    finally:
        doc.close()


def detect_ocr_required(pages: List[Dict], threshold: float = 0.8) -> bool:
    """
    Detect if a PDF appears to be scanned (image-only) and requires OCR.

    Returns True if >= threshold fraction of pages have no extractable text.
    Does NOT silently create an empty index — callers must handle OCR_REQUIRED status.
    """
    if not pages:
        return False
    empty_pages = sum(1 for p in pages if not p.get("has_text", True))
    ratio = empty_pages / len(pages)
    if ratio >= threshold:
        logger.warning(
            "OCR required: %d/%d pages have no extractable text (%.0f%%)",
            empty_pages, len(pages), ratio * 100
        )
        return True
    return False


# ---------------------------------------------------------------------------
# Existing Phase 1-9 functions — preserved unchanged for backward compatibility
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """Extracts text page by page from a PDF. (Phase 1-9 compatible)"""
    doc = fitz.open(file_path)
    pages_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        cleaned_text = clean_text(text)

        if cleaned_text:
            pages_text.append({
                "page_number": page_num + 1,
                "text": cleaned_text
            })

    return pages_text


def chunk_text(pages: List[Dict], max_words: int = 400, overlap_sentences: int = 2) -> List[Dict]:
    """
    Structural Semantic Chunking:
    Chunks text by sentences to preserve legal context boundaries.
    (Phase 1-9 compatible — preserved unchanged)
    """
    chunks = []

    for page in pages:
        text = page["text"]
        try:
            sentences = nltk.sent_tokenize(text)
        except Exception:
            sentences = [s.strip() for s in text.split(".") if s.strip()]

        current_chunk = []
        current_word_count = 0

        for i, sentence in enumerate(sentences):
            sentence_words = len(sentence.split())

            # If a single sentence is huge, we have to just add it
            if current_word_count + sentence_words > max_words and current_chunk:
                # Save current chunk
                chunk_text_joined = " ".join(current_chunk)
                chunks.append({
                    "page_number": page["page_number"],
                    "text": chunk_text_joined
                })

                # Start new chunk with overlap
                overlap = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
                current_chunk = overlap + [sentence]
                current_word_count = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words

        # Add remaining
        if current_chunk:
            chunk_text_joined = " ".join(current_chunk)
            chunks.append({
                "page_number": page["page_number"],
                "text": chunk_text_joined
            })

    return chunks

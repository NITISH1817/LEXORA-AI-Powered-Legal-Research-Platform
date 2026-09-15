"""
Legal-Aware Chunking Service — Phase 10
Replaces naive fixed-size chunking with section-aware legal chunking.

Design:
- Groups sentences within a detected legal section into chunks
- Preserves page number, section type, and sequence order
- Respects CHUNK_SIZE (words) and CHUNK_OVERLAP (sentences) from config
- Every chunk knows: chunk_id, document_id, page_number, section, text, sequence
- Old behavior in pdf_service.py preserved for backward compatibility
"""

import uuid
import logging
import nltk
from typing import List, Dict, Optional

from backend.config import settings
from backend.services.legal_structure_service import get_section_for_page

logger = logging.getLogger("lexora.chunking")

# Ensure NLTK punkt tokenizer is available
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


def create_legal_chunks(
    pages: List[Dict],
    sections: Optional[List[Dict]] = None,
    document_id: Optional[int] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Dict]:
    """
    Create section-aware legal chunks from extracted pages.

    Args:
        pages: List of {page_number, text, word_count, has_text}
        sections: List of {section_type, start_page, end_page, confidence}
        document_id: Database document ID for chunk metadata
        chunk_size: Max words per chunk (default from config)
        chunk_overlap: Overlap in sentences between chunks (default from config)

    Returns:
        List of chunk dicts:
        {
          "chunk_id": "uuid-string",
          "document_id": int or None,
          "page_number": int,
          "section": str,
          "text": str,
          "sequence": int,
          "word_count": int,
        }
    """
    max_words = chunk_size or settings.CHUNK_SIZE
    overlap_sentences = chunk_overlap or settings.CHUNK_OVERLAP
    sections = sections or []

    chunks: List[Dict] = []
    sequence = 0

    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text") or ""
        if not text.strip():
            continue

        # Detect section for this page
        section_label = get_section_for_page(page_num, sections)

        # Tokenize into sentences
        try:
            sentences = nltk.sent_tokenize(text)
        except Exception:
            # Fallback: split on periods
            sentences = [s.strip() for s in text.split(".") if s.strip()]

        current_chunk: List[str] = []
        current_word_count = 0

        for i, sentence in enumerate(sentences):
            sentence_words = len(sentence.split())

            # If adding this sentence would exceed limit and we have content, flush
            if current_word_count + sentence_words > max_words and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(_make_chunk(
                    chunk_text, page_num, section_label, document_id, sequence
                ))
                sequence += 1

                # Overlap: carry over last N sentences
                overlap = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
                current_chunk = overlap + [sentence]
                current_word_count = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words

        # Flush remaining sentences in this page
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(_make_chunk(
                chunk_text, page_num, section_label, document_id, sequence
            ))
            sequence += 1

    logger.info(
        "Chunking complete: %d chunks from %d pages (chunk_size=%d, overlap=%d)",
        len(chunks), len(pages), max_words, overlap_sentences
    )
    return chunks


def _make_chunk(
    text: str,
    page_number: int,
    section: str,
    document_id: Optional[int],
    sequence: int,
) -> Dict:
    """Create a single chunk dict."""
    return {
        "chunk_id": str(uuid.uuid4()),
        "document_id": document_id,
        "page_number": page_number,
        "section": section,
        "text": text.strip(),
        "sequence": sequence,
        "word_count": len(text.split()),
    }

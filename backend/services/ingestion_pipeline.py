"""
Document Ingestion Pipeline — Phase 10
Orchestrates the full document processing pipeline in a background thread.

Pipeline stages:
  UPLOADED → VALIDATING → EXTRACTING → OCR_REQUIRED/PARSING →
  STRUCTURING → CHUNKING → EMBEDDING → INDEXING → ANALYZING → READY

Design:
- Runs in background thread to avoid blocking HTTP requests
- Each stage updates DocumentProcessingJob (status, progress, current_stage)
- Each stage is logged to DocumentProcessingLog
- Idempotent: checks for existing data before re-inserting on retry
- Document text is always treated as untrusted content
- No stack traces exposed to users in error messages
"""

import threading
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.config import settings

logger = logging.getLogger("lexora.ingestion_pipeline")

# ---------------------------------------------------------------------------
# Stage progress table (stage_name → progress_percent)
# ---------------------------------------------------------------------------
STAGE_PROGRESS = {
    "VALIDATING":         5,
    "EXTRACTING":        20,
    "OCR_CHECK":         25,
    "PARSING":           40,
    "STRUCTURING":       50,
    "CHUNKING":          60,
    "EMBEDDING":         75,
    "INDEXING":          82,
    "CITATION_EXTRACT":  87,
    "TIMELINE_EXTRACT":  92,
    "CASE_INTELLIGENCE": 96,
    "READY":            100,
}


# ---------------------------------------------------------------------------
# Job Status Helpers
# ---------------------------------------------------------------------------

def _update_job(db: Session, document_id: int, status: str, progress: float,
                current_stage: str, error_message: Optional[str] = None):
    """Update the processing job record."""
    from backend.models.document_intel import DocumentProcessingJob
    from backend.models.domain import Document

    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == document_id
    ).first()
    doc = db.query(Document).filter(Document.id == document_id).first()

    if job:
        job.status = status
        job.progress = progress
        job.current_stage = current_stage
        if error_message:
            job.error_message = error_message
        if status == "READY" or status == "FAILED":
            job.completed_at = datetime.now(timezone.utc)

    if doc:
        doc.status = status
        if error_message:
            doc.error_message = error_message

    db.commit()


def _log_stage(db: Session, document_id: int, stage: str, status: str,
               duration_ms: Optional[int] = None, message: Optional[str] = None):
    """Append an immutable processing log entry."""
    from backend.models.document_intel import DocumentProcessingLog

    entry = DocumentProcessingLog(
        document_id=document_id,
        stage=stage,
        status=status,
        duration_ms=duration_ms,
        message=message,
    )
    db.add(entry)
    db.commit()


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

def run_pipeline(document_id: int):
    """
    Entry point for background processing.
    Call this from the upload route:
        threading.Thread(target=run_pipeline, args=(doc.id,), daemon=True).start()
    """
    db = SessionLocal()
    try:
        _execute_pipeline(db, document_id)
    except Exception as e:
        logger.error("Pipeline crashed for doc %d: %s", document_id, str(e))
        try:
            _update_job(db, document_id, "FAILED", 0,
                        "Processing failed", "An unexpected error occurred.")
            _log_stage(db, document_id, "PIPELINE", "FAILED",
                       message="Pipeline crashed unexpectedly.")
        except Exception:
            pass
    finally:
        db.close()


def _execute_pipeline(db: Session, document_id: int):
    """Main pipeline execution logic."""
    from backend.models.domain import Document, DocumentChunk, Case
    from backend.models.document_intel import (
        DocumentPage, DocumentProcessingJob, LegalSectionDetection, DocumentFingerprint
    )
    from backend.services.legal_structure_service import detect_legal_sections
    from backend.services.metadata_service import extract_legal_metadata, save_metadata_to_db
    from backend.services.chunking_service import create_legal_chunks
    from backend.services.vector_service import index_document_chunk, chunk_exists, delete_document_chunks
    from backend.services.embedding_service import get_embedding

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error("Document %d not found for pipeline", document_id)
        return

    # Mark started
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == document_id
    ).first()
    if job:
        job.started_at = datetime.now(timezone.utc)
        db.commit()

    doc.processing_started_at = datetime.now(timezone.utc)
    db.commit()

    # -----------------------------------------------------------------------
    # Stage 1: TEXT EXTRACTION
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "EXTRACTING", STAGE_PROGRESS["EXTRACTING"],
                f"Extracting text from {doc.document_type.upper()} document")
    t0 = time.time()

    try:
        pages = _extract_pages(doc)
        duration_ms = int((time.time() - t0) * 1000)
        _log_stage(db, document_id, "EXTRACTION", "SUCCESS", duration_ms,
                   f"Extracted {len(pages)} pages")
        logger.info("Doc %d: extracted %d pages in %dms", document_id, len(pages), duration_ms)
    except Exception as e:
        _log_stage(db, document_id, "EXTRACTION", "FAILED",
                   message="Text extraction failed.")
        _update_job(db, document_id, "FAILED", STAGE_PROGRESS["EXTRACTING"],
                    "Extraction failed", "Could not extract text from this document.")
        return

    # -----------------------------------------------------------------------
    # Stage 2: OCR CHECK
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "OCR_CHECK", STAGE_PROGRESS["OCR_CHECK"],
                "Checking for scanned pages")

    if doc.document_type == "pdf":
        from backend.services.pdf_service import detect_ocr_required
        ocr_needed = detect_ocr_required(pages)
    else:
        ocr_needed = all(not p.get("has_text", True) for p in pages)

    if ocr_needed:
        doc.ocr_required = True
        if settings.OCR_ENABLED:
            _update_job(db, document_id, "OCR_REQUIRED", STAGE_PROGRESS["OCR_CHECK"],
                        "Running OCR on scanned document")
            # Attempt OCR if pytesseract configured
            pages = _attempt_ocr(doc, pages, db, document_id)
        else:
            # Not silently creating empty index
            _log_stage(db, document_id, "OCR_CHECK", "SKIPPED",
                       message="Document appears scanned. OCR is not configured.")
            _update_job(db, document_id, "OCR_REQUIRED", STAGE_PROGRESS["OCR_CHECK"],
                        "OCR required but not configured",
                        "This document appears to be scanned and requires OCR.")
            db.commit()
            return
    else:
        _log_stage(db, document_id, "OCR_CHECK", "SUCCESS",
                   message="Text extractable — no OCR needed")

    # -----------------------------------------------------------------------
    # Stage 3: SAVE PAGE RECORDS
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "PARSING", STAGE_PROGRESS["PARSING"],
                "Storing page records")
    t0 = time.time()

    # Idempotent: clear existing pages before saving
    db.query(DocumentPage).filter(DocumentPage.document_id == document_id).delete()
    db.commit()

    total_pages = len(pages)
    for page_data in pages:
        db.add(DocumentPage(
            document_id=document_id,
            page_number=page_data["page_number"],
            text=page_data.get("text", ""),
            word_count=page_data.get("word_count", 0),
            has_text=page_data.get("has_text", True),
        ))

    doc.page_count = total_pages
    db.commit()
    _log_stage(db, document_id, "PAGE_STORAGE", "SUCCESS",
               int((time.time() - t0) * 1000), f"Saved {total_pages} page records")

    # -----------------------------------------------------------------------
    # Stage 4: LEGAL STRUCTURE DETECTION
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "STRUCTURING", STAGE_PROGRESS["STRUCTURING"],
                "Detecting legal document structure")
    t0 = time.time()

    sections = detect_legal_sections(pages)

    # Idempotent: clear existing sections
    db.query(LegalSectionDetection).filter(
        LegalSectionDetection.document_id == document_id
    ).delete()
    db.commit()

    for sec in sections:
        db.add(LegalSectionDetection(
            document_id=document_id,
            section_type=sec["section_type"],
            confidence=sec["confidence"],
            start_page=sec.get("start_page"),
            end_page=sec.get("end_page"),
        ))

    db.commit()
    _log_stage(db, document_id, "STRUCTURE_DETECTION", "SUCCESS",
               int((time.time() - t0) * 1000),
               f"Detected {len(sections)} sections")

    # -----------------------------------------------------------------------
    # Stage 5: METADATA EXTRACTION
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "STRUCTURING", STAGE_PROGRESS["STRUCTURING"] + 5,
                "Extracting legal metadata")
    t0 = time.time()

    full_text = "\n".join(p.get("text", "") for p in pages)

    try:
        metadata = extract_legal_metadata(full_text)
        save_metadata_to_db(db, document_id, metadata)
        _log_stage(db, document_id, "METADATA_EXTRACTION", "SUCCESS",
                   int((time.time() - t0) * 1000))

        # Auto-link or create Case record
        _resolve_case(db, doc, metadata)

    except Exception as e:
        logger.warning("Metadata extraction failed for doc %d: %s", document_id, str(e))
        _log_stage(db, document_id, "METADATA_EXTRACTION", "FAILED",
                   message="Metadata extraction encountered an error.")

    # -----------------------------------------------------------------------
    # Stage 6: LEGAL-AWARE CHUNKING
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "CHUNKING", STAGE_PROGRESS["CHUNKING"],
                "Creating legal-aware text chunks")
    t0 = time.time()

    chunk_dicts = create_legal_chunks(pages, sections, document_id=document_id)

    # Idempotent: clear existing DB chunks
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.commit()

    db_chunks = []
    for c in chunk_dicts:
        db_chunk = DocumentChunk(
            document_id=document_id,
            page_number=c["page_number"],
            text=c["text"],
            chunk_id_str=c["chunk_id"],
            chunk_sequence=c["sequence"],
            section=c["section"],
        )
        db.add(db_chunk)
        db_chunks.append((c, db_chunk))

    db.commit()
    _log_stage(db, document_id, "CHUNKING", "SUCCESS",
               int((time.time() - t0) * 1000),
               f"Created {len(chunk_dicts)} chunks")

    # -----------------------------------------------------------------------
    # Stage 7: EMBEDDING + INDEXING
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "EMBEDDING", STAGE_PROGRESS["EMBEDDING"],
                "Generating embeddings")
    t0 = time.time()

    # Idempotent: clear existing vector index entries
    delete_document_chunks(document_id)

    case = doc.case
    case_name = case.case_name if case else "Unknown Case"
    court = case.court if case else ""
    year = case.year if case else 0
    legal_topics = case.legal_topics if case else ""
    case_id = doc.case_id or 0

    _update_job(db, document_id, "INDEXING", STAGE_PROGRESS["INDEXING"],
                "Indexing into vector store")

    for c_dict, db_chunk in db_chunks:
        chunk_id = c_dict["chunk_id"]
        if not chunk_exists(chunk_id):
            index_document_chunk(
                chunk_id=chunk_id,
                case_id=case_id,
                document_id=document_id,
                page_number=c_dict["page_number"],
                text=c_dict["text"],
                case_name=case_name,
                court=court,
                year=year,
                section=c_dict["section"],
                legal_topics=legal_topics,
                chunk_sequence=c_dict["sequence"],
            )

    _log_stage(db, document_id, "EMBEDDING_INDEXING", "SUCCESS",
               int((time.time() - t0) * 1000),
               f"Indexed {len(db_chunks)} chunks")

    # -----------------------------------------------------------------------
    # Stage 8: CITATION EXTRACTION
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "CITATION_EXTRACT", STAGE_PROGRESS["CITATION_EXTRACT"],
                "Extracting legal citations")
    t0 = time.time()

    if case_id:
        try:
            from backend.services.citation_service import process_and_save_citations
            saved = process_and_save_citations(db, case_id, full_text[:50000])
            _log_stage(db, document_id, "CITATION_EXTRACTION", "SUCCESS",
                       int((time.time() - t0) * 1000),
                       f"Extracted {saved} citations")
        except Exception as e:
            logger.warning("Citation extraction failed for doc %d: %s", document_id, str(e))
            _log_stage(db, document_id, "CITATION_EXTRACTION", "FAILED",
                       message="Citation extraction encountered an error.")
    else:
        _log_stage(db, document_id, "CITATION_EXTRACTION", "SKIPPED",
                   message="No case linked — skipping citation extraction")

    # -----------------------------------------------------------------------
    # Stage 9: CASE INTELLIGENCE (reuse Phase 3)
    # -----------------------------------------------------------------------
    _update_job(db, document_id, "ANALYZING", STAGE_PROGRESS["CASE_INTELLIGENCE"],
                "Running case intelligence analysis")
    t0 = time.time()

    if case_id and settings.GEMINI_API_KEY:
        try:
            from backend.services.intelligence_service import intelligence_engine
            fresh_case = db.query(Case).filter(Case.id == case_id).first()
            if fresh_case and fresh_case.analysis_status != "COMPLETED":
                intelligence_engine.analyze_case(db, case_id)
            _log_stage(db, document_id, "CASE_INTELLIGENCE", "SUCCESS",
                       int((time.time() - t0) * 1000))
        except Exception as e:
            logger.warning("Case intelligence failed for doc %d: %s", document_id, str(e))
            _log_stage(db, document_id, "CASE_INTELLIGENCE", "FAILED",
                       message="Case intelligence analysis encountered an error.")
    else:
        _log_stage(db, document_id, "CASE_INTELLIGENCE", "SKIPPED",
                   message="Gemini API not configured or no case linked.")

    # -----------------------------------------------------------------------
    # DONE
    # -----------------------------------------------------------------------
    doc.processing_completed_at = datetime.now(timezone.utc)
    _update_job(db, document_id, "READY", 100, "Processing complete")
    _log_stage(db, document_id, "PIPELINE_COMPLETE", "SUCCESS",
               message="Document is ready for search and analysis.")

    logger.info("Pipeline complete for document %d", document_id)


# ---------------------------------------------------------------------------
# Helper: extract pages by document type
# ---------------------------------------------------------------------------

def _extract_pages(doc) -> list:
    """Route to the correct extraction service based on document type."""
    from backend.services.pdf_service import extract_text_with_pages
    from backend.services.docx_service import extract_text_from_docx
    from backend.services.txt_service import extract_text_from_txt

    path = doc.storage_path
    if not path:
        raise ValueError("Document has no storage path")

    doc_type = (doc.document_type or "").lower()
    if doc_type == "pdf":
        return extract_text_with_pages(path)
    elif doc_type == "docx":
        return extract_text_from_docx(path)
    elif doc_type == "txt":
        return extract_text_from_txt(path)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")


# ---------------------------------------------------------------------------
# Helper: OCR attempt (if enabled)
# ---------------------------------------------------------------------------

def _attempt_ocr(doc, pages: list, db: Session, document_id: int) -> list:
    """Attempt OCR if pytesseract is configured."""
    try:
        import pytesseract  # noqa: F401
        import fitz
        from PIL import Image
        import io

        logger.info("Running OCR on document %d", document_id)
        ocr_pages = []
        pdf_doc = fitz.open(doc.storage_path)
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img)
            word_count = len(text.split())
            ocr_pages.append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "word_count": word_count,
                "has_text": word_count > 5,
            })
        pdf_doc.close()
        return ocr_pages
    except ImportError:
        logger.warning("pytesseract not available — OCR cannot be performed")
        return pages
    except Exception as e:
        logger.error("OCR failed: %s", str(e))
        return pages


# ---------------------------------------------------------------------------
# Helper: Case resolution / auto-creation
# ---------------------------------------------------------------------------

def _resolve_case(db: Session, doc, metadata: dict):
    """
    Link document to existing Case or create a new one.
    Detects potential duplicates without auto-merging.
    """
    from backend.models.domain import Case

    case_name_field = metadata.get("case_name", {})
    case_name = case_name_field.get("value") if case_name_field else None

    court_field = metadata.get("court", {})
    court = court_field.get("value") if court_field else None

    case_number_field = metadata.get("case_number", {})
    case_number = case_number_field.get("value") if case_number_field else None

    decision_date_field = metadata.get("decision_date", {})
    decision_date = decision_date_field.get("value") if decision_date_field else None

    legal_topics_field = metadata.get("legal_topics", {})
    legal_topics = legal_topics_field.get("value") if legal_topics_field else None

    if not case_name and not case_number:
        logger.info("No case identifiers found for doc %d — skipping case linking", doc.id)
        return

    # Try to find existing case by case_number (most reliable)
    existing_case = None
    if case_number:
        existing_case = db.query(Case).filter(
            Case.case_number == case_number
        ).first()

    # If not found by number, try name (but flag as potential duplicate)
    if not existing_case and case_name:
        existing_case = db.query(Case).filter(
            Case.case_name.ilike(f"%{case_name[:50]}%")
        ).first()
        if existing_case:
            logger.info(
                "Potential duplicate case detected: doc=%d name='%s' matches case_id=%d. "
                "Not auto-merging.",
                doc.id, case_name, existing_case.id
            )

    if existing_case:
        doc.case_id = existing_case.id
        db.commit()
        logger.info("Linked doc %d to existing case %d", doc.id, existing_case.id)
    else:
        # Create new Case record
        from datetime import datetime
        decision_dt = None
        if decision_date:
            try:
                from datetime import datetime
                decision_dt = datetime.strptime(decision_date, "%Y-%m-%d")
            except Exception:
                pass

        new_case = Case(
            case_name=case_name or "Unknown Case",
            court=court or "Unknown Court",
            year=decision_dt.year if decision_dt else 0,
            case_number=case_number,
            decision_date=decision_dt,
            category="DOCUMENT_IMPORT",
            legal_topics=legal_topics,
            analysis_status="PENDING",
        )
        db.add(new_case)
        db.flush()
        doc.case_id = new_case.id
        db.commit()
        logger.info("Created new case %d for doc %d", new_case.id, doc.id)

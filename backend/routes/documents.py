"""
Document Intelligence API Routes — Phase 10

Endpoints:
  POST  /api/documents/upload         - Upload + validate + start pipeline
  GET   /api/documents                - List own documents
  GET   /api/documents/{id}           - Document detail
  GET   /api/documents/{id}/status    - Pipeline job progress
  POST  /api/documents/{id}/process   - Re-trigger processing
  POST  /api/documents/{id}/retry     - Idempotent retry from failed stage
  DELETE /api/documents/{id}          - Delete document + embeddings
  GET   /api/documents/{id}/pages/{page} - Fetch single page text
  GET   /api/documents/{id}/search    - Search within document
  GET   /api/documents/{id}/logs      - Processing log history

Security:
- File size enforced before reading bytes
- Filename sanitized; original stored separately
- Path traversal prevented at storage layer
- Owner check on all document routes
- RESEARCHER/ADMIN can upload; VIEWER can only read authorized docs
- Document text treated as untrusted throughout
"""

import threading
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models.domain import Document, User, DocumentChunk, Case
from backend.models.document_intel import (
    DocumentProcessingJob, DocumentProcessingLog,
    DocumentPage, LegalSectionDetection, DocumentMetadata
)
from backend.schemas.domain import (
    DocumentListItem, DocumentUploadResponse, DocumentStatusResponse,
    DocumentDetailResponse, DocumentPageResponse, DocumentSearchResult,
    ProcessingLogEntry, DocumentMetadataField, DocumentSectionInfo, DocumentVersionItem
)
from backend.dependencies import get_current_user
from backend.services.document_service import (
    validate_document, calculate_file_hash, find_duplicate_document,
    store_document, create_document_record, generate_document_id
)
from backend.services.ingestion_pipeline import run_pipeline
from backend.services.vector_service import delete_document_chunks, search_in_document
from backend.config import settings

logger = logging.getLogger("lexora.routes.documents")
router = APIRouter()

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------

def _get_authorized_document(
    document_id: int,
    db: Session,
    current_user: User,
    require_owner: bool = False,
) -> Document:
    """
    Fetch document and verify the user is authorized to access it.
    Raises 404 (not 403) to avoid leaking document existence.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    is_owner = doc.owner_id == current_user.id
    is_admin = current_user.role == "ADMIN"

    if not (is_owner or is_admin):
        # VIEWER role: raise 404 to avoid disclosing existence
        raise HTTPException(status_code=404, detail="Document not found.")

    if require_owner and not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Operation not permitted.")

    return doc


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    case_id: Optional[int] = Query(None, description="Link to existing case (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a legal document (PDF, DOCX, TXT).
    Validates the file, checks for duplicates, stores it securely,
    and launches the ingestion pipeline in the background.
    """
    # Only RESEARCHER and ADMIN can upload
    if current_user.role not in ("RESEARCHER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Researchers and Admins can upload documents."
        )

    # Read file bytes with size limit guard
    file_bytes = await file.read(MAX_BYTES + 1)
    original_filename = file.filename or "document"

    # Validate (raises HTTPException on failure)
    title, ext = validate_document(original_filename, file.content_type or "", file_bytes)

    # Duplicate detection
    file_hash = calculate_file_hash(file_bytes)
    existing_doc_id = find_duplicate_document(db, file_hash)
    if existing_doc_id:
        return DocumentUploadResponse(
            document_id=existing_doc_id,
            title=title,
            status="READY",
            message="Document already exists. Returning existing document.",
            duplicate_of=existing_doc_id,
        )

    # Generate internal ID and store file securely
    internal_id = generate_document_id()
    try:
        storage_path = store_document(file_bytes, internal_id, ext)
    except Exception as e:
        logger.error("File storage failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Document storage failed.")

    # Create database record
    try:
        doc = create_document_record(
            db=db,
            owner_id=current_user.id,
            title=title,
            original_filename=original_filename,
            document_type=ext,
            storage_path=storage_path,
            file_size_bytes=len(file_bytes),
            file_hash=file_hash,
            case_id=case_id,
        )
    except Exception as e:
        logger.error("DB record creation failed: %s", str(e))
        # Clean up stored file
        try:
            os.remove(storage_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Could not create document record.")

    # Launch pipeline in background thread
    threading.Thread(target=run_pipeline, args=(doc.id,), daemon=True).start()
    logger.info("Launched pipeline for document %d (type=%s)", doc.id, ext)

    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == doc.id
    ).first()

    return DocumentUploadResponse(
        document_id=doc.id,
        title=doc.title,
        status=doc.status,
        message="Document uploaded successfully. Processing has started.",
        job_id=job.id if job else None,
    )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

@router.get("", response_model=List[DocumentListItem])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents owned by the current user (ADMIN sees all)."""
    query = db.query(Document)
    if current_user.role != "ADMIN":
        query = query.filter(Document.owner_id == current_user.id)

    docs = query.order_by(Document.uploaded_at.desc()).all()

    result = []
    for doc in docs:
        case_name = doc.case.case_name if doc.case else None
        result.append(DocumentListItem(
            id=doc.id,
            title=doc.title,
            original_filename=doc.original_filename,
            document_type=doc.document_type,
            status=doc.status,
            page_count=doc.page_count,
            file_size_bytes=doc.file_size_bytes,
            version_number=doc.version_number,
            uploaded_at=doc.uploaded_at,
            case_id=doc.case_id,
            case_name=case_name,
        ))
    return result


# ---------------------------------------------------------------------------
# GET /{document_id}
# ---------------------------------------------------------------------------

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full document detail including metadata, sections, and processing log."""
    doc = _get_authorized_document(document_id, db, current_user)

    metadata_records = db.query(DocumentMetadata).filter(
        DocumentMetadata.document_id == document_id
    ).all()
    section_records = db.query(LegalSectionDetection).filter(
        LegalSectionDetection.document_id == document_id
    ).all()
    log_records = db.query(DocumentProcessingLog).filter(
        DocumentProcessingLog.document_id == document_id
    ).order_by(DocumentProcessingLog.timestamp.asc()).all()

    return DocumentDetailResponse(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        document_type=doc.document_type,
        status=doc.status,
        page_count=doc.page_count,
        file_size_bytes=doc.file_size_bytes,
        ocr_required=doc.ocr_required or False,
        version_number=doc.version_number,
        parent_document_id=doc.parent_document_id,
        uploaded_at=doc.uploaded_at,
        processing_started_at=doc.processing_started_at,
        processing_completed_at=doc.processing_completed_at,
        error_message=doc.error_message,
        case_id=doc.case_id,
        case_name=doc.case.case_name if doc.case else None,
        metadata_fields=[
            DocumentMetadataField(
                field_name=m.field_name,
                field_value=m.field_value,
                confidence=m.confidence,
            ) for m in metadata_records
        ],
        sections=[
            DocumentSectionInfo(
                section_type=s.section_type,
                confidence=s.confidence,
                start_page=s.start_page,
                end_page=s.end_page,
            ) for s in section_records
        ],
        processing_logs=[
            ProcessingLogEntry(
                stage=log.stage,
                status=log.status,
                duration_ms=log.duration_ms,
                message=log.message,
                timestamp=log.timestamp,
            ) for log in log_records
        ],
    )


# ---------------------------------------------------------------------------
# GET /{document_id}/status
# ---------------------------------------------------------------------------

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Poll processing job progress.
    Returns: status, progress (0-100), current_stage, pages_processed, total_pages
    """
    doc = _get_authorized_document(document_id, db, current_user)

    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == document_id
    ).first()

    # Count processed pages for progress detail
    pages_processed = db.query(DocumentPage).filter(
        DocumentPage.document_id == document_id
    ).count()

    return DocumentStatusResponse(
        document_id=document_id,
        status=job.status if job else doc.status,
        progress=job.progress if job else 0,
        current_stage=job.current_stage if job else None,
        pages_processed=pages_processed,
        total_pages=doc.page_count,
        error_message=doc.error_message,
        started_at=job.started_at if job else None,
        completed_at=job.completed_at if job else None,
    )


# ---------------------------------------------------------------------------
# POST /{document_id}/process
# ---------------------------------------------------------------------------

@router.post("/{document_id}/process")
def trigger_processing(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-trigger pipeline processing for a document."""
    doc = _get_authorized_document(document_id, db, current_user, require_owner=True)

    if doc.status == "READY":
        return {"message": "Document is already processed.", "status": "READY"}

    # Reset job
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == document_id
    ).first()
    if job:
        job.status = "UPLOADED"
        job.progress = 0.0
        job.current_stage = "Queued for reprocessing"
        job.error_message = None
    doc.status = "UPLOADED"
    doc.error_message = None
    db.commit()

    threading.Thread(target=run_pipeline, args=(doc.id,), daemon=True).start()
    return {"message": "Processing started.", "document_id": document_id}


# ---------------------------------------------------------------------------
# POST /{document_id}/retry
# ---------------------------------------------------------------------------

@router.post("/{document_id}/retry")
def retry_processing(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Idempotent retry for a FAILED document.
    The pipeline will check for existing data before re-inserting.
    """
    doc = _get_authorized_document(document_id, db, current_user, require_owner=True)

    if doc.status == "READY":
        return {"message": "Document is already ready.", "status": "READY"}

    if doc.status not in ("FAILED", "OCR_REQUIRED"):
        raise HTTPException(
            status_code=400,
            detail=f"Document is in '{doc.status}' state. Only FAILED documents can be retried."
        )

    # Reset to allow re-run
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.document_id == document_id
    ).first()
    if job:
        job.status = "UPLOADED"
        job.progress = 0.0
        job.current_stage = "Retrying"
        job.error_message = None
    doc.status = "UPLOADED"
    doc.error_message = None
    db.commit()

    threading.Thread(target=run_pipeline, args=(doc.id,), daemon=True).start()
    return {"message": "Retry started.", "document_id": document_id}


# ---------------------------------------------------------------------------
# DELETE /{document_id}
# ---------------------------------------------------------------------------

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and all associated data:
    - Vector store chunks
    - Database records (pages, chunks, metadata, sections, logs, job, fingerprint)
    - Original file from storage
    """
    doc = _get_authorized_document(document_id, db, current_user, require_owner=True)

    if current_user.role not in ("RESEARCHER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Operation not permitted.")

    # 1. Remove vector embeddings
    delete_document_chunks(document_id)

    # 2. Delete from storage
    storage_path = doc.storage_path
    if storage_path and os.path.exists(storage_path):
        try:
            os.remove(storage_path)
            # Try to remove the directory if empty
            storage_dir = os.path.dirname(storage_path)
            if os.path.isdir(storage_dir) and not os.listdir(storage_dir):
                os.rmdir(storage_dir)
        except OSError as e:
            logger.warning("Could not delete file %s: %s", storage_path, str(e))

    # 3. Delete DB record (cascade handles related records)
    db.delete(doc)
    db.commit()

    logger.info("Document %d deleted by user %d", document_id, current_user.id)
    return {"message": "Document deleted.", "document_id": document_id}


# ---------------------------------------------------------------------------
# GET /{document_id}/pages/{page_number}
# ---------------------------------------------------------------------------

@router.get("/{document_id}/pages/{page_number}", response_model=DocumentPageResponse)
def get_document_page(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch extracted text for a single page (for source viewer)."""
    _get_authorized_document(document_id, db, current_user)

    page = db.query(DocumentPage).filter(
        DocumentPage.document_id == document_id,
        DocumentPage.page_number == page_number,
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found.")

    # Get section for this page
    from backend.services.legal_structure_service import get_section_for_page
    sections = db.query(LegalSectionDetection).filter(
        LegalSectionDetection.document_id == document_id
    ).all()
    section_list = [
        {"section_type": s.section_type, "start_page": s.start_page, "end_page": s.end_page}
        for s in sections
    ]
    section_label = get_section_for_page(page_number, section_list)

    return DocumentPageResponse(
        page_number=page.page_number,
        text=page.text,
        word_count=page.word_count,
        has_text=page.has_text,
        section=section_label,
    )


# ---------------------------------------------------------------------------
# GET /{document_id}/search
# ---------------------------------------------------------------------------

@router.get("/{document_id}/search", response_model=List[DocumentSearchResult])
def search_in_document_route(
    document_id: int,
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search within a single document.
    Returns matching pages with text snippets.
    """
    doc = _get_authorized_document(document_id, db, current_user)

    if doc.status != "READY":
        raise HTTPException(
            status_code=400,
            detail="Document is not yet fully processed. Please wait."
        )

    results = search_in_document(document_id, q, n_results=10)

    # Also do keyword search in pages for complementary results
    pages = db.query(DocumentPage).filter(
        DocumentPage.document_id == document_id
    ).all()
    keyword_hits = {
        p.page_number: p for p in pages
        if p.text and q.lower() in p.text.lower()
    }

    # Merge semantic + keyword results, deduplicate by page
    seen_pages = set()
    output = []

    for hit in results:
        pg = hit["page_number"]
        if pg not in seen_pages:
            seen_pages.add(pg)
            # Extract snippet around match
            text = hit["text"]
            snippet = text[:300] if text else ""
            output.append(DocumentSearchResult(
                page_number=pg,
                text_snippet=snippet,
                match_count=1,
            ))

    for pg_num, page_rec in keyword_hits.items():
        if pg_num not in seen_pages:
            seen_pages.add(pg_num)
            text = page_rec.text or ""
            # Find keyword position for context
            idx = text.lower().find(q.lower())
            start = max(0, idx - 100)
            snippet = text[start:start + 300]
            output.append(DocumentSearchResult(
                page_number=pg_num,
                text_snippet=snippet,
                match_count=text.lower().count(q.lower()),
            ))

    output.sort(key=lambda x: x.page_number)
    return output


# ---------------------------------------------------------------------------
# GET /{document_id}/logs
# ---------------------------------------------------------------------------

@router.get("/{document_id}/logs", response_model=List[ProcessingLogEntry])
def get_processing_logs(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return full processing history for a document."""
    _get_authorized_document(document_id, db, current_user)

    logs = db.query(DocumentProcessingLog).filter(
        DocumentProcessingLog.document_id == document_id
    ).order_by(DocumentProcessingLog.timestamp.asc()).all()

    return [
        ProcessingLogEntry(
            stage=log.stage,
            status=log.status,
            duration_ms=log.duration_ms,
            message=log.message,
            timestamp=log.timestamp,
        )
        for log in logs
    ]


# ---------------------------------------------------------------------------
# GET /{document_id}/versions
# ---------------------------------------------------------------------------

@router.get("/{document_id}/versions", response_model=List[DocumentVersionItem])
def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all versions of a document (including itself and child versions)."""
    doc = _get_authorized_document(document_id, db, current_user)

    # Find root document
    root_id = doc.parent_document_id or doc.id

    # Get all documents sharing this root or parented to root
    versions = db.query(Document).filter(
        (Document.id == root_id) |
        (Document.parent_document_id == root_id)
    ).order_by(Document.version_number.asc()).all()

    return [
        DocumentVersionItem(
            id=v.id,
            version_number=v.version_number,
            uploaded_at=v.uploaded_at,
            status=v.status,
        )
        for v in versions
    ]

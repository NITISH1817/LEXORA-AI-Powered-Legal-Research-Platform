"""
Document Service — Phase 10
Handles file validation, secure storage, and duplicate detection.

Security:
- Never trust original filename or client-provided MIME type
- Sanitize filenames before storing
- SHA-256 hash for duplicate detection
- Path traversal prevention via strict path construction
- Size limits enforced before reading file bytes
"""

import os
import re
import uuid
import hashlib
import logging
import mimetypes
from typing import Optional, Tuple

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.config import settings

logger = logging.getLogger("lexora.document_service")

# ---------------------------------------------------------------------------
# Constants derived from config — do NOT hardcode elsewhere
# ---------------------------------------------------------------------------
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTS = {ext.strip().lower() for ext in settings.ALLOWED_EXTENSIONS.split(",")}

# Safe MIME type allowlist — never rely on client-provided Content-Type alone
ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/msword",    # legacy .doc — we'll reject at ext check
    "application/octet-stream",  # generic binary; pass-through for ext check
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """
    Strip path components and replace unsafe characters.
    The original filename is stored separately; the sanitized name is only
    used for display — never for filesystem path construction.
    """
    # Normalize backslashes to forward slashes for cross-platform POSIX compatibility
    name = name.replace("\\", "/")
    # Take the basename only (prevents directory traversal via filename)
    name = os.path.basename(name)
    # Strip any directory traversal dots (e.g. "..")
    name = name.replace("..", "")
    # Keep only alphanumeric, dash, underscore, dot
    name = re.sub(r"[^\w\.\-]", "_", name)
    # Collapse multiple underscores/dots
    name = re.sub(r"_{2,}", "_", name)
    # Limit length
    return name[:200]


def get_file_extension(filename: str) -> str:
    """Return lowercase extension without the dot."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


def detect_mime_from_bytes(data: bytes) -> str:
    """
    Detect MIME type from file magic bytes.
    Falls back to mimetypes library if python-magic is not installed.
    Never trusts the client-provided Content-Type.
    """
    try:
        import magic
        return magic.from_buffer(data[:2048], mime=True)
    except ImportError:
        pass
    # Fallback: check magic bytes manually for common types
    if data[:4] == b"%PDF":
        return "application/pdf"
    if data[:4] == b"PK\x03\x04":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"


def validate_document(
    filename: str,
    content_type: str,      # from HTTP header — untrusted
    file_bytes: bytes,
) -> Tuple[str, str]:
    """
    Validate a document upload.

    Returns:
        (sanitized_title, detected_extension)

    Raises:
        HTTPException with safe user-facing message on any violation.
    """
    # 1. File size (bytes already read by caller with limit)
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Document appears to be empty.")

    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB."
        )

    # 2. Extension check
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTS))}."
        )

    # 3. Magic bytes MIME check (ignore client-provided Content-Type)
    detected_mime = detect_mime_from_bytes(file_bytes)
    # Map extension to expected MIME
    expected_mimes_for_ext = {
        "pdf": {"application/pdf"},
        "docx": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/zip",          # DOCX is a ZIP internally
            "application/octet-stream",
        },
        "txt": {"text/plain", "application/octet-stream"},
    }
    allowed_mimes_for_ext = expected_mimes_for_ext.get(ext, {"application/octet-stream"})
    if detected_mime not in allowed_mimes_for_ext:
        logger.warning(
            "MIME mismatch: filename=%s ext=%s detected=%s",
            filename, ext, detected_mime
        )
        # For txt files with text/* subtypes we allow through
        if ext == "txt" and detected_mime.startswith("text/"):
            pass
        elif ext != "docx" or detected_mime not in {"application/zip"}:
            raise HTTPException(
                status_code=415,
                detail="File content does not match the declared file type."
            )

    # 4. Integrity and corruption checks
    if ext == "pdf":
        if not file_bytes[:4] == b"%PDF":
            raise HTTPException(status_code=422, detail="File appears to be a corrupted PDF.")
        try:
            import fitz
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            if pdf_doc.is_encrypted:
                pdf_doc.close()
                raise HTTPException(
                    status_code=422,
                    detail="Encrypted or password-protected PDFs are not supported."
                )
            if len(pdf_doc) == 0:
                pdf_doc.close()
                raise HTTPException(status_code=422, detail="PDF document contains no pages.")
            pdf_doc.close()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=422, detail="File appears to be a corrupted PDF.")
    elif ext == "docx":
        import zipfile
        import io
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                if "word/document.xml" not in z.namelist():
                    raise HTTPException(status_code=422, detail="File appears to be a corrupted DOCX.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=422, detail="File appears to be a corrupted DOCX.")
    elif ext == "txt":
        if not file_bytes.strip():
            raise HTTPException(status_code=400, detail="Document appears to be empty.")
        try:
            file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                file_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(status_code=422, detail="Could not decode text file.")

    # 5. Sanitize filename for display title
    sanitized = _sanitize_filename(filename)
    title = os.path.splitext(sanitized)[0]

    return title, ext


# ---------------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------------

def calculate_file_hash(file_bytes: bytes) -> str:
    """SHA-256 of raw file bytes. Used for exact duplicate detection."""
    return hashlib.sha256(file_bytes).hexdigest()


def find_duplicate_document(db: Session, file_hash: str, owner_id: Optional[int] = None) -> Optional[int]:
    """
    Check if a document with this hash already exists for this owner.
    Returns existing document_id or None.
    """
    from backend.models.document_intel import DocumentFingerprint
    from backend.models.domain import Document

    query = db.query(DocumentFingerprint).join(
        Document, DocumentFingerprint.document_id == Document.id
    ).filter(
        DocumentFingerprint.hash_sha256 == file_hash
    )
    if owner_id is not None:
        query = query.filter(Document.owner_id == owner_id)

    fp = query.first()
    return fp.document_id if fp else None


# ---------------------------------------------------------------------------
# Secure File Storage
# ---------------------------------------------------------------------------

def generate_document_id() -> str:
    """Generate a UUID-based internal document identifier."""
    return str(uuid.uuid4())


def get_upload_path(internal_id: str, ext: str) -> str:
    """
    Build secure storage path for a document.
    Uses internal UUID — never the original filename — to prevent path traversal.
    """
    # Validate internal_id is a valid UUID (belt-and-suspenders)
    try:
        uuid.UUID(internal_id)
    except ValueError:
        raise ValueError(f"Invalid internal document ID: {internal_id}")

    doc_dir = os.path.join(settings.UPLOAD_DIR, internal_id)
    os.makedirs(doc_dir, exist_ok=True)
    return os.path.join(doc_dir, f"original.{ext}")


def store_document(file_bytes: bytes, internal_id: str, ext: str) -> str:
    """
    Write document bytes to secure storage.
    Returns the stored file path.

    Security:
    - Path is always built from UUID + known extension
    - Original filename is NEVER used in path construction
    - Directory is created only under UPLOAD_DIR
    """
    path = get_upload_path(internal_id, ext)

    # Final path traversal guard: ensure path is inside UPLOAD_DIR
    upload_dir_real = os.path.realpath(settings.UPLOAD_DIR)
    path_real = os.path.realpath(path)
    if not path_real.startswith(upload_dir_real + os.sep):
        raise ValueError("Path traversal detected. Aborting storage.")

    with open(path, "wb") as f:
        f.write(file_bytes)

    logger.info("Stored document %s at %s (%d bytes)", internal_id, path, len(file_bytes))
    return path


# ---------------------------------------------------------------------------
# Database Record Creation
# ---------------------------------------------------------------------------

def create_document_record(
    db: Session,
    owner_id: int,
    title: str,
    original_filename: str,
    document_type: str,
    storage_path: str,
    file_size_bytes: int,
    file_hash: str,
    version_number: int = 1,
    parent_document_id: Optional[int] = None,
    case_id: Optional[int] = None,
) -> "Document":  # noqa: F821
    from backend.models.domain import Document
    from backend.models.document_intel import DocumentFingerprint, DocumentProcessingJob

    doc = Document(
        owner_id=owner_id,
        case_id=case_id,
        title=title,
        original_filename=original_filename,
        storage_path=storage_path,
        document_type=document_type,
        file_size_bytes=file_size_bytes,
        file_hash=file_hash,
        status="UPLOADED",
        version_number=version_number,
        parent_document_id=parent_document_id,
    )
    db.add(doc)
    db.flush()  # get doc.id

    # Fingerprint record
    fp = DocumentFingerprint(document_id=doc.id, hash_sha256=file_hash)
    db.add(fp)

    # Initial processing job
    job = DocumentProcessingJob(
        document_id=doc.id,
        status="UPLOADED",
        progress=0.0,
        current_stage="Queued",
    )
    db.add(job)

    db.commit()
    db.refresh(doc)
    return doc

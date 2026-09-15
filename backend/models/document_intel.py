from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime, timezone


class DocumentPage(Base):
    """
    Stores extracted text for each individual page of a document.
    Every downstream chunk references its page for evidence grounding.
    """
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    has_text = Column(Boolean, default=True)  # False for scanned/image-only pages
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="pages")


class DocumentProcessingJob(Base):
    """
    Tracks long-running document processing pipeline state.
    Created when a document is uploaded; updated throughout pipeline stages.
    """
    __tablename__ = "document_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    status = Column(String, default="UPLOADED")
    # Valid statuses: UPLOADED, VALIDATING, EXTRACTING, OCR_REQUIRED, PARSING,
    #                 STRUCTURING, EMBEDDING, INDEXING, ANALYZING, READY, FAILED
    progress = Column(Float, default=0.0)  # 0–100
    current_stage = Column(String, nullable=True)
    error_message = Column(String, nullable=True)  # sanitized, no stack traces exposed to users
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="processing_job", uselist=False)


class DocumentProcessingLog(Base):
    """
    Immutable log of every pipeline stage for a document.
    Provides full processing history without exposing internal secrets or stack traces.
    """
    __tablename__ = "document_processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)
    status = Column(String, default="SUCCESS")  # SUCCESS, FAILED, SKIPPED
    duration_ms = Column(Integer, nullable=True)
    message = Column(String, nullable=True)  # sanitized, user-facing message only
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="processing_logs")


class LegalSectionDetection(Base):
    """
    Stores detected legal document sections with confidence scores.
    Sections: BACKGROUND, FACTS, PLEADINGS, PLAINTIFF_ARGUMENTS, DEFENDANT_ARGUMENTS,
              ISSUES, EVIDENCE, ANALYSIS, REASONING, FINDINGS, JUDGMENT, ORDER,
              CONCLUSION, PROCEDURAL_HISTORY, OTHER
    """
    __tablename__ = "legal_section_detections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    section_type = Column(String, nullable=False)
    confidence = Column(Float, default=0.5)
    start_page = Column(Integer, nullable=True)
    end_page = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="section_detections")


class DocumentMetadata(Base):
    """
    Stores extracted legal metadata fields with individual confidence scores.
    Each field is stored separately so missing fields remain null without fabrication.
    Fields: case_name, court, jurisdiction, case_number, decision_date, judges,
            parties, appellant, respondent, legal_topics, statutes, regulations,
            cited_authorities
    """
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    field_name = Column(String, nullable=False)
    field_value = Column(Text, nullable=True)   # null if not found — never fabricated
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="extracted_metadata")


class DocumentFingerprint(Base):
    """
    SHA-256 hash of the original document bytes for duplicate detection.
    If hash already exists: processing is skipped and existing document is returned.
    """
    __tablename__ = "document_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    hash_sha256 = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="fingerprint", uselist=False)

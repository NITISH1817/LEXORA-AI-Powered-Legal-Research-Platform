from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, Table
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime, timezone
# Phase 10: document intelligence models imported after this file loads (circular-safe via string refs)

# Association table for Collection <-> Case
collection_case = Table(
    "collection_case",
    Base.metadata,
    Column("collection_id", Integer, ForeignKey("research_collections.id"), primary_key=True),
    Column("case_id", Integer, ForeignKey("cases.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(String, default="RESEARCHER") # ADMIN, RESEARCHER, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)
    
    sessions = relationship("ResearchSession", back_populates="user")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String, index=True)
    court = Column(String, index=True)
    year = Column(Integer, index=True)
    case_number = Column(String, index=True, nullable=True)
    category = Column(String, index=True) # Case Type
    decision_date = Column(DateTime, nullable=True)
    
    # Intelligence status
    analysis_status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    legal_topics = Column(Text, nullable=True) # JSON array or comma separated
    
    # AI Extracted Intelligence
    executive_summary = Column(Text, nullable=True)
    facts_summary = Column(Text, nullable=True) # Renamed to prevent clash with facts relationship
    procedural_history = Column(Text, nullable=True)
    legal_issues_summary = Column(Text, nullable=True) # Renamed to prevent clash
    parties_arguments_summary = Column(Text, nullable=True) # Renamed to prevent clash
    court_reasoning = Column(Text, nullable=True)
    decision = Column(Text, nullable=True)
    remedy = Column(Text, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="case")
    
    # Phase 3 Extracted Intelligence Relationships
    facts = relationship("CaseFact", back_populates="case", cascade="all, delete-orphan")
    legal_issues = relationship("LegalIssue", back_populates="case", cascade="all, delete-orphan")
    party_arguments = relationship("PartyArgument", back_populates="case", cascade="all, delete-orphan")
    principles = relationship("LegalPrinciple", back_populates="case", cascade="all, delete-orphan")
    timeline_events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")
    important_passages = relationship("ImportantPassage", back_populates="case", cascade="all, delete-orphan")
    
    # Self-referential for citations
    citations_made = relationship("Citation", foreign_keys="[Citation.citing_case_id]", back_populates="citing_case")
    citations_received = relationship("Citation", foreign_keys="[Citation.cited_case_id]", back_populates="cited_case")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String)
    original_filename = Column(String, nullable=True)          # original user-provided name
    file_path = Column(String, nullable=True)                  # legacy field — kept for Phase 1-9 compat
    storage_path = Column(String, nullable=True)               # internal secure storage path
    document_type = Column(String, nullable=True)              # pdf, docx, txt
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for duplicate detection
    page_count = Column(Integer, nullable=True)
    ocr_required = Column(Boolean, default=False)
    # Phase 10 ingestion status
    status = Column(String, default="UPLOADED", index=True)
    # Statuses: UPLOADED, VALIDATING, EXTRACTING, OCR_REQUIRED, PARSING,
    #           STRUCTURING, EMBEDDING, INDEXING, ANALYZING, READY, FAILED
    error_message = Column(String, nullable=True)  # user-facing only, no stack traces
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    # Versioning
    version_number = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    # Phase 10 relationships (string references to avoid circular imports)
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    processing_job = relationship("DocumentProcessingJob", back_populates="document",
                                  uselist=False, cascade="all, delete-orphan")
    processing_logs = relationship("DocumentProcessingLog", back_populates="document",
                                   cascade="all, delete-orphan")
    section_detections = relationship("LegalSectionDetection", back_populates="document",
                                      cascade="all, delete-orphan")
    extracted_metadata = relationship("DocumentMetadata", back_populates="document",
                                      cascade="all, delete-orphan")
    fingerprint = relationship("DocumentFingerprint", back_populates="document",
                               uselist=False, cascade="all, delete-orphan")
    # Self-referential for versioning
    versions = relationship("Document", foreign_keys=[parent_document_id])


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer)
    text = Column(Text)
    # Phase 10 additions
    chunk_id_str = Column(String, nullable=True, index=True)  # aligns with vector store ID
    chunk_sequence = Column(Integer, nullable=True)            # order within document
    section = Column(String, nullable=True)                    # detected legal section label
    # embedding goes to vector DB, so we only store chunk metadata here

    document = relationship("Document", back_populates="chunks")
    important_passages = relationship("ImportantPassage", back_populates="chunk")

# ---------------------------------------------------------
# Phase 3 Lexora Intelligence Models
# ---------------------------------------------------------

class CaseFact(Base):
    __tablename__ = "case_facts"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    fact_type = Column(String) # Material, Background, Disputed, Undisputed
    description = Column(Text)
    source_id = Column(String, nullable=True)
    
    case = relationship("Case", back_populates="facts")

class LegalIssue(Base):
    __tablename__ = "legal_issues"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    issue_text = Column(Text)
    
    case = relationship("Case", back_populates="legal_issues")

class PartyArgument(Base):
    __tablename__ = "party_arguments"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    party_type = Column(String) # Petitioner, Respondent
    argument_text = Column(Text)
    
    case = relationship("Case", back_populates="party_arguments")

class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    
    event_date = Column(String, nullable=True) # YYYY-MM-DD if exact, else approximate sortable string
    date_text = Column(String) # The raw string e.g. "around March 2022"
    date_precision = Column(String) # exact, approximate, range, unknown
    
    event_type = Column(String, index=True) # e.g. JUDGMENT, CONTRACT, NOTICE
    title = Column(String)
    description = Column(Text)
    actors = Column(String, nullable=True) # JSON array string
    court = Column(String, nullable=True)
    timeline_type = Column(String) # FACTUAL or PROCEDURAL
    
    source_document_id = Column(Integer, nullable=True)
    source_chunk_id = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    supporting_text = Column(Text)
    verification_status = Column(String, default="needs_review") # accepted, rejected, needs_review
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    case = relationship("Case", back_populates="timeline_events")

class ImportantPassage(Base):
    __tablename__ = "important_passages"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    category = Column(String) # FACT, ISSUE, ARGUMENT, EVIDENCE, REASONING, PRINCIPLE, DECISION
    page_number = Column(Integer, nullable=True)
    text = Column(Text)
    
    case = relationship("Case", back_populates="important_passages")
    chunk = relationship("DocumentChunk", back_populates="important_passages")

# ---------------------------------------------------------

class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, index=True)
    citing_case_id = Column(Integer, ForeignKey("cases.id"))
    cited_case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    cited_case_name = Column(String, nullable=True) # if case not in our DB
    context = Column(Text, nullable=True)
    relationship_type = Column(String) # CITES, FOLLOWS, DISTINGUISHES, etc.
    
    citing_case = relationship("Case", foreign_keys=[citing_case_id], back_populates="citations_made")
    cited_case = relationship("Case", foreign_keys=[cited_case_id], back_populates="citations_received")

class LegalPrinciple(Base):
    __tablename__ = "legal_principles"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    description = Column(Text)
    source_passage = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    
    case = relationship("Case", back_populates="principles")

# NOTE: ResearchSession is fully defined below (lines ~254+). The duplicate definition
# that previously existed here has been removed in Phase 10 to fix the shadowing bug.

class ResearchQuery(Base):
    __tablename__ = "research_queries"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    query_text = Column(Text)
    structured_intent = Column(Text, nullable=True) # JSON string
    filters = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    session = relationship("ResearchSession", back_populates="queries")

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    case_id = Column(Integer, ForeignKey("cases.id"))
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    notes = Column(Text, nullable=True)

    case = relationship("Case")

class ResearchCollection(Base):
    __tablename__ = "research_collections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="collections")
    cases = relationship("Case", secondary=collection_case)

class CaseComparison(Base):
    __tablename__ = "case_comparisons"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    title = Column(String, default="Comparative Intelligence")
    case_ids = Column(String) # JSON string of list of case ids
    research_question = Column(Text, nullable=True)
    comparison_result = Column(Text) # JSON string of result

class CaseCitation(Base):
    __tablename__ = "case_citations"
    id = Column(Integer, primary_key=True, index=True)
    source_case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    target_case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    target_case_name = Column(String, index=True)
    target_citation = Column(String, nullable=True)
    relationship_type = Column(String) # CITES, FOLLOWS, DISTINGUISHES, OVERRULES, etc.
    page_number = Column(Integer, nullable=True)
    source_chunk_id = Column(String, nullable=True)
    supporting_text = Column(Text)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    source_case = relationship("Case", foreign_keys=[source_case_id])
    target_case = relationship("Case", foreign_keys=[target_case_id])

class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String)
    research_question = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="sessions")
    
    cases = relationship("ResearchCase", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("ResearchEvidence", back_populates="session", cascade="all, delete-orphan")
    notes = relationship("ResearchNote", back_populates="session", cascade="all, delete-orphan")

class ResearchCase(Base):
    __tablename__ = "research_cases"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    case_id = Column(Integer, ForeignKey("cases.id"))
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    session = relationship("ResearchSession", back_populates="cases")
    case = relationship("Case")

class ResearchEvidence(Base):
    __tablename__ = "research_evidence"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    source_chunk_id = Column(String, nullable=True)
    category = Column(String) # FACT, ISSUE, PRINCIPLE, TIMELINE, etc
    supporting_text = Column(Text)
    page_number = Column(Integer, nullable=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    session = relationship("ResearchSession", back_populates="evidence")
    case = relationship("Case")

class ResearchNote(Base):
    __tablename__ = "research_notes"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    content = Column(Text)
    reference_case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    session = relationship("ResearchSession", back_populates="notes")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metadata_info = Column(String, nullable=True)


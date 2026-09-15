from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "researcher"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class CaseBase(BaseModel):
    case_name: str
    court: str
    year: int
    case_number: Optional[str] = None
    category: Optional[str] = None
    decision_date: Optional[datetime] = None
    
    # Intelligence fields
    executive_summary: Optional[str] = None
    facts: Optional[str] = None
    procedural_history: Optional[str] = None
    legal_issues: Optional[str] = None
    parties_arguments: Optional[str] = None
    court_reasoning: Optional[str] = None
    decision: Optional[str] = None
    remedy: Optional[str] = None

class CaseResponse(CaseBase):
    id: int
    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    title: str
    document_type: str

class DocumentResponse(DocumentBase):
    id: int
    case_id: int
    uploaded_at: datetime
    class Config:
        from_attributes = True

class CitationBase(BaseModel):
    citing_case_id: int
    cited_case_id: Optional[int] = None
    cited_case_name: Optional[str] = None
    context: Optional[str] = None
    relationship_type: str

class CitationResponse(CitationBase):
    id: int
    class Config:
        from_attributes = True

class LegalPrincipleBase(BaseModel):
    case_id: int
    description: str
    source_passage: Optional[str] = None

class LegalPrincipleResponse(LegalPrincipleBase):
    id: int
    class Config:
        from_attributes = True

class ResearchSessionBase(BaseModel):
    title: str = "New Research Session"

class ResearchSessionResponse(ResearchSessionBase):
    id: int
    user_id: int
    created_at: datetime
    last_active: datetime
    class Config:
        from_attributes = True

class ResearchQueryBase(BaseModel):
    query_text: str
    structured_intent: Optional[str] = None
    filters: Optional[str] = None

class ResearchQueryResponse(ResearchQueryBase):
    id: int
    session_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class BookmarkBase(BaseModel):
    case_id: int
    chunk_id: Optional[int] = None
    notes: Optional[str] = None

class BookmarkResponse(BookmarkBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class ResearchCollectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class ResearchCollectionResponse(ResearchCollectionBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None

class SearchResultItem(BaseModel):
    case_name: str
    court: str
    year: int
    page_number: int
    relevance_score: float
    semantic_score: float
    keyword_score: float
    matched_text: str
    reason: str

class ResearchRequest(BaseModel):
    query: str
    top_k: int = 8

class KeyFinding(BaseModel):
    finding: str
    sources: List[str]

class LegalPrincipleRAG(BaseModel):
    principle: str
    sources: List[str]

class Authority(BaseModel):
    case_name: str
    court: str
    year: int
    page: int
    source_id: str

class SourceData(BaseModel):
    source_id: str
    case_name: str
    court: str
    year: int
    document_id: Optional[int] = None
    page_number: int
    chunk_id: str
    matched_text: str

class ResearchResponse(BaseModel):
    query: str
    answer: str
    key_findings: List[KeyFinding]
    legal_principles: List[LegalPrincipleRAG]
    authorities: List[Authority]
    sources: List[SourceData]
    limitations: str

# ---------------------------------------------------------
# Phase 3 Lexora Intelligence Schemas
# ---------------------------------------------------------

class CaseFactSchema(BaseModel):
    id: Optional[int] = None
    fact_type: str
    description: str
    source_id: Optional[str] = None
    class Config:
        from_attributes = True

class LegalIssueSchema(BaseModel):
    id: Optional[int] = None
    issue_text: str
    class Config:
        from_attributes = True

class PartyArgumentSchema(BaseModel):
    id: Optional[int] = None
    party_type: str
    argument_text: str
    class Config:
        from_attributes = True

class CaseEventSchema(BaseModel):
    id: Optional[int] = None
    event_date: Optional[str] = None
    date_text: str
    date_precision: str
    event_type: str
    title: str
    description: str
    actors: Optional[str] = None
    court: Optional[str] = None
    timeline_type: str
    source_document_id: Optional[int] = None
    source_chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    supporting_text: str
    verification_status: str
    
    class Config:
        from_attributes = True

class TimelineResponse(BaseModel):
    case_id: int
    factual_events: List[CaseEventSchema]
    procedural_events: List[CaseEventSchema]
    events: List[CaseEventSchema]

class ImportantPassageSchema(BaseModel):
    id: Optional[int] = None
    category: str
    text: str
    page_number: Optional[int] = None
    class Config:
        from_attributes = True

class CaseIntelligenceResponse(BaseModel):
    id: int
    case_name: str
    case_number: Optional[str] = None
    court: str
    decision_date: Optional[datetime] = None
    executive_summary: Optional[str] = None
    facts: List[CaseFactSchema]
    issues: List[LegalIssueSchema]
    arguments: Dict[str, List[PartyArgumentSchema]] # {"Petitioner": [], "Respondent": []}
    court_reasoning: Optional[str] = None
    decision: Optional[str] = None
    principles: List[LegalPrincipleResponse]
    citations: List[CitationResponse]
    timeline: List[CaseEventSchema]
    important_passages: List[ImportantPassageSchema]
    analysis_status: str
    legal_topics: Optional[str] = None
    
    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Phase 4 Lexora Comparison Schemas
# ---------------------------------------------------------

class CompareRequest(BaseModel):
    case_ids: List[int]
    research_question: Optional[str] = None

class ComparisonClaim(BaseModel):
    claim: str
    sources: List[str] # List of source IDs

class ComparisonResponse(BaseModel):
    comparison_id: Optional[int] = None
    cases: List[CaseIntelligenceResponse]
    executive_comparison: str
    similarities: List[ComparisonClaim]
    differences: List[ComparisonClaim]
    distinguishing_factors: List[ComparisonClaim]
    reasoning_comparison: List[ComparisonClaim]
    principle_comparison: List[ComparisonClaim]
    outcome_comparison: List[ComparisonClaim]
    potential_tensions: List[ComparisonClaim]
    sources: List[SourceData]

# ---------------------------------------------------------
# Phase 5 Lexora Citation Graph Schemas
# ---------------------------------------------------------

class CaseCitationResponse(BaseModel):
    id: int
    source_case_id: int
    target_case_id: Optional[int] = None
    target_case_name: str
    target_citation: Optional[str] = None
    relationship_type: str
    page_number: Optional[int] = None
    source_chunk_id: Optional[str] = None
    supporting_text: str
    
    class Config:
        from_attributes = True

class GraphNode(BaseModel):
    id: str
    case_name: str
    court: Optional[str] = None
    year: Optional[int] = None
    indexed: bool = False

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    page: Optional[int] = None
    evidence: str

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# NOTE: CaseCitationResponse is defined above (lines 283-295). The duplicate
# definition that previously existed here has been removed in Phase 10.

# --- Research Session Schemas ---

class ResearchSessionCreate(BaseModel):
    title: str
    research_question: Optional[str] = None

class ResearchCaseCreate(BaseModel):
    case_id: int

class ResearchEvidenceCreate(BaseModel):
    case_id: Optional[int] = None
    source_chunk_id: Optional[str] = None
    category: str
    supporting_text: str
    page_number: Optional[int] = None

class ResearchNoteCreate(BaseModel):
    content: str
    reference_case_id: Optional[int] = None

class ResearchNoteSchema(BaseModel):
    id: int
    content: str
    reference_case_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ResearchEvidenceSchema(BaseModel):
    id: int
    case_id: Optional[int] = None
    source_chunk_id: Optional[str] = None
    category: str
    supporting_text: str
    page_number: Optional[int] = None
    added_at: datetime
    class Config:
        from_attributes = True

class ResearchCaseSchema(BaseModel):
    id: int
    case_id: int
    added_at: datetime
    case: CaseSchema
    class Config:
        from_attributes = True

class ResearchSessionSchema(BaseModel):
    id: int
    title: str
    research_question: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    cases: List[ResearchCaseSchema] = []
    evidence: List[ResearchEvidenceSchema] = []
    notes: List[ResearchNoteSchema] = []
    
    class Config:
        from_attributes = True


# ---------------------------------------------------------
# Phase 10 — Document Intelligence Schemas
# ---------------------------------------------------------

class DocumentListItem(BaseModel):
    id: int
    title: str
    original_filename: Optional[str] = None
    document_type: Optional[str] = None
    status: str
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    version_number: int = 1
    uploaded_at: Optional[datetime] = None
    case_id: Optional[int] = None
    # Injected from related Case
    case_name: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: int
    title: str
    status: str
    message: str
    job_id: Optional[int] = None
    duplicate_of: Optional[int] = None  # set if exact duplicate detected


class DocumentStatusResponse(BaseModel):
    document_id: int
    status: str
    progress: float          # 0–100
    current_stage: Optional[str] = None
    pages_processed: Optional[int] = None
    total_pages: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingLogEntry(BaseModel):
    stage: str
    status: str              # SUCCESS, FAILED, SKIPPED
    duration_ms: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class DocumentMetadataField(BaseModel):
    field_name: str
    field_value: Optional[str] = None
    confidence: float

    class Config:
        from_attributes = True


class DocumentSectionInfo(BaseModel):
    section_type: str
    confidence: float
    start_page: Optional[int] = None
    end_page: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    id: int
    title: str
    original_filename: Optional[str] = None
    document_type: Optional[str] = None
    status: str
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    ocr_required: bool = False
    version_number: int = 1
    parent_document_id: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    case_id: Optional[int] = None
    case_name: Optional[str] = None
    # Extracted intelligence
    metadata_fields: List[DocumentMetadataField] = []
    sections: List[DocumentSectionInfo] = []
    processing_logs: List[ProcessingLogEntry] = []

    class Config:
        from_attributes = True


class DocumentPageResponse(BaseModel):
    page_number: int
    text: Optional[str] = None
    word_count: int = 0
    has_text: bool = True
    section: Optional[str] = None  # detected section for this page

    class Config:
        from_attributes = True


class DocumentSearchResult(BaseModel):
    page_number: int
    text_snippet: str         # surrounding context for the match
    match_count: int = 1


class DocumentVersionItem(BaseModel):
    id: int
    version_number: int
    uploaded_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True

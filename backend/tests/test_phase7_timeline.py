import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app import app
from backend.database import SessionLocal
from backend.models.domain import User, Case, CaseEvent, Document, DocumentChunk
from backend.security import create_access_token, get_password_hash
from backend.services.timeline_service import (
    parse_date_expression,
    validate_date_grounding,
    distinguish_from_judgment_date,
    resolve_relative_date,
    detect_attribution,
    deduplicate_timeline_events,
    sort_timeline_events,
    get_case_timeline_data
)

client = TestClient(app)

@pytest.fixture
def db_session():
    """Provides a transactional database session for unit tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_users(db_session: Session):
    """Creates a regular researcher and an admin user."""
    researcher = db_session.query(User).filter(User.email == "p7_researcher@lexora.ai").first()
    if not researcher:
        researcher = User(
            email="p7_researcher@lexora.ai",
            password_hash=get_password_hash("Pass123!"),
            full_name="P7 Researcher",
            role="RESEARCHER",
            is_active=True
        )
        db_session.add(researcher)

    other_user = db_session.query(User).filter(User.email == "p7_other@lexora.ai").first()
    if not other_user:
        other_user = User(
            email="p7_other@lexora.ai",
            password_hash=get_password_hash("Pass123!"),
            full_name="P7 Other User",
            role="RESEARCHER",
            is_active=True
        )
        db_session.add(other_user)

    admin = db_session.query(User).filter(User.email == "p7_admin@lexora.ai").first()
    if not admin:
        admin = User(
            email="p7_admin@lexora.ai",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="P7 Admin",
            role="ADMIN",
            is_active=True
        )
        db_session.add(admin)

    db_session.commit()
    db_session.refresh(researcher)
    db_session.refresh(other_user)
    db_session.refresh(admin)

    return {
        "researcher": researcher,
        "token_researcher": create_access_token({"sub": researcher.email, "role": researcher.role, "user_id": researcher.id}),
        "other_user": other_user,
        "token_other": create_access_token({"sub": other_user.email, "role": other_user.role, "user_id": other_user.id}),
        "admin": admin,
        "token_admin": create_access_token({"sub": admin.email, "role": admin.role, "user_id": admin.id}),
    }


# =============================================================================
# 1. Exact Date Extraction
# =============================================================================
def test_exact_date_extraction():
    """Verifies that explicit calendar dates are parsed into ISO YYYY-MM-DD with exact precision."""
    test_cases = [
        ("15 May 2024", "2024-05-15"),
        ("15th May, 2024", "2024-05-15"),
        ("2024-05-15", "2024-05-15"),
        ("12/08/2019", "2019-08-12"),
        ("October 5, 2021", "2021-10-05")
    ]
    for raw_str, expected_iso in test_cases:
        event_date, date_text, precision, start_d, end_d = parse_date_expression(raw_str)
        assert precision == "exact"
        assert event_date == expected_iso
        assert date_text == raw_str
        assert start_d is None
        assert end_d is None


# =============================================================================
# 2. Approximate Date Extraction
# =============================================================================
def test_approximate_date_extraction():
    """Verifies that approximate phrases never manufacture an exact calendar day."""
    approx_samples = [
        "around March 2022",
        "circa 2015",
        "in or about July 2018",
        "in early 2020",
        "mid-2019",
        "late 2021",
        "sometime in 2016",
        "in the year 2018"
    ]
    for expr in approx_samples:
        event_date, date_text, precision, start_d, end_d = parse_date_expression(expr)
        assert precision == "approximate"
        assert event_date is None, f"Approximate phrase '{expr}' must not produce an exact event_date"
        assert date_text == expr


# =============================================================================
# 3. Date-Range Extraction
# =============================================================================
def test_date_range_extraction():
    """Verifies that temporal intervals are recognized as RANGE with start and end markers."""
    # Range 1: between years
    e_date, d_text, prec, s_date, e_date_val = parse_date_expression("between 2018 and 2020")
    assert prec == "range"
    assert e_date is None
    assert s_date == "2018"
    assert e_date_val == "2020"

    # Range 2: during period
    e_date, d_text, prec, s_date, e_date_val = parse_date_expression("during the period 2015-2017")
    assert prec == "range"
    assert s_date == "2015"
    assert e_date_val == "2017"

    # Range 3: from exact date to exact date
    e_date, d_text, prec, s_date, e_date_val = parse_date_expression("from 12 January 2019 to 15 March 2019")
    assert prec == "range"
    assert s_date == "2019-01-12"
    assert e_date_val == "2019-03-15"


# =============================================================================
# 4. Unknown Dates and Relative Expressions
# =============================================================================
def test_unknown_dates_and_relative_expressions():
    """Verifies relative expressions are classified as UNKNOWN without manufactured dates."""
    relative_phrases = [
        "several years later",
        "subsequently",
        "thereafter",
        "at all material times",
        "at a later stage",
        "shortly afterwards"
    ]
    for rel in relative_phrases:
        event_date, date_text, precision, _, _ = parse_date_expression(rel)
        assert precision == "unknown"
        assert event_date is None
        assert date_text == rel


# =============================================================================
# 5. Distinguishing Event Dates from Judgment Dates
# =============================================================================
def test_distinguishing_event_dates_from_judgment_dates():
    """Verifies that underlying substantive events (tender/contract) are not conflated with judgment delivery."""
    judgment_date = "2024-05-15"

    # Substantive contract event mistakenly assigned the judgment delivery date
    contract_passage = "The parties entered into an agreement for supply of materials."
    val_date, val_text, status = distinguish_from_judgment_date(
        event_date="2024-05-15",
        date_text="15 May 2024",
        event_type="CONTRACT",
        judgment_date_str=judgment_date,
        supporting_text=contract_passage
    )
    # Must flag the conflation and clear the date
    assert val_date is None
    assert status == "unsupported"

    # Legitimate judgment event matching the delivery date
    judgment_passage = "The bench pronounced this final judgment and disposed of the petition on 15 May 2024."
    val_date, val_text, status = distinguish_from_judgment_date(
        event_date="2024-05-15",
        date_text="15 May 2024",
        event_type="JUDGMENT",
        judgment_date_str=judgment_date,
        supporting_text=judgment_passage
    )
    assert val_date == "2024-05-15"
    assert status == "verified"


# =============================================================================
# 6. Unsupported LLM-Generated Dates
# =============================================================================
def test_unsupported_llm_generated_dates():
    """Verifies that dates invented by LLMs without passage grounding are demoted or rejected."""
    # Case A: Passage only says 'around March 2022', but LLM generated '2022-03-01' as exact
    passage_approx = "The dispute arose around March 2022 when payments were delayed."
    v_date, v_text, v_prec, v_status = validate_date_grounding(
        event_date="2022-03-01",
        date_text="1 March 2022",
        date_precision="exact",
        supporting_text=passage_approx
    )
    assert v_prec == "approximate"
    assert v_date is None
    assert v_status == "demoted_to_approximate"

    # Case B: LLM completely hallucinates a date (2021-07-14) that doesn't exist in the passage
    passage_unrelated = "The claimant filed an arbitration application without specifying calendar terms."
    v_date, v_text, v_prec, v_status = validate_date_grounding(
        event_date="2021-07-14",
        date_text="14 July 2021",
        date_precision="exact",
        supporting_text=passage_unrelated
    )
    assert v_prec == "unknown"
    assert v_date is None
    assert v_status == "unsupported"


# =============================================================================
# 7. Allegations Versus Established Facts
# =============================================================================
def test_allegations_versus_established_facts():
    """Verifies that party claims and allegations are not silently promoted to established facts."""
    # Allegation 1: Contention of party
    is_alleg, status = detect_attribution(
        title="Payment default",
        description="The petitioner alleged that payments were withheld intentionally.",
        supporting_text="It was alleged by the appellant that the respondent committed fraud."
    )
    assert is_alleg is True
    assert status in ["ALLEGATION", "DISPUTED"]

    # Allegation 2: Disputed claim
    is_alleg, status = detect_attribution(
        title="Notice receipt",
        description="Respondent disputed receipt of the termination notice.",
        supporting_text="The respondent contended that no notice was ever served."
    )
    assert is_alleg is True
    assert status in ["ALLEGATION", "DISPUTED"]

    # Established fact
    is_alleg, status = detect_attribution(
        title="Tender executed",
        description="Both parties signed the concession agreement under Section 74.",
        supporting_text="The agreement was signed and deposited before the registry."
    )
    assert is_alleg is False
    assert status == "ESTABLISHED"


# =============================================================================
# 8. Deduplication Across Overlapping Chunks
# =============================================================================
def test_deduplication_across_overlapping_chunks():
    """Verifies that duplicated events across boundary chunks are merged without losing citations."""
    events_raw = [
        {
            "timeline_type": "FACTUAL",
            "event_date": "2019-01-15",
            "date_text": "15 January 2019",
            "title": "Legal Notice Issued",
            "description": "Claimant served notice demanding arbitration.",
            "source_chunk_id": "chunk_001",
            "page_number": 3,
            "supporting_text": "On 15 January 2019, claimant issued notice."
        },
        {
            "timeline_type": "FACTUAL",
            "event_date": "2019-01-15",
            "date_text": "15 January 2019",
            "title": "Legal Notice Issued",
            "description": "Claimant served notice demanding arbitration.",
            "source_chunk_id": "chunk_002", # Overlapping chunk
            "page_number": 3,
            "supporting_text": "claimant issued notice demanding arbitration under Clause 25."
        },
        {
            "timeline_type": "PROCEDURAL",
            "event_date": "2020-04-10",
            "date_text": "10 April 2020",
            "title": "Section 11 Petition",
            "description": "High Court petition filed.",
            "source_chunk_id": "chunk_005",
            "page_number": 8,
            "supporting_text": "Filed petition on 10 April 2020."
        }
    ]

    deduped = deduplicate_timeline_events(events_raw)
    assert len(deduped) == 2, "Expected duplicate notice event from chunk_002 to be merged with chunk_001"
    
    notice_event = [e for e in deduped if "Legal Notice" in e["title"]][0]
    assert "chunk_001" in notice_event["source_chunk_id"]
    assert "chunk_002" in notice_event["source_chunk_id"]
    assert "Clause 25" in notice_event["supporting_text"]


# =============================================================================
# 9. Source and Page Metadata Preservation
# =============================================================================
def test_source_and_page_metadata_preservation(db_session: Session):
    """Verifies that all source metadata (page, chunk, doc_id) is preserved on CaseEvent records."""
    test_case = Case(case_name="Metadata Test Case", court="Supreme Court", year=2023)
    db_session.add(test_case)
    db_session.commit()
    db_session.refresh(test_case)

    event = CaseEvent(
        case_id=test_case.id,
        event_date="2021-09-20",
        date_text="20 September 2021",
        date_precision="exact",
        event_type="NOTICE",
        title="Arbitration Notice",
        description="Formal demand for arbitrator appointment.",
        timeline_type="PROCEDURAL",
        source_document_id=101,
        source_chunk_id="doc_101_chunk_4",
        page_number=14,
        supporting_text="Passed on 20 September 2021 at page 14.",
        verification_status="verified",
        confidence=0.98,
        is_allegation=False,
        attribution_status="ESTABLISHED"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    fetched = db_session.query(CaseEvent).filter(CaseEvent.id == event.id).first()
    assert fetched.source_document_id == 101
    assert fetched.source_chunk_id == "doc_101_chunk_4"
    assert fetched.page_number == 14
    assert fetched.confidence == 0.98
    assert fetched.attribution_status == "ESTABLISHED"
    assert fetched.is_allegation is False


# =============================================================================
# 10. Chronological Sorting with Mixed Date Precision
# =============================================================================
def test_chronological_sorting_with_mixed_precision():
    """Verifies that dated events sort chronologically while undated events are partitioned without false sequence."""
    events = [
        {"title": "Event 2023", "event_date": "2023-01-10", "date_text": "10 Jan 2023", "date_precision": "exact"},
        {"title": "Undated Event 1", "event_date": None, "date_text": "several years later", "date_precision": "unknown"},
        {"title": "Event 2018", "event_date": "2018-05-12", "date_text": "12 May 2018", "date_precision": "exact"},
        {"title": "Approx 2020", "event_date": None, "date_text": "around March 2020", "date_precision": "approximate"},
        {"title": "Undated Event 2", "event_date": None, "date_text": "subsequently", "date_precision": "unknown"},
    ]

    dated, undated = sort_timeline_events(events)

    # 1. Dated events must be sorted chronologically
    dated_titles = [e["title"] for e in dated]
    assert dated_titles == ["Event 2018", "Approx 2020", "Event 2023"]

    # 2. Undated events must be partitioned into undated list
    undated_titles = [e["title"] for e in undated]
    assert len(undated_titles) == 2
    assert "Undated Event 1" in undated_titles
    assert "Undated Event 2" in undated_titles


# =============================================================================
# 11. Existing Timeline Endpoint Compatibility & Authorization
# =============================================================================
def test_timeline_endpoint_compatibility_and_auth(db_session: Session, test_users):
    """Verifies GET /api/cases/{case_id}/timeline returns compliant schema and rejects unauthorized private cases."""
    # 1. Create a public case with events
    pub_case = Case(case_name="Public Timeline Case", court="High Court of Delhi", year=2021)
    db_session.add(pub_case)
    db_session.commit()
    db_session.refresh(pub_case)

    ev1 = CaseEvent(
        case_id=pub_case.id,
        event_date="2020-02-01",
        date_text="1 February 2020",
        date_precision="exact",
        event_type="CONTRACT",
        title="Lease signed",
        description="Lease agreement executed.",
        timeline_type="FACTUAL",
        supporting_text="Agreement executed on 1 February 2020."
    )
    ev2 = CaseEvent(
        case_id=pub_case.id,
        event_date="2021-03-15",
        date_text="15 March 2021",
        date_precision="exact",
        event_type="JUDGMENT",
        title="High Court Order",
        description="Order passed.",
        timeline_type="PROCEDURAL",
        supporting_text="Order passed on 15 March 2021."
    )
    db_session.add(ev1)
    db_session.add(ev2)
    db_session.commit()

    token = test_users["token_researcher"]
    resp = client.get(f"/api/cases/{pub_case.id}/timeline", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["case_id"] == pub_case.id
    assert len(data["factual_events"]) == 1
    assert data["factual_events"][0]["title"] == "Lease signed"
    assert len(data["procedural_events"]) == 1
    assert data["procedural_events"][0]["title"] == "High Court Order"
    assert len(data["events"]) == 2

    # 2. Authorization check on private document case
    priv_case = Case(case_name="Private Case", court="Bombay High Court", year=2022)
    db_session.add(priv_case)
    db_session.commit()
    db_session.refresh(priv_case)

    priv_doc = Document(
        title="Private Judgment",
        original_filename="priv.pdf",
        file_path="/tmp/priv.pdf",
        owner_id=test_users["other_user"].id, # Owned by other user
        case_id=priv_case.id
    )
    db_session.add(priv_doc)
    db_session.commit()

    # Researcher attempts to access other user's private case timeline -> 404
    resp_unauth = client.get(f"/api/cases/{priv_case.id}/timeline", headers={"Authorization": f"Bearer {token}"})
    assert resp_unauth.status_code == 404

    # Admin access -> allowed
    token_admin = test_users["token_admin"]
    resp_admin = client.get(f"/api/cases/{priv_case.id}/timeline", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin.status_code == 200


# =============================================================================
# 12. Empty Timelines and Missing Cases
# =============================================================================
def test_empty_timelines_and_missing_cases(db_session: Session, test_users):
    """Verifies that cases with no events return empty lists and missing cases return 404."""
    empty_case = Case(case_name="Empty Timeline Case", court="Supreme Court", year=2024)
    db_session.add(empty_case)
    db_session.commit()
    db_session.refresh(empty_case)

    token = test_users["token_researcher"]
    resp = client.get(f"/api/cases/{empty_case.id}/timeline", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["case_id"] == empty_case.id
    assert data["factual_events"] == []
    assert data["procedural_events"] == []
    assert data["events"] == []

    # Nonexistent case
    resp_missing = client.get("/api/cases/9999999/timeline", headers={"Authorization": f"Bearer {token}"})
    assert resp_missing.status_code == 404
    assert resp_missing.json()["detail"] == "Case not found"

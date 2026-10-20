import pytest
import json
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal
from backend.models.domain import Case, User, LegalPrinciple
from backend.services.precedent_service import process_case_intelligence

client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    # Register/login a user to get auth token
    user_email = "phase3_test_user@lexora.ai"
    user_pass = "securepass123"
    
    reg_resp = client.post("/api/auth/register", json={
        "email": user_email,
        "password": user_pass,
        "full_name": "Phase 3 Tester"
    })
    
    login_resp = client.post("/api/auth/login", data={
        "username": user_email,
        "password": user_pass
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def sample_case():
    db = SessionLocal()
    case = db.query(Case).filter(Case.case_name == "Phase 3 Benchmark Authority").first()
    if not case:
        case = Case(
            case_name="Phase 3 Benchmark Authority",
            court="Supreme Court of India",
            year=2024,
            case_number="CA 9999/2024",
            category="Constitutional Law",
            analysis_status="PENDING"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
    case_id = case.id
    db.close()
    return case_id

# ---------------------------------------------------------------------------
# 1. Disambiguated Research Routes
# ---------------------------------------------------------------------------

def test_research_session_creation_and_listing(auth_headers):
    # Test POST /api/research (session creation)
    create_resp = client.post(
        "/api/research",
        json={"title": "Contractual Breach Research", "research_question": "What is the standard for anticipatory breach?"},
        headers=auth_headers
    )
    assert create_resp.status_code == 200
    session_data = create_resp.json()
    assert "id" in session_data
    assert session_data["title"] == "Contractual Breach Research"
    assert session_data["research_question"] == "What is the standard for anticipatory breach?"
    assert "cases" in session_data
    assert "evidence" in session_data
    assert "notes" in session_data
    # Verify research session endpoint does NOT invoke RAG (no RAG answer or sources payload)
    assert "answer" not in session_data
    assert "key_findings" not in session_data

    # Test GET /api/research (list sessions)
    list_resp = client.get("/api/research", headers=auth_headers)
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert isinstance(sessions, list)
    assert any(s["id"] == session_data["id"] for s in sessions)

    # Test GET /api/research/ with trailing slash (no redirect error)
    list_slash_resp = client.get("/api/research/", headers=auth_headers)
    assert list_slash_resp.status_code == 200
    assert isinstance(list_slash_resp.json(), list)

def test_rag_question_answering_endpoint(monkeypatch):
    # Mock RAG response
    mock_rag_result = {
        "query": "What is res judicata?",
        "answer": "Res judicata prevents re-litigation of issues already decided between the same parties.",
        "key_findings": [{"finding": "Issue must be directly in issue in former suit", "sources": ["src_1"]}],
        "legal_principles": [{"principle": "Finality of judicial decisions", "sources": ["src_1"]}],
        "authorities": [{"case_name": "State of UP v Nawab Hussain", "court": "Supreme Court", "year": 1977, "page": 1, "source_id": "src_1"}],
        "sources": [{"source_id": "src_1", "case_name": "State of UP v Nawab Hussain", "court": "Supreme Court", "year": 1977, "document_id": 1, "page_number": 1, "chunk_id": "c1", "matched_text": "Res judicata applies"}],
        "limitations": "Strictly based on supplied judgments"
    }

    monkeypatch.setattr("backend.routes.api.ask_legal_question", lambda query, top_k: mock_rag_result)

    # Dedicated RAG endpoint: POST /api/research/ask
    ask_resp = client.post("/api/research/ask", json={"query": "What is res judicata?", "top_k": 5})
    assert ask_resp.status_code == 200
    ask_data = ask_resp.json()
    assert ask_data["answer"] == mock_rag_result["answer"]
    assert len(ask_data["key_findings"]) == 1
    assert len(ask_data["sources"]) == 1

    # Compatibility alias: POST /api/rag/ask
    alias_resp = client.post("/api/rag/ask", json={"query": "What is res judicata?", "top_k": 5})
    assert alias_resp.status_code == 200
    assert alias_resp.json()["answer"] == mock_rag_result["answer"]

    # Empty query validation
    bad_resp = client.post("/api/research/ask", json={"query": "  "})
    assert bad_resp.status_code == 400

# ---------------------------------------------------------------------------
# 2. Case Intelligence Routes & 404 Validation
# ---------------------------------------------------------------------------

def test_case_intelligence_existing_case(auth_headers, sample_case):
    # GET /api/cases/{case_id}
    resp = client.get(f"/api/cases/{sample_case}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sample_case
    assert data["case_name"] == "Phase 3 Benchmark Authority"
    assert "arguments" in data
    assert "Petitioner" in data["arguments"]
    assert "Respondent" in data["arguments"]
    assert "principles" in data
    assert "timeline" in data

    # GET /api/cases/{case_id}/timeline
    timeline_resp = client.get(f"/api/cases/{sample_case}/timeline", headers=auth_headers)
    assert timeline_resp.status_code == 200
    t_data = timeline_resp.json()
    assert t_data["case_id"] == sample_case
    assert "factual_events" in t_data
    assert "procedural_events" in t_data
    assert "events" in t_data

    # GET /api/cases/{case_id}/citations
    cit_resp = client.get(f"/api/cases/{sample_case}/citations", headers=auth_headers)
    assert cit_resp.status_code == 200
    c_data = cit_resp.json()
    assert c_data["case_id"] == sample_case
    assert "outgoing" in c_data
    assert "incoming" in c_data

    # GET /api/cases/{case_id}/graph
    graph_resp = client.get(f"/api/cases/{sample_case}/graph?depth=1", headers=auth_headers)
    assert graph_resp.status_code == 200
    g_data = graph_resp.json()
    assert "nodes" in g_data
    assert "edges" in g_data

def test_case_intelligence_nonexistent_case(auth_headers):
    nonexistent_id = 9999999

    # Detail 404
    resp = client.get(f"/api/cases/{nonexistent_id}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case not found"

    # Analyze 404
    resp_analyze = client.post(f"/api/cases/{nonexistent_id}/analyze", headers=auth_headers)
    assert resp_analyze.status_code == 404
    assert resp_analyze.json()["detail"] == "Case not found"

    # Timeline 404
    resp_timeline = client.get(f"/api/cases/{nonexistent_id}/timeline", headers=auth_headers)
    assert resp_timeline.status_code == 404
    assert resp_timeline.json()["detail"] == "Case not found"

    # Citations 404
    resp_cit = client.get(f"/api/cases/{nonexistent_id}/citations", headers=auth_headers)
    assert resp_cit.status_code == 404
    assert resp_cit.json()["detail"] == "Case not found"

    # Graph 404
    resp_graph = client.get(f"/api/cases/{nonexistent_id}/graph", headers=auth_headers)
    assert resp_graph.status_code == 404
    assert resp_graph.json()["detail"] == "Case not found"

def test_case_graph_invalid_depth(auth_headers, sample_case):
    # Depth must be >= 1
    resp = client.get(f"/api/cases/{sample_case}/graph?depth=0", headers=auth_headers)
    assert resp.status_code == 400
    assert "Depth must be at least 1" in resp.json()["detail"]

# ---------------------------------------------------------------------------
# 3. Case Comparison Integration
# ---------------------------------------------------------------------------

def test_compare_cases_validation(auth_headers):
    # Fewer than 2 cases
    resp_under = client.post("/api/compare", json={"case_ids": [1]}, headers=auth_headers)
    assert resp_under.status_code == 400
    assert "between 2 and 5" in resp_under.json()["detail"]

    # More than 5 cases
    resp_over = client.post("/api/compare", json={"case_ids": [1, 2, 3, 4, 5, 6]}, headers=auth_headers)
    assert resp_over.status_code == 400
    assert "between 2 and 5" in resp_over.json()["detail"]

    # Nonexistent case IDs in comparison
    resp_missing = client.post("/api/compare", json={"case_ids": [8888888, 9999999]}, headers=auth_headers)
    assert resp_missing.status_code == 400
    assert "One or more cases could not be found" in resp_missing.json()["detail"]

def test_compare_cases_success_and_trailing_slash(auth_headers, monkeypatch):
    # Create two benchmark cases in DB
    db = SessionLocal()
    c1 = db.query(Case).filter(Case.case_name == "Compare Authority 1").first()
    if not c1:
        c1 = Case(case_name="Compare Authority 1", court="SC", year=2021)
        db.add(c1)
    c2 = db.query(Case).filter(Case.case_name == "Compare Authority 2").first()
    if not c2:
        c2 = Case(case_name="Compare Authority 2", court="SC", year=2023)
        db.add(c2)
    db.commit()
    db.refresh(c1)
    db.refresh(c2)
    c1_id, c2_id = c1.id, c2.id
    db.close()

    mock_comparison = {
        "executive_comparison": "Synthesized comparison between authorities.",
        "similarities": [{"claim": "Both address contractual frustration", "sources": [f"case_{c1_id}", f"case_{c2_id}"]}] ,
        "differences": [{"claim": "Remedy differed based on causation", "sources": [f"case_{c1_id}"]}] ,
        "distinguishing_factors": [],
        "reasoning_comparison": [],
        "principle_comparison": [],
        "outcome_comparison": [],
        "potential_tensions": [],
        "sources": []
    }

    class MockModel:
        def generate_content(self, *args, **kwargs):
            class Resp:
                text = json.dumps(mock_comparison)
            return Resp()

    monkeypatch.setattr("backend.services.compare_service.model", MockModel())

    # POST /api/compare
    resp = client.post(
        "/api/compare",
        json={"case_ids": [c1_id, c2_id], "research_question": "Do these authorities conflict?"},
        headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["executive_comparison"] == mock_comparison["executive_comparison"]
    assert len(data["cases"]) == 2
    assert "comparison_id" in data

    # POST /api/compare/ (trailing slash, no redirect)
    resp_slash = client.post(
        "/api/compare/",
        json={"case_ids": [c1_id, c2_id], "research_question": "Do these authorities conflict?"},
        headers=auth_headers
    )
    assert resp_slash.status_code == 200
    assert resp_slash.json()["executive_comparison"] == mock_comparison["executive_comparison"]

# ---------------------------------------------------------------------------
# 4. Precedent Service Persistence & ORM Safety
# ---------------------------------------------------------------------------

def test_precedent_service_safe_orm_updates():
    db = SessionLocal()
    case = Case(
        case_name="Precedent Integrity Test Case",
        court="Delhi High Court",
        year=2022,
        analysis_status="PENDING"
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    intelligence_payload = {
        "executive_summary": "High Court ruling on statutory injunctions.",
        "facts": "Plaintiff sought injunction against patent infringement.",
        "issues": "Whether prima facie case and balance of convenience were established.",
        "procedural_history": "Appealed from single-judge interim injunction order.",
        "court_reasoning": "Interim injunction standard was satisfied.",
        "decision": "Appeal dismissed.",
        "remedy": "Interim injunction sustained.",
        "category": "Intellectual Property",
        "legal_principles": [
            {
                "principle_name": "Triple Test for Injunction",
                "description": "Prima facie case, irreparable injury, and balance of convenience must co-exist."
            }
        ]
    }

    # Process intelligence with explicit payload
    success = process_case_intelligence(db, case.id, intelligence=intelligence_payload)
    assert success is True

    # Re-query and verify scalar fields and ORM relationships
    db.expire_all()
    updated_case = db.query(Case).filter(Case.id == case.id).first()

    # Scalar fields populated correctly (not assigned to relationships)
    assert updated_case.executive_summary == "High Court ruling on statutory injunctions."
    assert updated_case.facts_summary == "Plaintiff sought injunction against patent infringement."
    assert updated_case.legal_issues_summary == "Whether prima facie case and balance of convenience were established."
    assert updated_case.procedural_history == "Appealed from single-judge interim injunction order."
    assert updated_case.court_reasoning == "Interim injunction standard was satisfied."
    assert updated_case.decision == "Appeal dismissed."
    assert updated_case.remedy == "Interim injunction sustained."
    assert updated_case.category == "Intellectual Property"

    # ORM relationships remain safe collections, NOT overwritten by strings
    assert isinstance(updated_case.facts, list)
    assert isinstance(updated_case.legal_issues, list)

    # LegalPrinciple ORM objects properly persisted and linked
    assert len(updated_case.principles) == 1
    principle = updated_case.principles[0]
    assert isinstance(principle, LegalPrinciple)
    assert principle.case_id == case.id
    assert "Triple Test for Injunction" in principle.description

    db.close()

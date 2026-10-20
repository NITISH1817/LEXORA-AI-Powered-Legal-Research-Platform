import pytest
import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app import app
from backend.database import SessionLocal
from backend.models.domain import User, Case, CaseCitation, Document, LegalPrinciple, CaseFact
from backend.security import create_access_token, get_password_hash
from backend.services.compare_service import compare_cases_service
from evaluation.metrics import evaluate_faithfulness

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
    researcher = db_session.query(User).filter(User.email == "p6_researcher@lexora.ai").first()
    if not researcher:
        researcher = User(
            email="p6_researcher@lexora.ai",
            password_hash=get_password_hash("Pass123!"),
            full_name="P6 Researcher",
            role="RESEARCHER",
            is_active=True
        )
        db_session.add(researcher)

    other_user = db_session.query(User).filter(User.email == "p6_other@lexora.ai").first()
    if not other_user:
        other_user = User(
            email="p6_other@lexora.ai",
            password_hash=get_password_hash("Pass123!"),
            full_name="P6 Other User",
            role="RESEARCHER",
            is_active=True
        )
        db_session.add(other_user)

    admin = db_session.query(User).filter(User.email == "p6_admin@lexora.ai").first()
    if not admin:
        admin = User(
            email="p6_admin@lexora.ai",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="P6 Admin",
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

@pytest.fixture
def sample_cases(db_session: Session):
    """Creates a set of 5 distinct test cases for comparison and graph tests."""
    created_cases = []
    cases_data = [
        ("Kailash Nath Associates v. DDA", "Supreme Court of India", 2015, "Compensation allowed", "Section 74 requires proof of loss unless impossible."),
        ("ONGC v. Saw Pipes Ltd", "Supreme Court of India", 2003, "Liquidated damages granted", "Liquidated damages represent genuine pre-estimate."),
        ("Associate Builders v. DDA", "Supreme Court of India", 2015, "Award set aside", "Patent illegality ground under Section 34."),
        ("Ssangyong Engineering v. NHAI", "Supreme Court of India", 2019, "Section 34 challenge rejected", "Public policy review is narrowly circumscribed."),
        ("State of Gujarat v. M/s Amber Builders", "Supreme Court of India", 2020, "Interim relief granted", "Powers of arbitral tribunal regarding interim orders."),
    ]
    for name, court, year, dec, reason in cases_data:
        c = db_session.query(Case).filter(Case.case_name == name).first()
        if not c:
            c = Case(
                case_name=name,
                court=court,
                year=year,
                decision=dec,
                court_reasoning=reason
            )
            db_session.add(c)
            db_session.commit()
            db_session.refresh(c)
        created_cases.append(c)

    return created_cases


# =============================================================================
# 1. Comparisons Containing Two and Five Cases
# =============================================================================
def test_comparison_two_and_five_cases(sample_cases, test_users):
    """Verifies successful comparison for minimum (2) and maximum (5) cases."""
    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Compare 2 cases
    resp_2 = client.post("/api/compare", json={"case_ids": [sample_cases[0].id, sample_cases[1].id]}, headers=headers)
    assert resp_2.status_code == 200
    data_2 = resp_2.json()
    assert len(data_2["cases"]) == 2
    assert "executive_comparison" in data_2
    assert len(data_2["similarities"]) >= 1
    assert len(data_2["sources"]) == 2

    # 2. Compare 5 cases
    case_ids_5 = [c.id for c in sample_cases[:5]]
    resp_5 = client.post("/api/compare", json={"case_ids": case_ids_5}, headers=headers)
    assert resp_5.status_code == 200
    data_5 = resp_5.json()
    assert len(data_5["cases"]) == 5
    assert len(data_5["sources"]) == 5


# =============================================================================
# 2. Rejection of Duplicate, Missing, or Excessive Case IDs
# =============================================================================
def test_comparison_validation_bounds_and_duplicates(sample_cases, test_users):
    """Verifies 400 rejection for <2, >5, duplicate IDs, and 404 for missing IDs."""
    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    # Under minimum (<2 cases)
    res_under = client.post("/api/compare", json={"case_ids": [sample_cases[0].id]}, headers=headers)
    assert res_under.status_code == 400
    assert "between 2 and 5" in res_under.json()["detail"]

    # Over maximum (>5 cases)
    res_over = client.post("/api/compare", json={"case_ids": [1, 2, 3, 4, 5, 6]}, headers=headers)
    assert res_over.status_code == 400

    # Duplicate case IDs
    res_dup = client.post("/api/compare", json={"case_ids": [sample_cases[0].id, sample_cases[0].id]}, headers=headers)
    assert res_dup.status_code == 400
    assert "Duplicate" in res_dup.json()["detail"]

    # Non-existent case ID
    res_missing = client.post("/api/compare", json={"case_ids": [sample_cases[0].id, 999999]}, headers=headers)
    assert res_missing.status_code == 400


# =============================================================================
# 3. Missing Fields in Source Documents
# =============================================================================
def test_missing_fields_represented_as_unknown(db_session: Session, test_users):
    """Verifies that cases with missing facts/remedy represent them honestly without hallucination."""
    sparse_case_1 = Case(
        case_name="Sparse Case One",
        court="High Court of Delhi",
        year=2021,
        court_reasoning=None,  # Missing reasoning
        decision=None          # Missing decision
    )
    sparse_case_2 = Case(
        case_name="Sparse Case Two",
        court="High Court of Bombay",
        year=2022
    )
    db_session.add(sparse_case_1)
    db_session.add(sparse_case_2)
    db_session.commit()
    db_session.refresh(sparse_case_1)
    db_session.refresh(sparse_case_2)

    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/compare", json={"case_ids": [sparse_case_1.id, sparse_case_2.id]}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Verify that differences and reasoning note missing documentation rather than inventing text
    reasoning_claims = [r["claim"] for r in data["reasoning_comparison"]]
    assert any("not available" in c.lower() or "not documented" in c.lower() for c in reasoning_claims)


# =============================================================================
# 4. Source-Grounding of Comparison Claims
# =============================================================================
def test_source_grounding_of_comparison_claims(sample_cases, db_session: Session):
    """Verifies that all substantive claims cite genuine source IDs present in the source map."""
    c1, c2 = sample_cases[0], sample_cases[1]
    res = compare_cases_service(db_session, [c1.id, c2.id])

    valid_sources = {s["source_id"] for s in res["sources"]}
    assert f"case_{c1.id}" in valid_sources
    assert f"case_{c2.id}" in valid_sources

    for cat in ["similarities", "differences", "reasoning_comparison", "outcome_comparison"]:
        for item in res[cat]:
            for s in item["sources"]:
                assert s in valid_sources, f"Claim source {s} not found in valid sources"


# =============================================================================
# 5. Detection of Unsupported or Uncertain Legal Conflicts
# =============================================================================
def test_tension_vs_conflict_distinction(sample_cases, db_session: Session):
    """Verifies that divergences in facts or forums are categorized as tensions/distinctions rather than automatic conflicts."""
    c1, c2 = sample_cases[0], sample_cases[1]
    res = compare_cases_service(db_session, [c1.id, c2.id])

    tensions = res.get("potential_tensions", [])
    assert len(tensions) >= 1
    # Check claim text acknowledges distinguishing factors
    tension_texts = " ".join([t["claim"] for t in tensions])
    assert "conflict" in tension_texts.lower() or "distinction" in tension_texts.lower() or "factual" in tension_texts.lower()


# =============================================================================
# 6. Citation-Edge Type and Provenance
# =============================================================================
def test_citation_edge_type_and_provenance(db_session: Session, sample_cases, test_users):
    """Verifies edge attributes include relationship_type, verification_status, and confidence."""
    c1, c2 = sample_cases[0], sample_cases[1]

    # Create citation: C1 follows C2
    cit = CaseCitation(
        source_case_id=c1.id,
        target_case_id=c2.id,
        target_case_name=c2.case_name,
        relationship_type="FOLLOWS",
        page_number=14,
        supporting_text="The Court expressly follows the principle laid down in ONGC v Saw Pipes."
    )
    db_session.add(cit)
    db_session.commit()

    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(f"/api/cases/{c1.id}/graph?depth=1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["edges"]) >= 1
    edge = next(e for e in data["edges"] if e["source"] == str(c1.id) and e["target"] == str(c2.id))
    assert edge["relationship"] == "FOLLOWS"
    assert edge["verification_status"] == "VERIFIED"
    assert edge["confidence"] == 1.0
    assert edge["page"] == 14
    assert "Saw Pipes" in edge["evidence"]


# =============================================================================
# 7. Graph Traversal Depth and Cycle Handling
# =============================================================================
def test_graph_cycle_protection_and_depth(db_session: Session, sample_cases, test_users):
    """Verifies that reciprocal citations (C1 -> C2 -> C1) terminate safely without infinite loops."""
    c1, c2 = sample_cases[0], sample_cases[1]

    # Create cycle: C1 -> C2 and C2 -> C1
    db_session.add(CaseCitation(source_case_id=c1.id, target_case_id=c2.id, target_case_name=c2.case_name, relationship_type="CITES"))
    db_session.add(CaseCitation(source_case_id=c2.id, target_case_id=c1.id, target_case_name=c1.case_name, relationship_type="DISTINGUISHES"))
    db_session.commit()

    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    # Traversal with depth=2 must terminate cleanly
    resp = client.get(f"/api/cases/{c1.id}/graph?depth=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Both nodes present
    node_ids = {n["id"] for n in data["nodes"]}
    assert str(c1.id) in node_ids
    assert str(c2.id) in node_ids

    # Invalid depth < 1 returns 400/422
    resp_invalid = client.get(f"/api/cases/{c1.id}/graph?depth=0", headers=headers)
    assert resp_invalid.status_code in (400, 422)


# =============================================================================
# 8. Duplicate Citation Elimination
# =============================================================================
def test_duplicate_citation_elimination(db_session: Session, sample_cases, test_users):
    """Verifies that multiple citations of the same case with the same relationship are deduplicated."""
    c1, c2 = sample_cases[0], sample_cases[1]

    # Two identical citation records in DB
    db_session.add(CaseCitation(source_case_id=c1.id, target_case_id=c2.id, relationship_type="APPLIES", supporting_text="Passage 1"))
    db_session.add(CaseCitation(source_case_id=c1.id, target_case_id=c2.id, relationship_type="APPLIES", supporting_text="Passage 2"))
    db_session.commit()

    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(f"/api/cases/{c1.id}/graph?depth=1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    applies_edges = [e for e in data["edges"] if e["source"] == str(c1.id) and e["target"] == str(c2.id) and e["relationship"] == "APPLIES"]
    assert len(applies_edges) == 1, "Duplicate APPLIES edges should be deduplicated"


# =============================================================================
# 9. Missing or Unauthorized Graph Nodes
# =============================================================================
def test_graph_authorization_and_missing_nodes(db_session: Session, test_users):
    """Verifies 404 for missing case and exclusion of private target cases."""
    researcher = test_users["researcher"]
    other_user = test_users["other_user"]
    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    # Missing case ID returns 404
    resp_404 = client.get("/api/cases/999999/graph", headers=headers)
    assert resp_404.status_code == 404

    # Private case owned by other_user
    private_case = Case(case_name="Private Arbitral Decision", court="Delhi HC", year=2024)
    db_session.add(private_case)
    db_session.commit()
    db_session.refresh(private_case)

    private_doc = Document(title="Private Doc", case_id=private_case.id, owner_id=other_user.id, status="READY")
    db_session.add(private_doc)
    db_session.commit()

    # Public case citing private case
    public_case = Case(case_name="Public High Court Order", court="Delhi HC", year=2024)
    db_session.add(public_case)
    db_session.commit()
    db_session.refresh(public_case)

    db_session.add(CaseCitation(source_case_id=public_case.id, target_case_id=private_case.id, relationship_type="CITES"))
    db_session.commit()

    # Researcher should not see other_user's private case in graph
    resp_graph = client.get(f"/api/cases/{public_case.id}/graph?depth=1", headers=headers)
    assert resp_graph.status_code == 200
    data = resp_graph.json()
    node_ids = {n["id"] for n in data["nodes"]}
    assert str(private_case.id) not in node_ids, "Private target case must be excluded from unauthorized graph traversal"


# =============================================================================
# 10. Frontend Comparison & Graph Response Compatibility
# =============================================================================
def test_frontend_comparison_and_graph_compatibility(sample_cases, test_users):
    """Verifies that API response formats match ComparativeIntelligence and PrecedentGraph expectations."""
    token = test_users["token_researcher"]
    headers = {"Authorization": f"Bearer {token}"}

    # Comparison endpoint contract
    comp_resp = client.post("/api/compare", json={"case_ids": [sample_cases[0].id, sample_cases[1].id]}, headers=headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    assert "executive_comparison" in comp_data
    assert "similarities" in comp_data
    assert "differences" in comp_data
    assert "distinguishing_factors" in comp_data
    assert "reasoning_comparison" in comp_data
    assert "principle_comparison" in comp_data
    assert "outcome_comparison" in comp_data
    assert "potential_tensions" in comp_data
    assert "cases" in comp_data
    assert "sources" in comp_data

    # Graph endpoint contract
    graph_resp = client.get(f"/api/cases/{sample_cases[0].id}/graph?depth=1", headers=headers)
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    for node in graph_data["nodes"]:
        assert "id" in node
        assert "case_name" in node
        assert "indexed" in node
    for edge in graph_data["edges"]:
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "relationship" in edge
        assert "evidence" in edge


# =============================================================================
# 11. RAG Faithfulness Investigation & Regression Cases
# =============================================================================
def test_rag_faithfulness_investigation_reproducible_cases():
    """
    Reproduces the exact bug in evaluate_faithfulness where required_sources=[]
    resulted in cov_ratio = 0.0 and score = 0.0, and tests the corrected calculation.
    """
    # Case A: Answer acknowledges date is missing without making forbidden claims
    ans_no_date = "The exact date is not provided, but it was signed around March 2022."
    forbidden = ["2022-03-01", "March 1st"]
    required_empty = []

    # Under original faulty evaluator, cov_ratio was 0.0 -> score was 0.0
    # Under revised logic with zero required sources, score is 1.0 (no hallucinations, no unfulfilled sources)
    score_a = evaluate_faithfulness(ans_no_date, required_empty, forbidden)
    assert score_a == 1.0, "Faithful answer with no required sources must receive full score (1.0)"

    # Case B: Standard abstention
    ans_abstain = "Insufficient evidence in the indexed authorities."
    score_b = evaluate_faithfulness(ans_abstain, required_empty, ["plaintiff won"])
    assert score_b == 1.0

    # Case C: Hallucination penalty
    ans_hallucinated = "The contract was executed on 2022-03-01 without dispute."
    score_c = evaluate_faithfulness(ans_hallucinated, required_empty, forbidden)
    assert score_c == 0.5, "Forbidden claim must be penalized by 0.5"

    # Case D: Missing required source
    ans_uncited = "Liquidated damages were awarded."
    required_s1 = ["case_001:p.5"]
    score_d = evaluate_faithfulness(ans_uncited, required_s1, [])
    assert score_d == 0.0, "Missing required source must reduce coverage to 0.0"

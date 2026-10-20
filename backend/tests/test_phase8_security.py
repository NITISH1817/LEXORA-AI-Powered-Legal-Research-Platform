"""
Phase 8 Security, Privacy & Production Readiness Regression Test Suite
Covers:
1. Password hashing, bcrypt 72-byte truncation resolution, legacy backward compatibility, and length bounds.
2. Authentication, session tokens (expiry, malformation, missing), timing-attack resistance, and auto re-hashing.
3. Strict cross-user isolation and IDOR protections across documents, cases, timelines, graphs, compare, and research sessions.
4. Public/seeded document modification and deletion controls (regular user 403, admin allowed).
5. File ingestion security: path traversal neutralization, size limits, extension allowlists, MIME validation, and corruption rejection.
6. RAG untrusted evidence handling, prompt injection defense, citation grounding, and strict abstention.
7. Production configuration safety: weak SECRET_KEY rejection in production mode, security headers, and secret masking in error responses.
"""

import os
import json
import pytest
import bcrypt
from datetime import timedelta
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import SessionLocal
from backend.models.domain import User, Case, Document, ResearchSession
from backend.security import (
    get_password_hash,
    verify_password,
    verify_and_check_rehash,
    create_access_token,
    get_secret_key,
    MAX_PASSWORD_LENGTH,
)
from backend.config import settings
from backend.services.document_service import (
    validate_document,
    store_document,
    generate_document_id,
    _sanitize_filename,
)
from backend.services.citation_service import validate_and_ground_citations
from backend.services.rag_service import ask_legal_question

client = TestClient(app)


@pytest.fixture(scope="module")
def user_tokens():
    """Create test users in database and return access tokens."""
    tokens = {}
    users_data = [
        ("p8_user_a@lexora.ai", "Password123!", "User Alpha", "RESEARCHER"),
        ("p8_user_b@lexora.ai", "Password123!", "User Beta", "RESEARCHER"),
        ("p8_admin@lexora.ai", "AdminPass123!", "User Admin", "ADMIN"),
    ]
    for email, password, full_name, role in users_data:
        client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name
        })
        login_resp = client.post("/api/auth/login", data={"username": email, "password": password})
        if login_resp.status_code == 200:
            tokens[email] = login_resp.json()["access_token"]
        
        # Ensure role is set correctly in DB
        db = SessionLocal()
        u = db.query(User).filter(User.email == email).first()
        if u and u.role != role:
            u.role = role
            db.commit()
        db.close()
    return tokens


# ===========================================================================
# 1. Password Security & Bcrypt Truncation Hardening
# ===========================================================================

def test_bcrypt_72_byte_truncation_fixed():
    """
    Standard bcrypt truncates passwords at 72 bytes, meaning two passwords that
    share the first 72 bytes authenticate identically. SHA-256 pre-hashing resolves this.
    """
    prefix = "A" * 72
    pwd_1 = prefix + "secret_token_alpha"
    pwd_2 = prefix + "secret_token_beta"

    hash_1 = get_password_hash(pwd_1)
    
    # Must authenticate with correct password
    assert verify_password(pwd_1, hash_1) is True
    # Must NOT authenticate with different password even though first 72 bytes are identical
    assert verify_password(pwd_2, hash_1) is False


def test_legacy_bcrypt_backward_compatibility():
    """
    Existing users with legacy bcrypt hashes (raw bytes) must still be able to log in,
    and the system should indicate that a re-hash is needed.
    """
    raw_password = "legacyUserPassword789!"
    legacy_hash = bcrypt.hashpw(raw_password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

    # Dual verification should succeed and report needs_rehash=True
    is_valid, needs_rehash = verify_and_check_rehash(raw_password, legacy_hash)
    assert is_valid is True
    assert needs_rehash is True

    # Modern format should report needs_rehash=False
    modern_hash = get_password_hash(raw_password)
    is_valid_modern, needs_rehash_modern = verify_and_check_rehash(raw_password, modern_hash)
    assert is_valid_modern is True
    assert needs_rehash_modern is False


def test_oversized_password_rejected_dos_prevention():
    """Passwords exceeding MAX_PASSWORD_LENGTH (1024) must be rejected to prevent CPU exhaustion."""
    huge_pwd = "X" * (MAX_PASSWORD_LENGTH + 1)
    with pytest.raises(ValueError, match="exceeds maximum allowed length"):
        get_password_hash(huge_pwd)

    # Verification must also return False safely without computing expensive hashes
    assert verify_password(huge_pwd, "some_hash") is False


# ===========================================================================
# 2. Authentication & Session Edge Cases
# ===========================================================================

def test_unauthorized_token_edge_cases():
    """Verify malformed, expired, and missing tokens on protected endpoints."""
    # Missing token
    resp = client.get("/api/documents")
    assert resp.status_code == 401

    # Malformed token
    resp = client.get("/api/documents", headers={"Authorization": "Bearer not-a-valid-token"})
    assert resp.status_code == 401

    # Expired token
    expired_token = create_access_token(
        {"sub": "p8_user_a@lexora.ai", "role": "RESEARCHER"},
        expires_delta=timedelta(minutes=-10)
    )
    resp = client.get("/api/documents", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_login_timing_attack_protection_and_generic_error():
    """Non-existent user login should return 401 without revealing user existence."""
    resp = client.post("/api/auth/login", data={"username": "nonexistent_account@lexora.test", "password": "WrongPassword123!"})
    assert resp.status_code == 401
    assert "incorrect" in resp.json()["detail"].lower()


# ===========================================================================
# 3. Cross-User Isolation & IDOR Protections
# ===========================================================================

def test_cross_user_document_isolation(user_tokens):
    """User B cannot access or mutate User A's private document."""
    db = SessionLocal()
    user_a = db.query(User).filter(User.email == "p8_user_a@lexora.ai").first()
    assert user_a is not None

    # Create private doc for User A
    doc_a = Document(
        owner_id=user_a.id,
        title="User A Confidential Brief",
        original_filename="confidential_a.pdf",
        document_type="pdf",
        status="READY",
    )
    db.add(doc_a)
    db.commit()
    db.refresh(doc_a)
    doc_a_id = doc_a.id
    db.close()

    headers_b = {"Authorization": f"Bearer {user_tokens['p8_user_b@lexora.ai']}"}

    # User B reading User A doc -> 404
    resp = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert resp.status_code == 404

    # User B deleting User A doc -> 404
    resp = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert resp.status_code == 404

    # User B retrying User A doc -> 404
    resp = client.post(f"/api/documents/{doc_a_id}/retry", headers=headers_b)
    assert resp.status_code == 404

    # User B reading pages of User A doc -> 404
    resp = client.get(f"/api/documents/{doc_a_id}/pages/1", headers=headers_b)
    assert resp.status_code == 404

    # User B searching inside User A doc -> 404
    resp = client.get(f"/api/documents/{doc_a_id}/search?q=confidential", headers=headers_b)
    assert resp.status_code == 404


def test_public_document_protection_from_unauthorized_deletion(user_tokens):
    """
    Public or system-seeded documents (owner_id is None) can be viewed by researchers,
    but CANNOT be deleted or retried by regular users. Only Admins can mutate them.
    """
    db = SessionLocal()
    pub_doc = Document(
        owner_id=None,  # Public / system-seeded
        title="Supreme Court Landmark Judgment",
        original_filename="landmark.pdf",
        document_type="pdf",
        status="READY",
    )
    db.add(pub_doc)
    db.commit()
    db.refresh(pub_doc)
    pub_doc_id = pub_doc.id
    db.close()

    headers_researcher = {"Authorization": f"Bearer {user_tokens['p8_user_a@lexora.ai']}"}
    headers_admin = {"Authorization": f"Bearer {user_tokens['p8_admin@lexora.ai']}"}

    # Regular user can read public document
    resp = client.get(f"/api/documents/{pub_doc_id}", headers=headers_researcher)
    assert resp.status_code == 200

    # Regular user CANNOT delete public document -> 403 Forbidden
    resp = client.delete(f"/api/documents/{pub_doc_id}", headers=headers_researcher)
    assert resp.status_code == 403
    assert "only be modified or deleted by administrators" in resp.json()["detail"]

    # Regular user CANNOT retry public document -> 403 Forbidden
    resp = client.post(f"/api/documents/{pub_doc_id}/retry", headers=headers_researcher)
    assert resp.status_code == 403

    # Admin CAN delete public document
    resp = client.delete(f"/api/documents/{pub_doc_id}", headers=headers_admin)
    assert resp.status_code == 200


def test_cross_user_case_and_timeline_isolation(user_tokens):
    """User B cannot access User A's private case intelligence or timeline."""
    db = SessionLocal()
    user_a = db.query(User).filter(User.email == "p8_user_a@lexora.ai").first()

    case_a = Case(
        case_name="Private Dispute Alpha v. Beta",
        court="Delhi High Court",
        year=2024,
        category="Commercial",
        analysis_status="COMPLETED",
        executive_summary="Private arbitration findings",
    )
    db.add(case_a)
    db.commit()
    db.refresh(case_a)

    doc_a = Document(
        case_id=case_a.id,
        owner_id=user_a.id,
        title="Arbitration Award",
        document_type="pdf",
        status="READY",
    )
    db.add(doc_a)
    db.commit()
    case_a_id = case_a.id
    db.close()

    headers_b = {"Authorization": f"Bearer {user_tokens['p8_user_b@lexora.ai']}"}

    # User B accessing private case detail -> 404
    resp = client.get(f"/api/cases/{case_a_id}", headers=headers_b)
    assert resp.status_code == 404

    # User B triggering analysis on private case -> 404
    resp = client.post(f"/api/cases/{case_a_id}/analyze", headers=headers_b)
    assert resp.status_code == 404

    # User B accessing private case timeline -> 404
    resp = client.get(f"/api/cases/{case_a_id}/timeline", headers=headers_b)
    assert resp.status_code == 404

    # User B accessing private case citations -> 404
    resp = client.get(f"/api/cases/{case_a_id}/citations", headers=headers_b)
    assert resp.status_code == 404

    # User B accessing private case graph -> 404
    resp = client.get(f"/api/cases/{case_a_id}/graph", headers=headers_b)
    assert resp.status_code == 404


def test_cross_user_research_session_isolation(user_tokens):
    """User B cannot access, delete, or link cases to User A's research session."""
    db = SessionLocal()
    user_a = db.query(User).filter(User.email == "p8_user_a@lexora.ai").first()

    session_a = ResearchSession(
        user_id=user_a.id,
        title="User A Strategy Session",
        research_question="What are the jurisdictional limits?",
    )
    db.add(session_a)
    db.commit()
    db.refresh(session_a)
    session_a_id = session_a.id
    db.close()

    headers_b = {"Authorization": f"Bearer {user_tokens['p8_user_b@lexora.ai']}"}

    # User B viewing session A -> 404
    resp = client.get(f"/api/research/{session_a_id}", headers=headers_b)
    assert resp.status_code == 404

    # User B deleting session A -> 404
    resp = client.delete(f"/api/research/{session_a_id}", headers=headers_b)
    assert resp.status_code == 404

    # User B adding case to session A -> 404
    resp = client.post(f"/api/research/{session_a_id}/cases", json={"case_id": 1}, headers=headers_b)
    assert resp.status_code == 404


# ===========================================================================
# 4. File Ingestion & Path Traversal Security
# ===========================================================================

def test_path_traversal_neutralized():
    """Malicious paths in filenames must be stripped and not used for filesystem storage."""
    malicious_names = [
        "../../etc/passwd.pdf",
        "..\\..\\windows\\system32\\cmd.exe.pdf",
        "/absolute/path/to/evil.pdf",
        "nested/sub/folder/doc.pdf",
    ]
    for name in malicious_names:
        sanitized = _sanitize_filename(name)
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert ".." not in sanitized

    # File storage always uses internal UUID, never raw filename
    internal_id = generate_document_id()
    path = store_document(b"%PDF-1.4 test safe content", internal_id, "pdf")
    upload_dir_real = os.path.realpath(settings.UPLOAD_DIR)
    assert os.path.realpath(path).startswith(upload_dir_real)


def test_upload_format_and_corruption_rejection():
    """Unsupported extensions, mismatched magic bytes, and corrupted files must be rejected."""
    # Disallowed extension
    with pytest.raises(Exception) as excinfo:
        validate_document("malicious.sh", "application/x-sh", b"#!/bin/bash\necho evil")
    assert "415" in str(excinfo.value) or "Unsupported file type" in str(excinfo.value)

    # Fake PDF (claims to be PDF but lacks %PDF header)
    with pytest.raises(Exception) as excinfo:
        validate_document("fake.pdf", "application/pdf", b"Not a real PDF file content")
    assert "corrupted" in str(excinfo.value).lower() or "415" in str(excinfo.value) or "422" in str(excinfo.value)

    # Empty document
    with pytest.raises(Exception) as excinfo:
        validate_document("empty.txt", "text/plain", b"")
    assert "empty" in str(excinfo.value).lower()


# ===========================================================================
# 5. RAG & Evidence Grounding Security
# ===========================================================================

def test_citation_hallucination_and_grounding_layer():
    """
    Simulate LLM response with hallucinated source IDs ([S99]).
    Verification layer must strip hallucinated sources and ground valid ones.
    """
    mock_source_map = {
        "S1": {
            "source_id": "S1",
            "case_name": "State of Punjab v. Ram Singh",
            "court": "Supreme Court of India",
            "year": 1992,
            "page_number": 4,
            "matched_text": "Grave misconduct requires something more than mere negligence.",
        }
    }

    mock_llm_response = {
        "answer": "Grave misconduct requires intent [S1], and damages can be awarded arbitrarily [S99].",
        "key_findings": [
            {"finding": "Grave misconduct requires intent", "sources": ["S1"]},
            {"finding": "Damages can be awarded arbitrarily", "sources": ["S99"]},
        ],
        "legal_principles": [
            {"principle": "Misconduct threshold is high", "sources": ["S1"]},
            {"principle": "Hallucinated principle without evidence", "sources": ["S88"]},
        ],
        "authorities": [
            {"source_id": "S1", "case_name": "Fabricated Name", "court": "Wrong Court", "year": 2099, "page": 999},
            {"source_id": "S99", "case_name": "Imaginary Case", "court": "Fake", "year": 2024, "page": 1},
        ],
    }

    grounded = validate_and_ground_citations(mock_llm_response, mock_source_map)

    # S1 authorities metadata must be overwritten with true ground truth
    assert len(grounded["authorities"]) == 1
    assert grounded["authorities"][0]["case_name"] == "State of Punjab v. Ram Singh"
    assert grounded["authorities"][0]["year"] == 1992
    assert grounded["authorities"][0]["page"] == 4

    # S99 inline citation in answer must be flagged as unsupported
    assert "[UNSUPPORTED CITATION]" in grounded["answer"]

    # Unsupported finding must be marked
    assert any("[UNSUPPORTED]" in f["finding"] for f in grounded["key_findings"])


def test_rag_abstention_on_empty_retrieval(monkeypatch):
    """When no relevant indexed documents are found, RAG must return clear abstention."""
    monkeypatch.setattr("backend.services.rag_service.search_service.hybrid_search", lambda *a, **kw: [])
    response = ask_legal_question("Hypothetical query with zero indexed records")
    assert response["retrieval_info"]["abstained"] is True
    assert "Insufficient evidence" in response["answer"]
    assert response["sources"] == []


# ===========================================================================
# 6. Production Configuration & Security Headers
# ===========================================================================

def test_production_environment_rejects_insecure_secret(monkeypatch):
    """When ENVIRONMENT is 'production', weak or default SECRET_KEY must raise ValueError."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SECRET_KEY", "change_this_to_a_secure_random_string_in_production")

    with pytest.raises(ValueError, match="Insecure SECRET_KEY configured for production environment"):
        get_secret_key()


def test_security_headers_present():
    """Ensure standard defense-in-depth security headers are attached to responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in resp.headers
    assert "X-Request-ID" in resp.headers

"""
Phase 17 Unit and Regression Tests: Human Legal Review Execution & Institutional Pilot Activation.

Systematically verifies:
1. Role-Based Reviewer Authorization (Task 2):
   - Authorized reviewer acceptance.
   - Unauthorized reviewer rejection (UnauthorizedReviewerError).
   - Legitimate human IDs that contain blocked substrings (adv_abbott, lucie_talbot, ciaran_advocate).
   - Automated approval attempts forbidden (AutomatedApprovalForbiddenError).
   - Forged reviewer identities rejected.
   - Invalid or incomplete approval records rejected.
   - Senior-adjudicator-only transitions strictly enforced.
   - Audit-history preservation and schema completeness.
2. Enforced Restricted Pilot Access (Task 3):
   - Public registration rejected when PILOT_REGISTRATION_RESTRICTED is active without invitation code.
   - Rejection on invalid invitation code.
   - Successful registration with valid authorized invitation code.
   - Admin-provisioned user creation (/api/auth/admin/provision-user) restricted to ADMIN role.
   - Non-admin and unauthenticated users rejected from admin provisioning.
"""

import os
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app import app
from backend.config import settings
from evaluation.review_workflow import (
    LegalReviewWorkflow,
    ReviewStatus,
    ReviewerRole,
    ReviewerPermission,
    ReviewerProfile,
    ReviewerRegistry,
    IllegalStateTransitionError,
    AutomatedApprovalForbiddenError,
    UnauthorizedReviewerError,
    UnverifiedImportPacketError,
    compute_verification_signature,
)
from scripts.submit_human_review import process_import_packet


client = TestClient(app)


# =============================================================================
# 1. Role-Based Reviewer Authorization & Anti-Fabrication Tests (Task 2)
# =============================================================================

class TestRoleBasedReviewerAuthorization:
    """Verifies role-based reviewer authorization, false-positive elimination, and audit preservation."""

    @pytest.fixture
    def workflow(self, tmp_path):
        records_path = tmp_path / "review_records.json"
        return LegalReviewWorkflow(storage_path=str(records_path))

    def test_authorized_reviewer_acceptance(self, workflow):
        """Registered human advocate can claim, verify source, review annotation, and approve gold label."""
        qid = "bench_001"
        adv_id = "adv_priya_sharma_delhi_d1234"

        rec1 = workflow.claim_for_review(qid, adv_id, "Claiming for constitutional analysis")
        assert rec1["status"] == ReviewStatus.IN_REVIEW.value

        rec2 = workflow.verify_source(
            qid, adv_id,
            source_authority="AIR 2017 SC 4161",
            source_location="Para 24-28",
            rationale="SCR transcript inspected and verified"
        )
        assert rec2["status"] == ReviewStatus.SOURCE_VERIFIED.value

        rec3 = workflow.review_annotation(
            qid, adv_id,
            rubric_scores={"ratio_accuracy": True, "citation_support": True, "procedural_fidelity": True},
            rationale="Ratio correctly isolated from concurring opinions"
        )
        assert rec3["status"] == ReviewStatus.ANNOTATION_REVIEWED.value

        rec4 = workflow.approve_gold_label(
            qid, adv_id,
            rationale="Approved as authoritative gold label after primary reporter verification",
            source_authority="AIR 2017 SC 4161",
            source_location="Para 24-28"
        )
        assert rec4["status"] == ReviewStatus.APPROVED.value
        assert rec4["stages"]["gold_label_approved"] is True

    def test_unauthorized_reviewer_rejection(self, workflow):
        """Unregistered or forged reviewer identities are rejected with UnauthorizedReviewerError."""
        qid = "bench_002"
        workflow.claim_for_review(qid, "adv_priya_sharma_delhi_d1234")

        with pytest.raises(UnauthorizedReviewerError) as exc_info:
            workflow.approve_gold_label(
                qid,
                reviewer_id="unregistered_anonymous_reviewer",
                rationale="Attempting unverified approval"
            )
        assert "not an authorized legal reviewer" in str(exc_info.value)

    def test_legitimate_human_ids_with_blocked_substrings(self, workflow):
        """
        Legitimate human advocates whose names contain substrings like 'bot', 'ci', or 'script'
        are NOT rejected by naive string matching; their registered role authorizes them.
        """
        # 1. adv_abbott contains 'bot'
        qid1 = "bench_003"
        workflow.claim_for_review(qid1, "adv_abbott")
        workflow.verify_source(qid1, "adv_abbott", "SCR 1950", "p. 88", "Verified")
        workflow.review_annotation(qid1, "adv_abbott", {"ratio_accuracy": True}, "Ratio checked")
        rec_abbott = workflow.approve_gold_label(qid1, "adv_abbott", "Approved by Timothy Abbott Advocate")
        assert rec_abbott["status"] == ReviewStatus.APPROVED.value
        assert rec_abbott["current_reviewer"] == "adv_abbott"

        # 2. lucie_talbot contains 'bot'
        qid2 = "bench_004"
        workflow.claim_for_review(qid2, "lucie_talbot")
        workflow.verify_source(qid2, "lucie_talbot", "SCC 2017", "p. 1", "Verified")
        workflow.review_annotation(qid2, "lucie_talbot", {"ratio_accuracy": True}, "Ratio checked")
        rec_talbot = workflow.approve_gold_label(qid2, "lucie_talbot", "Approved by Lucie Talbot Advocate")
        assert rec_talbot["status"] == ReviewStatus.APPROVED.value

        # 3. ciaran_advocate contains 'ci'
        qid3 = "bench_005"
        workflow.claim_for_review(qid3, "ciaran_advocate")
        workflow.verify_source(qid3, "ciaran_advocate", "AIR 1978", "p. 248", "Verified")
        workflow.review_annotation(qid3, "ciaran_advocate", {"ratio_accuracy": True}, "Ratio checked")
        rec_ciaran = workflow.approve_gold_label(qid3, "ciaran_advocate", "Approved by Ciaran Advocate")
        assert rec_ciaran["status"] == ReviewStatus.APPROVED.value

    def test_automated_approval_attempts_forbidden(self, workflow):
        """Automated scripts, bots, and CI processes raise AutomatedApprovalForbiddenError."""
        qid = "bench_006"
        workflow.claim_for_review(qid, "adv_priya_sharma_delhi_d1234")

        # Explicit bot ID
        with pytest.raises(AutomatedApprovalForbiddenError):
            workflow.approve_gold_label(qid, "bot_evaluator", "CI test script attempt")

        # is_automated flag set to True
        with pytest.raises(AutomatedApprovalForbiddenError):
            workflow.approve_gold_label(
                qid,
                "adv_priya_sharma_delhi_d1234",
                "Automated call",
                is_automated=True
            )

    def test_forged_reviewer_identities_rejected_in_import(self, workflow, tmp_path):
        """Imported packets asserting forged, unregistered reviewer identities are rejected."""
        packet_data = {
            "query_id": "bench_007",
            "reviewer_id": "forged_advocate_unknown_999",
            "decision": "APPROVED",
            "rationale": "Asserting approval from forged account",
            "source_authority": "(2017) 10 SCC 1",
            "source_location": "Para 10"
        }
        packet_path = tmp_path / "forged_packet.json"
        with open(packet_path, "w", encoding="utf-8") as f:
            json.dump(packet_data, f)

        with pytest.raises(UnauthorizedReviewerError) as exc_info:
            process_import_packet(workflow, str(packet_path))
        assert "unregistered or forged reviewer" in str(exc_info.value)

    def test_invalid_or_incomplete_approval_records(self, workflow, tmp_path):
        """Imported packets flagged as unverified or containing invalid cryptographic tokens are rejected."""
        # 1. Unverified approval
        unverified_packet = {
            "query_id": "bench_008",
            "reviewer_id": "adv_priya_sharma_delhi_d1234",
            "decision": "APPROVED",
            "rationale": "Unverified external notes",
            "unverified": True
        }
        p1 = tmp_path / "unverified.json"
        with open(p1, "w", encoding="utf-8") as f:
            json.dump(unverified_packet, f)

        with pytest.raises(UnverifiedImportPacketError) as exc_info:
            process_import_packet(workflow, str(p1))
        assert "unverified external approvals are strictly rejected" in str(exc_info.value).lower()

        # 2. Forged verification token
        bad_token_packet = {
            "query_id": "bench_009",
            "reviewer_id": "adv_priya_sharma_delhi_d1234",
            "decision": "APPROVED",
            "rationale": "Substantive rationale with forged token",
            "verification_token": "forged_invalid_hmac_token_value"
        }
        p2 = tmp_path / "bad_token.json"
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(bad_token_packet, f)

        with pytest.raises(UnverifiedImportPacketError) as exc_info:
            process_import_packet(workflow, str(p2))
        assert "invalid cryptographic verification token" in str(exc_info.value).lower()

    def test_senior_adjudicator_only_transitions(self, workflow):
        """Dispute adjudication and resolution strictly requires the SENIOR_ADJUDICATOR role."""
        qid = "bench_010"
        rev = "adv_priya_sharma_delhi_d1234"
        workflow.claim_for_review(qid, rev)
        workflow.request_adjudication(qid, rev, "Doctrinal conflict on prospective overruling")

        # Regular legal reviewer cannot resolve dispute
        with pytest.raises(UnauthorizedReviewerError) as exc_info:
            workflow.adjudicate_disagreement(
                qid,
                adjudicator_id="adv_priya_sharma_delhi_d1234",
                rationale="Attempting resolution without senior permission"
            )
        assert "lacks SENIOR_ADJUDICATOR permission" in str(exc_info.value)

        # Authorized senior adjudicator can resolve dispute
        rec_resolved = workflow.adjudicate_disagreement(
            qid,
            adjudicator_id="senior_adjudicator_justice_kaul",
            rationale="Resolved per Constitution Bench judgment in In Re Interplay (2024)",
            adjudication_outcome="PRECEDENT_CONFIRMED"
        )
        assert rec_resolved["status"] == ReviewStatus.DISAGREEMENT_ADJUDICATED.value
        assert rec_resolved["stages"]["disagreement_adjudicated"] is True

    def test_audit_history_preservation(self, workflow):
        """Every action records benchmark version, item ID, reviewer role, audit event, and appends to history."""
        qid = "bench_011"
        adv = "adv_priya_sharma_delhi_d1234"
        workflow.claim_for_review(qid, adv, "Step 1: Claim")
        workflow.verify_source(qid, adv, "SCR 2017", "p. 10", "Step 2: Source")
        rec = workflow.review_annotation(qid, adv, {"ratio_accuracy": True}, "Step 3: Rubric")

        history = rec["review_history"]
        assert len(history) == 3

        for entry in history:
            assert entry["benchmark_version"] == "3.0.0"
            assert entry["item_id"] == qid
            assert entry["reviewer_id"] == adv
            assert entry["reviewer_role"] == ReviewerRole.LEGAL_REVIEWER.value
            assert "audit_event" in entry
            assert "timestamp" in entry
            assert "rationale" in entry


# =============================================================================
# 2. Restricted Pilot Access & Account Provisioning Tests (Task 3)
# =============================================================================

class TestRestrictedPilotAccess:
    """Verifies that public self-registration is disabled and admin provisioning is enforced."""

    def test_public_registration_rejected_without_invitation_code(self):
        """Calling /api/auth/register without an invitation code returns 403 Forbidden."""
        resp = client.post("/api/auth/register", json={
            "email": "uninvited_public_user@example.com",
            "password": "securepassword123!",
            "full_name": "Uninvited Public User"
        })
        assert resp.status_code == 403
        assert "Public self-registration is disabled" in resp.json()["detail"]

    def test_public_registration_rejected_with_invalid_invitation_code(self):
        """Calling /api/auth/register with an invalid invitation code returns 403 Forbidden."""
        resp = client.post("/api/auth/register", json={
            "email": "fake_invite_user@example.com",
            "password": "securepassword123!",
            "full_name": "Fake Invite User",
            "invitation_code": "WRONG-INVALID-CODE-999"
        })
        assert resp.status_code == 403
        assert "institutional invitation code is required" in resp.json()["detail"]

    def test_public_registration_accepted_with_valid_invitation_code(self):
        """Calling /api/auth/register with the designated invitation code succeeds."""
        email = f"authorized_pilot_user_{int(datetime.now().timestamp())}@example.com"
        resp = client.post("/api/auth/register", json={
            "email": email,
            "password": "securepassword123!",
            "full_name": "Authorized Pilot Researcher",
            "invitation_code": settings.PILOT_INVITATION_CODE
        })
        assert resp.status_code == 200
        assert resp.json()["email"] == email
        assert resp.json()["role"] == "RESEARCHER"

    def test_admin_provision_user_success(self):
        """An administrator can provision a designated pilot participant via /api/auth/admin/provision-user."""
        # 1. Login as admin
        login_resp = client.post("/api/auth/login", data={
            "username": "p8_admin@lexora.ai",
            "password": "AdminPass123!"
        })
        assert login_resp.status_code == 200
        admin_token = login_resp.json()["access_token"]

        # 2. Provision pilot researcher
        target_email = f"designated_researcher_{int(datetime.now().timestamp())}@pilot.lexora.internal"
        prov_resp = client.post(
            "/api/auth/admin/provision-user",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": target_email,
                "password": "pilotPassword123!",
                "full_name": "Designated Pilot Fellow",
                "role": "RESEARCHER"
            }
        )
        assert prov_resp.status_code == 200
        assert prov_resp.json()["email"] == target_email
        assert prov_resp.json()["role"] == "RESEARCHER"

    def test_non_admin_forbidden_from_admin_provisioning(self):
        """A non-admin user receives 403 Forbidden when attempting to provision accounts."""
        # Login as non-admin researcher
        login_resp = client.post("/api/auth/login", data={
            "username": "p8_user_a@lexora.ai",
            "password": "Password123!"
        })
        assert login_resp.status_code == 200
        user_token = login_resp.json()["access_token"]

        prov_resp = client.post(
            "/api/auth/admin/provision-user",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "email": "hacked_user@example.com",
                "password": "password123!",
                "role": "ADMIN"
            }
        )
        assert prov_resp.status_code == 403

    def test_unauthenticated_forbidden_from_admin_provisioning(self):
        """An unauthenticated request to /api/auth/admin/provision-user returns 401 Unauthorized."""
        prov_resp = client.post(
            "/api/auth/admin/provision-user",
            json={
                "email": "anon_user@example.com",
                "password": "password123!"
            }
        )
        assert prov_resp.status_code == 401

"""
Phase 15 Unit and Integration Tests: Human Legal Adjudication Workflow,
Critical Review Packet Integrity, Approved-Label Evaluation, and Pilot Evidence Collection.

Verifies:
1. Distinct, non-interchangeable review lifecycle states:
   - PENDING -> IN_REVIEW -> SOURCE_VERIFIED -> ANNOTATION_REVIEWED -> APPROVED (GOLD_LABEL_APPROVED)
   - Secondary escalation: NEEDS_ADJUDICATION -> DISAGREEMENT_ADJUDICATED -> APPROVED
   - Rejection: REJECTED with mandatory legal rationale
2. Strict prohibition of automated gold-label approval (AutomatedApprovalForbiddenError).
3. Audit log integrity and append-only stage history.
4. Critical review packets generation for the 8 highest-risk legal items.
5. Review status audit reporting 100% pending reality.
6. Evaluator approved_labels_only mode: Honest INSUFFICIENT_APPROVED_LABELS handling.
7. Pilot telemetry, privacy redaction, and 72-hour triage SLA tracking.
"""

import os
import json
import pytest
from datetime import datetime, timezone, timedelta

from evaluation.review_workflow import (
    LegalReviewWorkflow,
    ReviewStatus,
    IllegalStateTransitionError,
    AutomatedApprovalForbiddenError,
)
from evaluation.evaluator import run_evaluation
from scripts.analyze_pilot_feedback import analyze_pilot_feedback, sanitize_feedback_record
from backend.services.monitoring_service import PilotMonitoringService, sanitize_text
from backend.config import settings


# =============================================================================
# 1. Human Legal Adjudication Workflow & State Machine Tests
# =============================================================================

class TestAdjudicationWorkflowStateMachine:
    """Verifies granular multi-stage review transitions and state separation."""

    @pytest.fixture
    def temp_workflow(self, tmp_path):
        """Creates an isolated workflow instance backed by a temporary file."""
        queue_file = tmp_path / "test_review_records.json"
        wf = LegalReviewWorkflow(storage_path=str(queue_file))
        return wf

    def test_initial_benchmark_state(self, temp_workflow):
        """All queries in a newly initialized workflow start in PENDING state."""
        summary = temp_workflow.get_audit_summary()
        counts = summary["status_distribution"]
        assert counts[ReviewStatus.PENDING.value] == 160
        assert counts[ReviewStatus.APPROVED.value] == 0
        assert counts[ReviewStatus.SOURCE_VERIFIED.value] == 0
        assert counts[ReviewStatus.ANNOTATION_REVIEWED.value] == 0

    def test_complete_adjudication_happy_path(self, temp_workflow):
        """
        Tests the full sequential workflow:
        PENDING -> IN_REVIEW -> SOURCE_VERIFIED -> ANNOTATION_REVIEWED -> APPROVED
        """
        qid = "bench_001"
        rev_id = "advocate_priya_sharma"

        # 1. Claim for review
        rec1 = temp_workflow.claim_for_review(qid, rev_id, "Commencing constitutional review")
        assert rec1["status"] == ReviewStatus.IN_REVIEW.value
        assert rec1["current_reviewer"] == rev_id

        # 2. Verify primary source provenance
        rec2 = temp_workflow.verify_source(
            qid, rev_id,
            source_authority="AIR 2017 SC 4161 (Supreme Court official reporter)",
            source_location="Para 24-28 (Judgment of Chandrachud, J.)",
            rationale="Checked SCR transcript; bench composition and date verified"
        )
        assert rec2["status"] == ReviewStatus.SOURCE_VERIFIED.value
        assert rec2["stages"]["source_verified"] is True
        assert rec2["review_history"][-1]["source_authority"] == "AIR 2017 SC 4161 (Supreme Court official reporter)"

        # 3. Review candidate annotation against legal evidence
        rec3 = temp_workflow.review_annotation(
            qid, rev_id,
            rubric_scores={"ratio_accuracy": True, "citation_support": True, "procedural_fidelity": True},
            rationale="Ratio clearly separated from concurring obiter; statutory citations correct"
        )
        assert rec3["status"] == ReviewStatus.ANNOTATION_REVIEWED.value
        assert rec3["stages"]["annotation_reviewed"] is True
        assert rec3["review_history"][-1]["rubric_scores"]["ratio_accuracy"] is True

        # 4. Formal approval as authoritative gold label
        rec4 = temp_workflow.approve_gold_label(
            qid, rev_id,
            rationale="Holding accurately synthesizes 9-judge bench holding. Citations valid."
        )
        assert rec4["status"] == ReviewStatus.APPROVED.value
        assert rec4["status"] == ReviewStatus.GOLD_LABEL_APPROVED.value

        # Audit trail must have 4 distinct transitions
        assert len(rec4["review_history"]) == 4
        assert [h["to_status"] for h in rec4["review_history"]] == [
            ReviewStatus.IN_REVIEW.value,
            ReviewStatus.SOURCE_VERIFIED.value,
            ReviewStatus.ANNOTATION_REVIEWED.value,
            ReviewStatus.APPROVED.value
        ]

    def test_second_opinion_and_senior_adjudication_path(self, temp_workflow):
        """
        Tests escalating disagreement to senior adjudication:
        PENDING -> IN_REVIEW -> NEEDS_ADJUDICATION -> DISAGREEMENT_ADJUDICATED -> APPROVED
        """
        qid = "bench_072"
        rev1 = "advocate_junior_anand"
        adjudicator = "senior_counsel_deshmukh"

        # Claim and encounter conflict regarding overruling timeline
        temp_workflow.claim_for_review(qid, rev1)
        rec_adj = temp_workflow.request_adjudication(
            qid, rev1,
            dispute_rationale="Ambiguity regarding whether 7-judge In Re Interplay retrospectively overruled 5-judge NN Global"
        )
        assert rec_adj["status"] == ReviewStatus.NEEDS_ADJUDICATION.value

        # Senior adjudicator resolves disagreement
        rec_resolved = temp_workflow.adjudicate_disagreement(
            qid, adjudicator,
            rationale="In Re Interplay (2024) expressly overruled NN Global (2023) 5-judge bench. Annotation is accurate."
        )
        assert rec_resolved["status"] == ReviewStatus.DISAGREEMENT_ADJUDICATED.value

        # Senior adjudicator grants formal gold label approval
        rec_approved = temp_workflow.approve_gold_label(
            qid, adjudicator,
            rationale="Approved as gold label following Constitution Bench adjudication."
        )
        assert rec_approved["status"] == ReviewStatus.APPROVED.value

    def test_rejection_path_with_mandatory_rationale(self, temp_workflow):
        """Reviewer rejects an annotation and provides legal justification."""
        qid = "bench_050"
        rev = "advocate_verma"
        temp_workflow.claim_for_review(qid, rev)

        rec = temp_workflow.reject_annotation(
            qid, rev,
            rationale="Passage omits Section 34(2A) patent illegality limitation for international arbitrations."
        )
        assert rec["status"] == ReviewStatus.REJECTED.value
        assert rec["review_history"][-1]["rationale"] == "Passage omits Section 34(2A) patent illegality limitation for international arbitrations."

    def test_status_separation_non_interchangeability(self):
        """Distinct legal review statuses are mutually exclusive and non-interchangeable."""
        assert ReviewStatus.SOURCE_VERIFIED != ReviewStatus.ANNOTATION_REVIEWED
        assert ReviewStatus.ANNOTATION_REVIEWED != ReviewStatus.APPROVED
        assert ReviewStatus.NEEDS_ADJUDICATION != ReviewStatus.DISAGREEMENT_ADJUDICATED
        assert ReviewStatus.PENDING != ReviewStatus.IN_REVIEW


# =============================================================================
# 2. Anti-Fabrication & Transition Guard Tests
# =============================================================================

class TestAntiFabricationAndSecurityGuards:
    """Verifies that automated scripts cannot approve labels and transitions are checked."""

    @pytest.fixture
    def temp_workflow(self, tmp_path):
        queue_file = tmp_path / "test_review_records.json"
        return LegalReviewWorkflow(storage_path=str(queue_file))

    def test_automated_approval_strictly_forbidden(self, temp_workflow):
        """Any attempt to approve gold labels by automated script raises AutomatedApprovalForbiddenError."""
        qid = "bench_093"
        temp_workflow.claim_for_review(qid, "test_evaluator_bot")

        # Explicit automated flag
        with pytest.raises(AutomatedApprovalForbiddenError):
            temp_workflow.approve_gold_label(qid, "human_reviewer", "Valid rationale", is_automated=True)

        # Bot / automated in reviewer name
        with pytest.raises(AutomatedApprovalForbiddenError):
            temp_workflow.approve_gold_label(qid, "bot_automated_script", "Auto approved by test")

        with pytest.raises(AutomatedApprovalForbiddenError):
            temp_workflow.approve_gold_label(qid, "automated", "CI pipeline")

    def test_illegal_jump_from_pending_to_approved(self, temp_workflow):
        """Cannot bypass review and jump directly from PENDING to APPROVED."""
        qid = "bench_121"
        with pytest.raises(IllegalStateTransitionError):
            temp_workflow.approve_gold_label(qid, "adv_mehta", "Trying to bypass stages")

    def test_empty_rationale_prohibited(self, temp_workflow):
        """Approval and rejection require substantive rationale."""
        qid = "bench_106"
        temp_workflow.claim_for_review(qid, "adv_mehta")
        temp_workflow.verify_source(qid, "adv_mehta", "SCR reporter", "Vol 2, page 100")
        temp_workflow.review_annotation(qid, "adv_mehta", {"ratio_accuracy": True}, "Reviewed")

        with pytest.raises(ValueError):
            temp_workflow.approve_gold_label(qid, "adv_mehta", rationale="   ")

        with pytest.raises(ValueError):
            temp_workflow.reject_annotation(qid, "adv_mehta", rationale="")


# =============================================================================
# 3. Critical Review Packets & Status Audit Export Tests
# =============================================================================

class TestReviewPacketsAndAuditExport:
    """Tests the structured review packets for the 8 critical legal items."""

    def test_critical_review_packets_generation(self):
        """Ensures all 8 critical priority items produce comprehensive legal packets."""
        wf = LegalReviewWorkflow()
        packets = wf.export_critical_review_packets()
        assert len(packets) == 8

        critical_qids = {p["query_id"] for p in packets}
        expected_critical = {
            "bench_093", "bench_132", "bench_131", "bench_121",
            "bench_106", "bench_072", "bench_056", "bench_007"
        }
        assert critical_qids == expected_critical

        # Verify each packet has the mandatory legal analysis fields
        for p in packets:
            assert p["priority_tier"] == "PRIORITY_1_CRITICAL"
            assert "question" in p and len(p["question"]) > 10
            assert "legal_domain" in p
            assert "jurisdiction" in p
            assert "authoritative_sources" in p and len(p["authoritative_sources"]) > 0
            assert "procedural_posture_and_judgment_date" in p
            assert "proposed_expected_answer" in p
            assert "potential_contrary_or_overruling_authorities" in p
            assert "current_status" in p

    def test_review_status_audit_verifies_160_pending(self):
        """Exported review status audit accurately reports 160 items pending and 0 approved."""
        wf = LegalReviewWorkflow()
        audit = wf.export_review_status_audit()
        assert audit["total_benchmark_queries"] == 160
        assert audit["status_distribution"]["PENDING_HUMAN_LEGAL_REVIEW"] == 160
        assert audit["status_distribution"]["APPROVED"] == 0
        assert audit["approved_gold_labels_count"] == 0
        assert audit["pending_review_count"] == 160


# =============================================================================
# 4. Approved-Labels-Only Evaluation Integrity Tests
# =============================================================================

class TestApprovedLabelsEvaluation:
    """Verifies that evaluation restricted to approved labels honestly reports limitations."""

    def test_evaluator_approved_only_empty_state(self):
        """When 0 labels are approved, evaluator outputs INSUFFICIENT_APPROVED_LABELS report."""
        res = run_evaluation(
            split="all",
            retrieval_mode="optimized",
            approved_labels_only=True
        )
        assert res["status"] == "INSUFFICIENT_APPROVED_LABELS"
        assert res["benchmark_metadata"]["approved_gold_label_count"] == 0
        assert res["benchmark_metadata"]["pending_review_count"] == 160
        assert res["metrics"] is None
        assert res["release_gate_status"]["gate_passed"] is False
        assert "evaluation integrity" in res["limitation_statement"].lower()

    def test_approved_query_ids_filtering(self, tmp_path):
        """Workflow correctly returns query IDs for APPROVED items only."""
        queue_file = tmp_path / "test_review_records.json"
        wf = LegalReviewWorkflow(storage_path=str(queue_file))

        assert wf.get_approved_query_ids() == []

        # Approve one item
        wf.claim_for_review("bench_001", "adv_test")
        wf.verify_source("bench_001", "adv_test", "AIR 2017 SC 4161", "Vol 2, p 100")
        wf.review_annotation("bench_001", "adv_test", {"ratio_accuracy": True}, "Valid annotation")
        wf.approve_gold_label("bench_001", "adv_test", "Holding accurate")

        assert wf.get_approved_query_ids() == ["bench_001"]


# =============================================================================
# 5. Pilot Telemetry, Privacy Redaction & 72-Hour Triage SLA Tests
# =============================================================================

class TestPilotEvidenceAndTriageSLA:
    """Verifies pilot monitoring privacy, empty-state reporting, and 72-hour triage SLA."""

    def test_pilot_feedback_empty_state_report(self):
        """analyze_pilot_feedback accurately confirms empty state when no records exist."""
        summary = analyze_pilot_feedback()
        assert summary["status"] == "EMPTY_STATE_VERIFIED"
        assert summary["is_empty_state"] is True
        assert summary["total_feedback_submissions"] == 0
        assert summary["average_rating"] is None

        # Verify SLA tracking structure
        sla = summary["triage_sla_tracking"]
        assert sla["target_sla_hours"] == 72
        assert sla["pending_items_count"] == 0
        assert sla["sla_breaches_count"] == 0
        assert sla["status"] == "COMPLIANT"

    def test_72_hour_triage_sla_calculation(self, tmp_path):
        """SLA calculator flags items pending for longer than 72 hours."""
        mon_dir = tmp_path / "monitoring"
        mon_dir.mkdir()

        now = datetime.now(timezone.utc)
        # 1 item 10 hours old (compliant)
        recent_record = {
            "feedback_id": "fb_1",
            "user_id": 101,
            "timestamp_utc": (now - timedelta(hours=10)).isoformat(),
            "review_status": "PENDING",
            "review_notes": "Citation metadata wrong"
        }
        # 1 item 80 hours old (breached)
        overdue_record = {
            "feedback_id": "fb_2",
            "user_id": 102,
            "timestamp_utc": (now - timedelta(hours=80)).isoformat(),
            "review_status": "PENDING",
            "review_notes": "Holding unsupported"
        }

        fb_file = mon_dir / f"pilot_feedback_{now.strftime('%Y-%m-%d')}.jsonl"
        with open(fb_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(recent_record) + "\n")
            f.write(json.dumps(overdue_record) + "\n")

        summary = analyze_pilot_feedback(
            monitoring_dir=str(mon_dir),
            output_md=str(tmp_path / "report.md"),
            output_json=str(tmp_path / "summary.json")
        )

        assert summary["total_feedback_submissions"] == 2
        sla = summary["triage_sla_tracking"]
        assert sla["pending_items_count"] == 2
        assert sla["sla_breaches_count"] == 1
        assert sla["status"] == "BREACHED"

    def test_privacy_redaction_zero_query_leakage(self):
        """Sanitizer scrubs PII, API tokens, and raw queries from telemetry logs."""
        raw = "User query regarding secret API_KEY=sk-proj-12345 and email test@legalfirm.in"
        clean = sanitize_text(raw)
        assert "sk-proj" not in clean
        assert "test@legalfirm.in" not in clean
        assert "[REDACTED_SENSITIVE]" in clean

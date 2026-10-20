"""
Phase 16 Unit and Regression Tests: Human Legal Review Execution & Controlled Pilot Evidence.

Systematically verifies:
1. Human Legal Review CLI & Submission Engine (scripts/submit_human_review.py):
   - Structured packet formatting and display.
   - Batch packet import from external advocates with schema validation.
   - Strict enforcement of anti-fabrication rules (AutomatedApprovalForbiddenError on bot/script IDs).
2. Separation of Review Stages:
   - Source verification (SOURCE_VERIFIED) is strictly separate from legal proposition approval (APPROVED).
   - Annotation review (ANNOTATION_REVIEWED) requires rubric validation before approval.
   - Disagreement escalation (NEEDS_ADJUDICATION) and senior adjudication (DISAGREEMENT_ADJUDICATED).
3. Approved-Labels Evaluator Integrity:
   - Evaluator in approved-only mode accurately reports INSUFFICIENT_APPROVED_LABELS when 0 items approved.
   - Zero synthetic metrics or false claims of statistical significance.
4. Supervised Pilot Infrastructure & Privacy:
   - 72-hour triage SLA monitoring.
   - Query sanitization and zero PII leakage.
   - Tenant-isolated telemetry and deletion controls.
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
from scripts.submit_human_review import format_packet_display, process_import_packet
from evaluation.evaluator import run_evaluation
from scripts.analyze_pilot_feedback import analyze_pilot_feedback
from backend.services.monitoring_service import PilotMonitoringService, sanitize_text


# =============================================================================
# 1. Review Submission Tool & Packet Import Tests
# =============================================================================

class TestHumanReviewSubmissionCLI:
    """Tests the review submission CLI, formatting, and external packet import workflow."""

    @pytest.fixture
    def isolated_workflow(self, tmp_path):
        storage_file = tmp_path / "test_records.json"
        return LegalReviewWorkflow(storage_path=str(storage_file))

    def test_format_packet_display_contains_mandatory_sections(self):
        """Review packet formatter includes question, citations, holding, and advocate rubric."""
        packet = {
            "query_id": "bench_093",
            "priority_tier": "PRIORITY_1_CRITICAL",
            "risk_score": 7.3,
            "current_status": "PENDING_HUMAN_LEGAL_REVIEW",
            "question": "Trace the evolution of Article 21.",
            "legal_domain": "Constitutional Law",
            "jurisdiction": "Supreme Court of India",
            "procedural_posture_and_judgment_date": "1950 SCR to 2017 SCC",
            "required_citations": ["A.K. Gopalan", "Maneka Gandhi", "Puttaswamy"],
            "proposed_expected_answer": "Evolution from procedure established by law to due process.",
            "potential_contrary_or_overruling_authorities": "Gopalan overruled in Maneka Gandhi",
            "known_uncertainties_and_reviewer_questions": "Scope of substantive due process in India",
            "authoritative_sources": [
                {
                    "chunk_id": "chunk_01",
                    "case_name": "A.K. Gopalan v. State of Madras",
                    "citation": "(1950) SCR 88",
                    "court": "Supreme Court of India",
                    "year": 1950,
                    "excerpt": "Procedure established by law text..."
                }
            ]
        }
        text = format_packet_display(packet)
        assert "LEGAL REVIEW PACKET: bench_093" in text
        assert "PRIORITY_1_CRITICAL" in text
        assert "A.K. Gopalan v. State of Madras" in text
        assert "ADVOCATE VERIFICATION CHECKLIST:" in text
        assert "Source authenticity" in text
        assert "Controlling holding" in text

    def test_import_valid_advocate_review_packet(self, isolated_workflow, tmp_path):
        """Authorized advocate review packet imports successfully and transitions state."""
        packet_data = {
            "query_id": "bench_001",
            "reviewer_id": "adv_suresh_menon_delhi_d1234",
            "decision": "APPROVED",
            "rationale": "SCR official volume inspected; 9-judge ratio on Article 21 substantiated.",
            "source_authority": "AIR 2017 SC 4161 / (2017) 10 SCC 1",
            "source_location": "Paragraphs 24-28 (Judgment of Dr. D.Y. Chandrachud, J.)",
            "source_verified": True,
            "rubric_scores": {
                "ratio_accuracy": True,
                "citation_support": True,
                "procedural_fidelity": True
            }
        }
        packet_file = tmp_path / "advocate_packet.json"
        with open(packet_file, "w", encoding="utf-8") as f:
            json.dump(packet_data, f)

        rec = process_import_packet(isolated_workflow, str(packet_file))
        assert rec["status"] == ReviewStatus.APPROVED.value
        assert rec["stages"]["source_verified"] is True
        assert rec["stages"]["annotation_reviewed"] is True
        assert rec["stages"]["gold_label_approved"] is True
        assert rec["current_reviewer"] == "adv_suresh_menon_delhi_d1234"
        assert len(rec["review_history"]) == 4

    def test_import_packet_rejects_missing_required_fields(self, isolated_workflow, tmp_path):
        """Packets lacking reviewer credentials or rationale are rejected with ValueError."""
        # Missing reviewer_id
        bad_packet = {
            "query_id": "bench_001",
            "decision": "APPROVED",
            "rationale": "Holding is accurate"
        }
        p_file = tmp_path / "bad_packet.json"
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(bad_packet, f)

        with pytest.raises(ValueError, match="missing required field: 'reviewer_id'"):
            process_import_packet(isolated_workflow, str(p_file))

    def test_import_packet_rejects_automated_or_bot_reviewer(self, isolated_workflow, tmp_path):
        """Packets identifying an automated bot or script raise AutomatedApprovalForbiddenError."""
        bot_packet = {
            "query_id": "bench_001",
            "reviewer_id": "bot_automated_eval_script",
            "decision": "APPROVED",
            "rationale": "Passing unit test"
        }
        p_file = tmp_path / "bot_packet.json"
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(bot_packet, f)

        with pytest.raises(AutomatedApprovalForbiddenError):
            process_import_packet(isolated_workflow, str(p_file))


# =============================================================================
# 2. Separation of Review Stages & Disagreement Management
# =============================================================================

class TestReviewStageSeparation:
    """Verifies that source verification, annotation review, and approval remain strictly segregated."""

    @pytest.fixture
    def isolated_workflow(self, tmp_path):
        storage_file = tmp_path / "test_records.json"
        return LegalReviewWorkflow(storage_path=str(storage_file))

    def test_source_verification_does_not_approve_legal_proposition(self, isolated_workflow):
        """Verifying source text must NOT automatically approve the legal holding."""
        qid = "bench_121"
        rev = "adv_kavita_nair"

        isolated_workflow.claim_for_review(qid, rev)
        rec = isolated_workflow.verify_source(
            qid, rev,
            source_authority="Insolvency and Bankruptcy Code, 2016",
            source_location="Section 53(1)(d) vs 53(1)(e)",
            rationale="Statutory text confirmed from Gazette of India"
        )
        assert rec["status"] == ReviewStatus.SOURCE_VERIFIED.value
        assert rec["status"] != ReviewStatus.APPROVED.value
        assert isolated_workflow.get_approved_query_ids() == []

    def test_annotation_review_does_not_approve_gold_label(self, isolated_workflow):
        """Auditing candidate annotation does NOT automatically grant gold label approval."""
        qid = "bench_106"
        rev = "adv_kavita_nair"

        isolated_workflow.claim_for_review(qid, rev)
        isolated_workflow.verify_source(qid, rev, "Arbitration Act 1996", "Section 34(2A)")
        rec = isolated_workflow.review_annotation(
            qid, rev,
            rubric_scores={"ratio_accuracy": True, "citation_support": True, "procedural_fidelity": True},
            rationale="Ssangyong ratio distinguished domestic from international arbitrations"
        )
        assert rec["status"] == ReviewStatus.ANNOTATION_REVIEWED.value
        assert rec["status"] != ReviewStatus.APPROVED.value
        assert isolated_workflow.get_approved_query_ids() == []

    def test_disagreement_escalation_and_adjudication_trail(self, isolated_workflow):
        """Escalating conflict to adjudication preserves prior reviewer notes and adjudicator rationale."""
        qid = "bench_072"
        rev1 = "adv_junior_associate"
        sr_counsel = "senior_adv_harish_salve"

        isolated_workflow.claim_for_review(qid, rev1)
        rec_adj = isolated_workflow.request_adjudication(
            qid, rev1,
            dispute_rationale="Conflict between NN Global (2023) 5-judge majority and earlier Vidya Drolia stamping bench"
        )
        assert rec_adj["status"] == ReviewStatus.NEEDS_ADJUDICATION.value

        rec_res = isolated_workflow.adjudicate_disagreement(
            qid, sr_counsel,
            rationale="7-judge bench In Re Interplay (2024) conclusively settled the law: curable defect under Stamp Act.",
            adjudication_outcome="RESOLVED_APPROVED"
        )
        assert rec_res["status"] == ReviewStatus.DISAGREEMENT_ADJUDICATED.value

        # Grant final gold approval
        rec_final = isolated_workflow.approve_gold_label(
            qid, sr_counsel,
            rationale="Approved as authoritative gold label following 7-judge Constitution Bench holding."
        )
        assert rec_final["status"] == ReviewStatus.APPROVED.value
        # Ensure full history is preserved
        actions = [h["to_status"] for h in rec_final["review_history"]]
        assert actions == [
            ReviewStatus.IN_REVIEW.value,
            ReviewStatus.NEEDS_ADJUDICATION.value,
            ReviewStatus.DISAGREEMENT_ADJUDICATED.value,
            ReviewStatus.APPROVED.value
        ]


# =============================================================================
# 3. Approved-Labels Evaluator Integrity Tests
# =============================================================================

class TestApprovedLabelsEvaluatorIntegrity:
    """Verifies that evaluation restricted to approved labels reports limitations honestly."""

    def test_approved_labels_evaluator_empty_state_report(self):
        """Evaluator reports INSUFFICIENT_APPROVED_LABELS when 0 approved queries exist."""
        results = run_evaluation(
            split="all",
            retrieval_mode="optimized",
            approved_labels_only=True
        )
        assert results["status"] == "INSUFFICIENT_APPROVED_LABELS"
        assert results["benchmark_metadata"]["approved_gold_label_count"] == 0
        assert results["benchmark_metadata"]["pending_review_count"] == 160
        assert results["metrics"] is None
        assert results["release_gate_status"]["gate_passed"] is False

    def test_split_boundaries_preserved_without_leakage(self):
        """Dev and held-out queries remain strictly separated."""
        wf = LegalReviewWorkflow()
        queue = wf.generate_review_queue()
        dev_items = [q for q in queue if q["split"] == "dev"]
        held_out_items = [q for q in queue if q["split"] == "held_out"]

        assert len(dev_items) == 70
        assert len(held_out_items) == 90
        assert len(dev_items) + len(held_out_items) == 160
        # Check no intersection
        dev_ids = {q["query_id"] for q in dev_items}
        held_ids = {q["query_id"] for q in held_out_items}
        assert dev_ids.isdisjoint(held_ids)


# =============================================================================
# 4. Supervised Pilot Infrastructure & Privacy Verification
# =============================================================================

class TestPilotInfrastructureAndPrivacy:
    """Verifies pilot telemetry isolation, 72-hour triage SLA, and PII redaction."""

    def test_empty_pilot_feedback_store_integrity(self):
        """Pilot analysis utility confirms EMPTY_STATE_VERIFIED with zero synthetic data."""
        summary = analyze_pilot_feedback()
        assert summary["status"] == "EMPTY_STATE_VERIFIED"
        assert summary["total_feedback_submissions"] == 0
        assert summary["average_rating"] is None
        assert summary["triage_sla_tracking"]["sla_breaches_count"] == 0
        assert summary["triage_sla_tracking"]["status"] == "COMPLIANT"

    def test_user_telemetry_isolation_and_deletion(self, tmp_path):
        """Users can retrieve and delete only their own telemetry records."""
        mon_service = PilotMonitoringService(monitoring_dir=str(tmp_path))

        # Record events for two distinct users
        mon_service.record_event(user_id=101, query_text="IBC Section 53", latency_ms=120.0)
        mon_service.record_event(user_id=102, query_text="Article 21 privacy", latency_ms=140.0)

        u1_events = mon_service.get_user_events(user_id=101)
        u2_events = mon_service.get_user_events(user_id=102)

        assert len(u1_events) == 1
        assert len(u2_events) == 1
        assert u1_events[0]["user_id"] == 101
        assert u2_events[0]["user_id"] == 102

        # Delete user 101 records
        deleted = mon_service.delete_user_records(user_id=101)
        assert deleted == 1

        assert len(mon_service.get_user_events(user_id=101)) == 0
        assert len(mon_service.get_user_events(user_id=102)) == 1

    def test_query_redaction_by_default(self, tmp_path):
        """Query text is masked with [REDACTED_BY_DEFAULT] in telemetry logs."""
        mon_service = PilotMonitoringService(monitoring_dir=str(tmp_path))
        event = mon_service.record_event(user_id=201, query_text="Confidential case search")
        assert event["query_summary"] == "[REDACTED_BY_DEFAULT]"

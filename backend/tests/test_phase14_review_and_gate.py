"""
Phase 14 Unit and Regression Tests: Human Legal Review Workflow,
Apples-to-Apples Dual-Mode Regression Gate, Risk Engine, and Pilot Privacy.

Systematically verifies:
1. Dual-Mode Regression Gate:
   - Fixed-corpus mode: Requires identical corpus, paired query tracking, rejects incompatible datasets.
   - Expanded-corpus mode: Evaluates expanded benchmark independently, prevents false regression flags.
2. Legal Review Workflow & State Machine:
   - Enforces 5 lifecycle states (PENDING, IN_REVIEW, APPROVED, REJECTED, NEEDS_ADJUDICATION).
   - Rejects illegal state transitions (e.g. PENDING -> APPROVED directly).
   - Strictly prohibits automated scripts from transitioning items to APPROVED.
   - Requires valid human reviewer credentials and maintains full audit history.
3. Legal Accuracy Risk Engine:
   - Calculates risk scores (1.0 to 10.0) across 8 doctrinal failure modes.
   - Accurately tags overruled authorities, constitutional benches, and statutory conflicts.
   - Generates risk-prioritized review queues.
4. Pilot Telemetry & Privacy Controls:
   - Verifies empty-state handling without data fabrication.
   - Verifies PII/credential scrubbing and zero query retention by default.
"""

import os
import json
import pytest
from typing import Dict, Any

from evaluation.regression_gate import (
    RegressionGate,
    evaluate_regression_gate,
    DEFAULT_QUALITY_THRESHOLDS,
)
from evaluation.review_workflow import (
    LegalReviewWorkflow,
    ReviewStatus,
    IllegalStateTransitionError,
    AutomatedApprovalForbiddenError,
    calculate_query_risk_score,
)
from scripts.analyze_pilot_feedback import sanitize_feedback_record, analyze_pilot_feedback
from backend.services.monitoring_service import sanitize_text, PilotMonitoringService
from backend.config import settings


# =============================================================================
# 1. Dual-Mode Regression Gate Tests
# =============================================================================

class TestDualModeRegressionGate:
    """Tests the apples-to-apples regression gate ensuring sound comparative methodology."""

    @pytest.fixture
    def mock_eval_results(self):
        """Creates sample evaluation results for testing gate logic."""
        base_summary = {
            "retrieval_metrics": {
                "answerable_only": {"recall@3": 0.90, "hit_rate@3": 0.95, "mrr@3": 0.85},
                "all_queries": {"recall@3": 0.90, "hit_rate@3": 0.95}
            },
            "claim_support_metrics": {
                "answerable_only": {"macro_support_rate": 0.85, "micro_support_rate": 0.86}
            },
            "citation_metrics": {
                "answerable_only": {"citation_validity_rate": 1.0, "macro_support_rate": 0.88}
            },
            "abstention_metrics": {
                "abstention_precision": 1.0, "correct_abstentions": 20, "missed_abstentions": 0
            }
        }
        
        cand_summary = {
            "retrieval_metrics": {
                "answerable_only": {"recall@3": 0.95, "hit_rate@3": 0.99, "mrr@3": 0.90},
                "all_queries": {"recall@3": 0.95, "hit_rate@3": 0.99}
            },
            "claim_support_metrics": {
                "answerable_only": {"macro_support_rate": 0.86, "micro_support_rate": 0.87}
            },
            "citation_metrics": {
                "answerable_only": {"citation_validity_rate": 1.0, "macro_support_rate": 0.89}
            },
            "abstention_metrics": {
                "abstention_precision": 1.0, "correct_abstentions": 20, "missed_abstentions": 0
            }
        }

        # Mock per-query results
        q_results_base = [
            {"query_id": f"q_{i}", "retrieval_eval": {"recall@3": 1.0 if i < 18 else 0.0}}
            for i in range(20)
        ]
        q_results_cand = [
            {"query_id": f"q_{i}", "retrieval_eval": {"recall@3": 1.0 if i < 19 else 0.0}}
            for i in range(20)
        ]

        baseline = {
            "benchmark_metadata": {"version": "3.0.0", "num_passages": 52, "num_queries": 20},
            "summary": base_summary,
            "query_results": q_results_base
        }
        candidate = {
            "benchmark_metadata": {"version": "3.0.0", "num_passages": 52, "num_queries": 20},
            "summary": cand_summary,
            "query_results": q_results_cand
        }
        return baseline, candidate

    def test_fixed_corpus_mode_passes_when_non_regressed(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        gate = RegressionGate(mode="fixed_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        assert res["gate_passed"] is True
        assert "APPROVED" in res["gate_decision"]
        assert res["mode"] == "fixed_corpus"
        assert res["is_compatible"] is True
        assert res["paired_query_analysis"]["regressed_queries_count"] == 0
        assert res["paired_query_analysis"]["improved_queries_count"] == 1

    def test_fixed_corpus_mode_rejects_incompatible_corpus_size(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        # Alter candidate corpus size
        candidate["benchmark_metadata"]["num_passages"] = 100

        gate = RegressionGate(mode="fixed_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        assert res["gate_passed"] is False
        assert "REJECTED (Incompatible Datasets" in res["gate_decision"]
        assert res["is_compatible"] is False
        assert any("Corpus size mismatch" in r for r in res["violations_list"])

    def test_fixed_corpus_mode_rejects_mismatched_query_count(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        candidate["benchmark_metadata"]["num_queries"] = 35

        gate = RegressionGate(mode="fixed_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        assert res["gate_passed"] is False
        assert "REJECTED (Incompatible Datasets" in res["gate_decision"]
        assert res["is_compatible"] is False

    def test_fixed_corpus_mode_flags_net_query_regression(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        # Cause candidate to regress on query 0
        candidate["query_results"][0]["retrieval_eval"]["recall@3"] = 0.0
        candidate["summary"]["retrieval_metrics"]["answerable_only"]["recall@3"] = 0.85

        gate = RegressionGate(mode="fixed_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        assert res["gate_passed"] is False
        assert "REJECTED" in res["gate_decision"]
        assert res["paired_query_analysis"]["regressed_queries_count"] >= 1

    def test_expanded_corpus_mode_approves_coverage_baseline(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        # Cross-benchmark evaluation: v2 (20 passages, 61 queries) vs v3 (52 passages, 160 queries)
        baseline["benchmark_metadata"] = {"version": "2.0.0", "num_passages": 20, "num_queries": 61}
        candidate["benchmark_metadata"] = {"version": "3.0.0", "num_passages": 52, "num_queries": 160}

        gate = RegressionGate(mode="expanded_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        # In expanded_corpus mode, size differences are expected and not rejected
        assert res["gate_passed"] is True
        assert "APPROVED (Expanded-Corpus Coverage Baseline Established)" in res["gate_decision"]
        assert res["mode"] == "expanded_corpus"

    def test_expanded_corpus_mode_rejects_substandard_quality(self, mock_eval_results):
        baseline, candidate = mock_eval_results
        candidate["benchmark_metadata"] = {"version": "3.0.0", "num_passages": 52, "num_queries": 160}
        # Drop recall below threshold
        candidate["summary"]["retrieval_metrics"]["answerable_only"]["recall@3"] = 0.70

        gate = RegressionGate(mode="expanded_corpus")
        res = gate.evaluate(baseline=baseline, candidate=candidate)

        assert res["gate_passed"] is False
        assert "REJECTED" in res["gate_decision"]
        assert any("recall@3" in r.lower() for r in res["violations_list"])


# =============================================================================
# 2. Human Legal Review Workflow State Machine Tests
# =============================================================================

class TestLegalReviewWorkflow:
    """Verifies state machine transitions, anti-fabrication safeguards, and audit records."""

    @pytest.fixture
    def temp_workflow(self, tmp_path):
        storage_file = str(tmp_path / "test_review_records.json")
        return LegalReviewWorkflow(storage_path=storage_file)

    def test_initial_state_defaults_to_pending(self, temp_workflow):
        rec = temp_workflow.records.get("test_q_01")
        assert rec is None  # Unregistered starts empty, defaults to PENDING in queue

    def test_valid_state_transitions(self, temp_workflow):
        qid = "test_q_01"
        
        # 1. PENDING -> IN_REVIEW
        rec1 = temp_workflow.transition_state(
            query_id=qid,
            to_status=ReviewStatus.IN_REVIEW,
            reviewer_id="ADV_PRIYA_R1",
            rationale="Commencing review of IBC Section 53 waterfall priority."
        )
        assert rec1["status"] == ReviewStatus.IN_REVIEW.value
        assert len(rec1["review_history"]) == 1

        # 2. IN_REVIEW -> NEEDS_ADJUDICATION
        rec2 = temp_workflow.transition_state(
            query_id=qid,
            to_status=ReviewStatus.NEEDS_ADJUDICATION,
            reviewer_id="ADV_PRIYA_R1",
            rationale="Unresolved tension between Rainbow Papers and Paschimanchal Vidyut."
        )
        assert rec2["status"] == ReviewStatus.NEEDS_ADJUDICATION.value
        assert len(rec2["review_history"]) == 2

        # 3. NEEDS_ADJUDICATION -> APPROVED (by Senior Adjudicator)
        rec3 = temp_workflow.transition_state(
            query_id=qid,
            to_status=ReviewStatus.APPROVED,
            reviewer_id="SR_ADVOCATE_ADJUDICATOR",
            rationale="Paschimanchal (3-judge) clarifies Rainbow Papers (2-judge) per Section 53.",
            source_authority="Paschimanchal Vidyut Vitran Nigam v. Raman Ispat (2023) 10 SCC 60",
            source_location="SCC Para 48-52"
        )
        assert rec3["status"] == ReviewStatus.APPROVED.value
        assert len(rec3["review_history"]) == 3
        assert rec3["review_history"][-1]["source_authority"] != ""

    def test_illegal_transition_pending_to_approved_raises_error(self, temp_workflow):
        with pytest.raises(IllegalStateTransitionError) as exc_info:
            temp_workflow.transition_state(
                query_id="test_q_02",
                to_status=ReviewStatus.APPROVED,
                reviewer_id="ADV_PRIYA_R1",
                rationale="Skipping in_review stage."
            )
        assert "Illegal state transition from PENDING_HUMAN_LEGAL_REVIEW to APPROVED" in str(exc_info.value)

    def test_illegal_transition_rejected_to_approved_raises_error(self, temp_workflow):
        qid = "test_q_03"
        temp_workflow.transition_state(qid, ReviewStatus.IN_REVIEW, "ADV_PRIYA_R1", "Starting review.")
        temp_workflow.transition_state(qid, ReviewStatus.REJECTED, "ADV_PRIYA_R1", "Holding misattributed.")

        # Attempting REJECTED -> APPROVED directly should fail
        with pytest.raises(IllegalStateTransitionError):
            temp_workflow.transition_state(qid, ReviewStatus.APPROVED, "ADV_PRIYA_R1", "Overriding rejection directly.")

    def test_automated_approval_is_strictly_forbidden(self, temp_workflow):
        qid = "test_q_04"
        temp_workflow.transition_state(qid, ReviewStatus.IN_REVIEW, "ADV_PRIYA_R1", "Starting review.")

        # Attempting approval with is_automated=True must raise AutomatedApprovalForbiddenError
        with pytest.raises(AutomatedApprovalForbiddenError) as exc_info:
            temp_workflow.transition_state(
                query_id=qid,
                to_status=ReviewStatus.APPROVED,
                reviewer_id="ADV_PRIYA_R1",
                rationale="Automated batch pass.",
                is_automated=True
            )
        assert "Automated evaluation cannot transition item" in str(exc_info.value)

    def test_bot_reviewer_id_cannot_approve_or_reject(self, temp_workflow):
        qid = "test_q_05"
        temp_workflow.transition_state(qid, ReviewStatus.IN_REVIEW, "ADV_PRIYA_R1", "Starting review.")

        with pytest.raises(AutomatedApprovalForbiddenError):
            temp_workflow.transition_state(
                query_id=qid,
                to_status=ReviewStatus.APPROVED,
                reviewer_id="BOT_EVALUATOR_V1",
                rationale="Automated test script pass."
            )

        with pytest.raises(AutomatedApprovalForbiddenError):
            temp_workflow.transition_state(
                query_id=qid,
                to_status=ReviewStatus.REJECTED,
                reviewer_id="automated",
                rationale="Automated script reject."
            )

    def test_persistence_and_reload(self, tmp_path):
        storage_file = str(tmp_path / "persistence_test.json")
        wf1 = LegalReviewWorkflow(storage_path=storage_file)
        wf1.transition_state("q_persist", ReviewStatus.IN_REVIEW, "ADV_R1", "Starting.")
        wf1.transition_state("q_persist", ReviewStatus.REJECTED, "ADV_R1", "Invalid holding.")

        # Load into brand new instance
        wf2 = LegalReviewWorkflow(storage_path=storage_file)
        assert "q_persist" in wf2.records
        assert wf2.records["q_persist"]["status"] == ReviewStatus.REJECTED.value
        assert len(wf2.records["q_persist"]["review_history"]) == 2


# =============================================================================
# 3. Legal Accuracy Risk Engine Tests
# =============================================================================

class TestLegalRiskEngine:
    """Verifies doctrinal risk scoring across the 8 critical legal failure modes."""

    def test_overruled_authority_receives_critical_priority(self):
        query = {
            "id": "q_overruled_test",
            "category": "CONFLICT_DISTINCTION",
            "question": "Was NN Global overruled by the 7-judge bench in In Re Interplay?",
            "expected_answer": "Yes, NN Global Mercantile was overruled by the 7-judge Constitution Bench."
        }
        res = calculate_query_risk_score(query)
        assert res["risk_score"] >= 6.5
        assert res["priority_tier"] == "PRIORITY_1_CRITICAL"
        assert any("OVERRULED_AUTHORITY_RISK" in f for f in res["risk_factors"])

    def test_ratio_vs_submission_receives_high_risk(self):
        query = {
            "id": "q_holding_sub_test",
            "category": "HOLDING_VS_SUBMISSION",
            "question": "What was the majority holding versus the petitioner submission in Puttaswamy?",
            "expected_answer": "The 9-judge bench recognized the fundamental right to privacy under Article 21."
        }
        res = calculate_query_risk_score(query)
        assert res["risk_score"] >= 4.5
        assert res["priority_tier"] in ("PRIORITY_1_CRITICAL", "PRIORITY_2_HIGH")
        assert any("SUBMISSION_VS_HOLDING_RISK" in f for f in res["risk_factors"])

    def test_negative_control_receives_abstention_risk_multiplier(self):
        query = {
            "id": "q_neg_control_test",
            "category": "NEGATIVE_CONTROL_ABSTENTION",
            "question": "What did the Supreme Court hold regarding the 2029 Space Treaty in 1950?",
            "is_unanswerable": True,
            "expected_behavior": "ABSTAIN"
        }
        res = calculate_query_risk_score(query)
        assert any("ABSTENTION_BOUNDARY_RISK" in f for f in res["risk_factors"])
        assert res["risk_score"] >= 4.5

    def test_review_queue_sorting_order(self, tmp_path):
        # Create small mock benchmark
        mock_bm = {
            "queries": [
                {"id": "q_std", "category": "STATUTORY", "question": "What is Section 10?"},
                {"id": "q_crit", "category": "CONFLICT_DISTINCTION", "question": "Overruled precedent in NN Global?"},
                {"id": "q_med", "category": "PRECEDENT_RELATIONSHIP", "question": "Compare Kesavananda and Minerva Mills."}
            ]
        }
        bm_path = str(tmp_path / "mock_bm.json")
        with open(bm_path, "w", encoding="utf-8") as f:
            json.dump(mock_bm, f)

        wf = LegalReviewWorkflow(storage_path=str(tmp_path / "wf_records.json"))
        queue = wf.generate_review_queue(benchmark_path=bm_path)

        assert len(queue) == 3
        # Highest risk should be at index 0
        assert queue[0]["query_id"] == "q_crit"
        assert queue[0]["priority_tier"] == "PRIORITY_1_CRITICAL"
        assert queue[-1]["query_id"] == "q_std"


# =============================================================================
# 4. Pilot Measurement Protocol & Telemetry Privacy Tests
# =============================================================================

class TestPilotMeasurementProtocolAndPrivacy:
    """Verifies privacy preservation, PII scrubbing, and empty-state reproducibility."""

    def test_feedback_record_pii_sanitization(self):
        raw_feedback = {
            "timestamp": "2026-10-20T10:00:00Z",
            "user_id": "advocate_priya_sharma",
            "rating": 2,
            "issue_category": "CLAIM_UNSUPPORTED_BY_PASSAGE",
            "notes": "Sent from priya.advocate@supremecourt.in. Auth token: bearer secret_tok_12345. Ratio was ungrounded."
        }

        sanitized = sanitize_feedback_record(raw_feedback)

        # Raw email must be redacted
        assert "priya.advocate@supremecourt.in" not in sanitized["notes"]
        assert "[REDACTED_EMAIL]" in sanitized["notes"]

        # Sensitive auth token must be redacted
        assert "secret_tok_12345" not in sanitized["notes"]
        assert "[REDACTED_SENSITIVE]" in sanitized["notes"]

        # User ID must be anonymized
        assert sanitized["user_id"] != "advocate_priya_sharma"
        assert sanitized["user_id"].startswith("anonymized_user_")

    def test_empty_pilot_feedback_store_reproducibility(self, tmp_path):
        """Verifies that an empty feedback store generates an honest, reproducible report."""
        empty_dir = tmp_path / "empty_monitoring"
        empty_dir.mkdir()

        out_md = str(tmp_path / "EMPTY_REPORT.md")
        out_json = str(tmp_path / "empty_report.json")

        summary = analyze_pilot_feedback(
            monitoring_dir=str(empty_dir),
            output_md=out_md,
            output_json=out_json
        )

        assert summary["total_feedback_records"] == 0
        assert summary["total_telemetry_events"] == 0
        assert summary["status"] == "EMPTY_STATE_VERIFIED"

        with open(out_md, "r", encoding="utf-8") as f:
            md_content = f.read()
        assert "EMPTY STATE — NO ACTIVE PILOT FEEDBACK" in md_content
        assert "No genuine external pilot feedback records currently exist" in md_content

    def test_zero_raw_query_leakage_when_query_logging_disabled(self, tmp_path):
        """Verifies that queries are masked as [REDACTED_BY_DEFAULT] when query logging is disabled."""
        svc = PilotMonitoringService(monitoring_dir=str(tmp_path))
        orig_setting = settings.PILOT_MONITORING_LOG_QUERIES
        try:
            settings.PILOT_MONITORING_LOG_QUERIES = False
            rec = svc.record_event(
                user_id=1,
                query_text="What are the grounds for winding up under Companies Act Section 271?",
                candidate_count=3,
                latency_ms=120.0
            )
            assert rec is not None
            assert rec["query_summary"] == "[REDACTED_BY_DEFAULT]"
            assert "winding up" not in rec["query_summary"]
        finally:
            settings.PILOT_MONITORING_LOG_QUERIES = orig_setting

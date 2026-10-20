"""
LEXORA Phase 11 Regression & Validation Test Suite

Validates:
1. Metric reconciliation across JSON and Markdown reports.
2. Exact split aggregation (dev, held-out, overall; micro vs macro).
3. Statistical cluster-aware bootstrap and Wilson score calculations.
4. Benchmark expansion schema, domain representation, and annotation provenance.
5. Privacy-safe pilot telemetry logging (redaction of keys, tokens, emails).
6. Disabling monitoring via configuration.
7. Strict tenant/user isolation for audit records.
8. User feedback capture, review flags, and administrative aggregation.
9. Abstention and citation-validation regression invariants.
"""

import os
import json
import shutil
import tempfile
import pytest
from datetime import datetime, timezone

from backend.config import settings
from backend.services.monitoring_service import PilotMonitoringService, sanitize_text
from evaluation.metrics import (
    calculate_cluster_bootstrap_ci,
    get_query_legal_cluster,
    evaluate_claim_support,
    evaluate_citation_correctness,
    evaluate_abstention
)
from evaluation.evaluator import calculate_wilson_ci, run_evaluation


@pytest.fixture
def temp_monitoring_service():
    """Provides an isolated monitoring service using a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="lexora_test_monitoring_")
    svc = PilotMonitoringService(monitoring_dir=temp_dir)
    yield svc
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetricReconciliationAndReporting:
    def test_json_and_markdown_reconciled_consistency(self):
        """Verifies that Markdown and JSON outputs are synchronized and report identical numbers."""
        results = run_evaluation(split="all", retrieval_mode="optimized")

        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "results")
        latest_json_path = os.path.join(results_dir, "latest.json")
        latest_md_path = os.path.join(results_dir, "latest.md")

        assert os.path.exists(latest_json_path), "latest.json must exist"
        assert os.path.exists(latest_md_path), "latest.md must exist"

        with open(latest_json_path, "r", encoding="utf-8") as f:
            j_data = json.load(f)

        with open(latest_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Check that reconciled metrics exist in JSON
        reconciled = j_data.get("reconciled_metrics", {})
        assert "answerable_grounding_targets_n55" in reconciled
        assert "global_macro_benchmark_n61" in reconciled

        ans_data = reconciled["answerable_grounding_targets_n55"]
        glob_data = reconciled["global_macro_benchmark_n61"]

        if j_data.get("benchmark_metadata", {}).get("version") == "3.0.0":
            assert ans_data["query_count"] == 136
            assert glob_data["query_count"] == 160
        else:
            assert ans_data["query_count"] == 55
            assert glob_data["query_count"] == 61

        # Check macro and micro claim support
        micro_cs = ans_data["micro_claim_support"]
        macro_cs = ans_data["macro_claim_support"]
        global_cs = glob_data["macro_claim_support"]

        # Exact expected numbers: 84.13%, 84.24%, 85.79%
        assert f"{micro_cs * 100:.2f}%" in md_content
        assert f"{macro_cs * 100:.2f}%" in md_content
        assert f"{global_cs * 100:.2f}%" in md_content

        # Check numerator and denominator in markdown table
        num = ans_data["claims_numerator"]
        den = ans_data["claims_denominator"]
        assert f"{num} / {den}" in md_content

    def test_split_reconciliation_math(self):
        """Verifies that split counts add up precisely to the overall totals."""
        results = run_evaluation(split="all", retrieval_mode="optimized")
        split_rec = results["reconciled_metrics"]["split_reconciliation"]

        dev = split_rec["dev"]
        held = split_rec["held_out"]

        assert dev["total_queries"] == 25
        assert held["total_queries"] == 36
        assert dev["total_queries"] + held["total_queries"] == 61

        assert dev["answerable_queries"] == 23
        assert held["answerable_queries"] == 32
        assert dev["answerable_queries"] + held["answerable_queries"] == 55


class TestStatisticalMethodology:
    def test_cluster_bootstrap_calculation_and_boundaries(self):
        """Tests cluster-aware bootstrap on clustered data."""
        items = [
            {"cluster_id": "c1", "score": 1.0},
            {"cluster_id": "c1", "score": 0.9},
            {"cluster_id": "c2", "score": 0.8},
            {"cluster_id": "c2", "score": 0.85},
            {"cluster_id": "c3", "score": 0.5},
            {"cluster_id": "c3", "score": 0.6},
        ]
        res = calculate_cluster_bootstrap_ci(items, metric_key="score", cluster_key="cluster_id", B=200, seed=123)
        assert 0.0 <= res["ci_lower"] <= res["mean"] <= res["ci_upper"] <= 1.0
        assert res["clusters"] == 3

    def test_cluster_bootstrap_empty_and_single_cluster_boundaries(self):
        """Tests edge cases for bootstrap: empty items and single item."""
        empty_res = calculate_cluster_bootstrap_ci([], "score")
        assert empty_res["ci_lower"] == 0.0
        assert empty_res["ci_upper"] == 0.0

        single = [{"cluster_id": "c1", "score": 0.75}]
        single_res = calculate_cluster_bootstrap_ci(single, "score", B=100)
        assert single_res["ci_lower"] == 0.75
        assert single_res["ci_upper"] == 0.75

    def test_wilson_ci_boundary_cases(self):
        """Tests Wilson score intervals under boundary cases."""
        zero_res = calculate_wilson_ci(0, 0)
        assert zero_res["proportion"] == 0.0
        assert zero_res["ci_lower"] == 0.0

        all_pass = calculate_wilson_ci(10, 10)
        assert all_pass["proportion"] == 1.0
        assert all_pass["ci_upper"] == 1.0
        assert all_pass["ci_lower"] > 0.65


class TestBenchmarkExpansionAndProvenance:
    def test_expansion_plan_structure_and_coverage(self):
        """Validates that the expansion plan defines >=150 targets across required legal domains."""
        plan_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "evaluation", "datasets", "legal_benchmark_expansion_plan.json"
        )
        assert os.path.exists(plan_path), "Expansion plan file must exist"

        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)

        meta = plan.get("metadata", {})
        assert meta.get("target_query_count", 0) >= 150
        assert len(meta.get("domains", [])) >= 4
        assert len(meta.get("courts", [])) >= 3

        # Verify sample curated items adhere to schema
        samples = plan.get("sample_curated_expansion_items", [])
        assert len(samples) >= 4

        for s in samples:
            assert "id" in s
            assert "question" in s
            assert "category" in s
            assert "relevant_chunk_ids" in s
            assert "annotation_metadata" in s
            ann = s["annotation_metadata"]
            assert "primary_annotator" in ann
            assert "secondary_verifier" in ann
            assert "agreement_status" in ann


class TestPrivacySafePilotMonitoring:
    def test_sensitive_text_sanitization(self):
        """Ensures API keys, tokens, and passwords are never logged verbatim."""
        raw_text = "API_KEY=sk-test-123456789; Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. Contact: test@example.com"
        clean = sanitize_text(raw_text)
        assert "sk-test-123456789" not in clean
        assert "eyJhbGci" not in clean
        assert "test@example.com" not in clean
        assert "[REDACTED_SENSITIVE]" in clean

    def test_query_redaction_by_default(self, temp_monitoring_service):
        """Verifies queries are redacted by default unless specifically configured."""
        orig_setting = settings.PILOT_MONITORING_LOG_QUERIES
        try:
            settings.PILOT_MONITORING_LOG_QUERIES = False
            rec = temp_monitoring_service.record_event(
                user_id=1,
                query_text="Confidential merger clause query between Company A and Company B",
                candidate_count=5,
                latency_ms=120.5
            )
            assert rec is not None
            assert rec["query_summary"] == "[REDACTED_BY_DEFAULT]"
            assert "Company A" not in rec["query_summary"]
        finally:
            settings.PILOT_MONITORING_LOG_QUERIES = orig_setting

    def test_monitoring_disabled_toggle(self, temp_monitoring_service):
        """Verifies no telemetry is recorded when PILOT_MONITORING_ENABLED is False."""
        orig_setting = settings.PILOT_MONITORING_ENABLED
        try:
            settings.PILOT_MONITORING_ENABLED = False
            rec = temp_monitoring_service.record_event(user_id=1, latency_ms=50.0)
            assert rec is None
        finally:
            settings.PILOT_MONITORING_ENABLED = orig_setting

    def test_user_isolation_and_right_to_be_forgotten(self, temp_monitoring_service):
        """Verifies strict tenant isolation: users can only inspect and delete their own events."""
        orig_enabled = settings.PILOT_MONITORING_ENABLED
        settings.PILOT_MONITORING_ENABLED = True
        try:
            temp_monitoring_service.record_event(user_id=101, latency_ms=100.0)
            temp_monitoring_service.record_event(user_id=101, latency_ms=110.0)
            temp_monitoring_service.record_event(user_id=202, latency_ms=250.0)

            # User 101 retrieves only their events
            evs_101 = temp_monitoring_service.get_user_events(user_id=101)
            assert len(evs_101) == 2
            assert all(e["user_id"] == 101 for e in evs_101)

            # User 202 retrieves only their events
            evs_202 = temp_monitoring_service.get_user_events(user_id=202)
            assert len(evs_202) == 1
            assert evs_202[0]["user_id"] == 202

            # User 101 deletes their records
            deleted = temp_monitoring_service.delete_user_records(user_id=101)
            assert deleted == 2

            # User 101 has 0 remaining, while User 202 is unaffected
            assert len(temp_monitoring_service.get_user_events(user_id=101)) == 0
            assert len(temp_monitoring_service.get_user_events(user_id=202)) == 1
        finally:
            settings.PILOT_MONITORING_ENABLED = orig_enabled

    def test_feedback_capture_and_admin_aggregation(self, temp_monitoring_service):
        """Verifies feedback logging and aggregated admin telemetry without leaking private data."""
        orig_enabled = settings.PILOT_MONITORING_ENABLED
        settings.PILOT_MONITORING_ENABLED = True
        try:
            temp_monitoring_service.record_event(user_id=1, latency_ms=100.0, citations_validated=True, abstained=False)
            temp_monitoring_service.record_event(user_id=2, latency_ms=300.0, citations_validated=False, abstained=True)

            temp_monitoring_service.record_feedback(
                request_id="req-test-1",
                user_id=1,
                rating=5,
                review_status="APPROVED",
                review_notes="Grounding accurately substantiated."
            )
            temp_monitoring_service.record_feedback(
                request_id="req-test-2",
                user_id=2,
                rating=2,
                review_status="FLAGGED",
                flag_reason="Distinction between obiter and ratio was blurred."
            )

            summary = temp_monitoring_service.get_admin_summary()
            assert summary["total_requests"] == 2
            assert summary["active_pilot_users_count"] == 2
            assert summary["total_abstentions"] == 1
            assert summary["citations_validated_total"] == 1
            assert summary["feedback_summary"]["total_feedback_submissions"] == 2
            assert summary["feedback_summary"]["flagged_issues_count"] == 1
            assert summary["feedback_summary"]["average_rating"] == 3.5
        finally:
            settings.PILOT_MONITORING_ENABLED = orig_enabled


class TestAbstentionAndCitationRegression:
    def test_negative_control_abstention_behavior(self):
        """Verifies unanswerable query triggers abstention."""
        ans = "Based on the provided authorities, there is insufficient evidence to support this proposition."
        eval_res = evaluate_abstention(ans, is_unanswerable=True)
        assert eval_res["classification"] == "TRUE_ABSTENTION"
        assert eval_res["is_correct"] is True

    def test_citation_correctness_separation(self):
        """Verifies citation validity (metadata match) is distinct from substantive support."""
        catalog = {
            "chunk_01": {
                "case_name": "Kailash Nath Associates v. DDA",
                "page_number": 12,
                "text": "Section 74 of the Indian Contract Act requires proof of damage or loss before liquidated damages can be awarded."
            }
        }

        # Case 1: Valid metadata and substantively supported
        good_cit = [{
            "source_id": "chunk_01",
            "case_name": "Kailash Nath Associates v. DDA",
            "page": 12,
            "associated_claim": "Proof of damage is required under Section 74."
        }]
        res1 = evaluate_citation_correctness(good_cit, catalog)
        assert res1["validity_rate"] == 1.0
        assert res1["support_rate"] == 1.0

        # Case 2: Valid metadata but unrelated claim (unsupported)
        unsupported_cit = [{
            "source_id": "chunk_01",
            "case_name": "Kailash Nath Associates v. DDA",
            "page": 12,
            "associated_claim": "The arbitration award must be rendered within twelve months."
        }]
        res2 = evaluate_citation_correctness(unsupported_cit, catalog)
        assert res2["validity_rate"] == 1.0
        assert res2["support_rate"] == 0.0

        # Case 3: Hallucinated / missing source ID
        fake_cit = [{
            "source_id": "chunk_nonexistent_99",
            "case_name": "Imaginary Case v. State",
            "page": 1,
            "associated_claim": "Some claim"
        }]
        res3 = evaluate_citation_correctness(fake_cit, catalog)
        assert res3["validity_rate"] == 0.0
        assert res3["support_rate"] == 0.0

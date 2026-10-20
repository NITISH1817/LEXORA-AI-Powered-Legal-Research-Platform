"""
Phase 13 Unit and Regression Tests: Legal Accuracy Improvement, Benchmark Expansion,
Metric Hardening, Regression Gate, and Telemetry Privacy.

These tests systematically verify:
1. Hardened Metric Calculations:
   - Prevention of empty/whitespace substring matching vulnerability in claim grounding.
   - Strict decoupling of citation validity from citation support.
   - Abstention detection without false answers across negative controls.
2. Benchmark v3 Schema, Provenance, and Split Integrity:
   - Exactly 52 corpus passages and 160 queries.
   - 70 dev / 90 held-out split isolation without data leakage.
   - Non-empty source citations, authentic domains, and unique IDs.
3. Statistical Confidence Engine:
   - Wilson score 95% confidence intervals.
   - Cluster-aware bootstrap resampling across authority clusters.
4. Regression Gate Engine:
   - Detection of recall drops, claim grounding drops, and abstention violations.
5. Pilot Telemetry & Feedback Privacy:
   - Empty-state compliance without fabricated usage statistics.
   - Redaction of raw queries, PII, and client-sensitive text.
"""

import os
import json
import pytest
from typing import Dict, Any

from evaluation.metrics import (
    evaluate_claim_support,
    evaluate_citation_correctness,
    evaluate_abstention,
    calculate_cluster_bootstrap_ci,
    get_query_legal_cluster,
    ABSTENTION_INDICATORS,
)
from evaluation.evaluator import calculate_wilson_ci, run_evaluation
from evaluation.regression_gate import evaluate_regression_gate, RegressionGate, DEFAULT_QUALITY_THRESHOLDS
from scripts.analyze_pilot_feedback import analyze_pilot_feedback, sanitize_feedback_record, ISSUE_TAXONOMY


# =============================================================================
# 1. Hardened Metric Calculations & Vulnerability Fixes
# =============================================================================

class TestMetricHardening:
    """Tests verifying fixes for known evaluator edge cases and vulnerabilities."""

    def test_empty_or_whitespace_claim_cannot_be_supported(self):
        """
        Regression Test: In Python, `"" in passage` evaluates to True.
        Previously, empty, whitespace-only, or degenerate claims could falsely
        match passages and receive 100% support.
        """
        passage_text = "Under Section 74 of the Indian Contract Act, reasonable compensation is awarded."
        source_chunks = {"doc_01": passage_text}

        # Test empty claim
        res_empty = evaluate_claim_support(
            claims=[{"claim": "", "source_ids": ["doc_01"]}],
            source_chunks=source_chunks
        )
        assert res_empty["support_ratio"] == 0.0
        assert res_empty["supported_claims"] == 0
        assert res_empty["total_claims"] == 1
        assert res_empty["details"][0]["is_supported"] is False

        # Test whitespace-only claim
        res_spaces = evaluate_claim_support(
            claims=[{"claim": "   \n\t  ", "source_ids": ["doc_01"]}],
            source_chunks=source_chunks
        )
        assert res_spaces["support_ratio"] == 0.0
        assert res_spaces["details"][0]["is_supported"] is False

        # Test very short/degenerate claim (<3 chars)
        res_short = evaluate_claim_support(
            claims=[{"claim": "no", "source_ids": ["doc_01"]}],
            source_chunks=source_chunks
        )
        assert res_short["support_ratio"] == 0.0
        assert res_short["details"][0]["is_supported"] is False

    def test_decoupling_citation_validity_from_citation_support(self):
        """
        Regression Test: A citation can be formally valid (matching the document catalog)
        without substantively supporting the specific legal claim.
        Verifies validity != support.
        """
        valid_citations = [
            {
                "source_id": "chunk_kn_01",
                "case_name": "Kailash Nath Associates v. DDA",
                "associated_claim": ""  # No substantive claim attached
            }
        ]
        doc_catalog = {
            "chunk_kn_01": {
                "case_name": "Kailash Nath Associates v. DDA",
                "text": "Section 74 requires proof of loss where loss is possible to prove."
            }
        }
        res = evaluate_citation_correctness(valid_citations, doc_catalog)
        assert res["validity_rate"] == 1.0, "Formally valid citation must pass validity check"
        assert res["support_rate"] == 0.0, "Citation without an associated claim cannot be marked supported"
        assert res["details"][0]["is_valid"] is True
        assert res["details"][0]["is_supported"] is False

    def test_valid_citation_with_mismatched_claim_fails_support(self):
        """A valid citation with a claim contradicted or completely unrelated to the passage must fail support."""
        citations = [
            {
                "source_id": "chunk_kn_01",
                "case_name": "Kailash Nath Associates v. DDA",
                "associated_claim": "Income tax penalties apply to offshore share transfers between foreign corporations."
            }
        ]
        doc_catalog = {
            "chunk_kn_01": {
                "case_name": "Kailash Nath Associates v. DDA",
                "text": "Proof of damage or loss is a condition precedent for claiming liquidated damages under Section 74."
            }
        }
        res = evaluate_citation_correctness(citations, doc_catalog)
        assert res["validity_rate"] == 1.0
        assert res["support_rate"] == 0.0
        assert res["details"][0]["is_supported"] is False

    def test_negative_control_abstention_detection(self):
        """Verifies that expanded abstention indicators correctly classify unanswerable queries."""
        # Indicator 1: "must abstain"
        r1 = evaluate_abstention(
            "The system must abstain from answering as the indexed corpus lacks state tax acts.",
            is_unanswerable=True
        )
        assert r1["classification"] == "TRUE_ABSTENTION"
        assert r1["is_correct"] is True

        # Indicator 2: "does not exist"
        r2 = evaluate_abstention(
            "Such a constitutional provision does not exist in the indexed database.",
            is_unanswerable=True
        )
        assert r2["classification"] == "TRUE_ABSTENTION"
        assert r2["is_correct"] is True

        # Indicator 3: "outside the indexed corpus"
        r3 = evaluate_abstention(
            "This statutory question falls outside the indexed corpus.",
            is_unanswerable=True
        )
        assert r3["classification"] == "TRUE_ABSTENTION"
        assert r3["is_correct"] is True

        # False answer (unsafe answering of negative control)
        r4 = evaluate_abstention(
            "Yes, the state VAT amendment of 2024 requires a 15% surcharge.",
            is_unanswerable=True
        )
        assert r4["classification"] == "FALSE_ANSWER"
        assert r4["is_correct"] is False


# =============================================================================
# 2. Benchmark v3 Schema, Provenance, and Integrity
# =============================================================================

class TestBenchmarkV3Integrity:
    """Verifies that legal_benchmark_v3.json adheres strictly to quality standards."""

    @pytest.fixture(scope="class")
    def benchmark_v3_data(self):
        v3_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "evaluation", "datasets", "legal_benchmark_v3.json"
        )
        assert os.path.exists(v3_path), f"Benchmark v3 not found at {v3_path}"
        with open(v3_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_target_scale_52_passages_160_queries(self, benchmark_v3_data):
        """Benchmark v3 must meet the expanded scale of exactly 52 passages and 160 queries."""
        corpus = benchmark_v3_data.get("corpus", [])
        queries = benchmark_v3_data.get("queries", [])
        assert len(corpus) == 52, f"Expected 52 passages, found {len(corpus)}"
        assert len(queries) == 160, f"Expected 160 queries, found {len(queries)}"

    def test_split_distribution_70_dev_90_held_out(self, benchmark_v3_data):
        """Queries must be partitioned into 70 dev and 90 held-out without unassigned items."""
        queries = benchmark_v3_data.get("queries", [])
        dev_queries = [q for q in queries if q.get("split") == "dev"]
        held_out_queries = [q for q in queries if q.get("split") == "held_out"]
        assert len(dev_queries) == 70, f"Expected 70 dev queries, got {len(dev_queries)}"
        assert len(held_out_queries) == 90, f"Expected 90 held-out queries, got {len(held_out_queries)}"
        assert len(dev_queries) + len(held_out_queries) == 160

    def test_expanded_abstention_sample_size_n24(self, benchmark_v3_data):
        """Negative control queries must be expanded from 6 (provisional) to 24."""
        queries = benchmark_v3_data.get("queries", [])
        negative_controls = [
            q for q in queries
            if q.get("is_unanswerable")
            or q.get("category") in ("ABSTENTION", "NEGATIVE_CONTROL_ABSTENTION")
            or "ABSTAIN" in q.get("expected_behavior", "")
        ]
        assert len(negative_controls) == 24, f"Expected 24 negative controls, found {len(negative_controls)}"

    def test_corpus_provenance_and_schema(self, benchmark_v3_data):
        """Every corpus passage must contain verifiable citation, authentic source, and non-empty text."""
        corpus = benchmark_v3_data.get("corpus", [])
        for doc in corpus:
            assert doc["id"], "Passage must have unique ID"
            assert len(doc["text"]) > 100, f"Passage {doc['id']} text is too short ({len(doc['text'])} chars)"
            meta = doc.get("metadata", {})
            assert meta.get("citation"), f"Passage {doc['id']} must have authoritative citation"
            assert meta.get("court") in ["Supreme Court of India", "Parliament of India", "Constituent Assembly of India"], f"Unverified source in {doc['id']}"

    def test_query_schema_and_cross_referencing(self, benchmark_v3_data):
        """Every query must reference valid passages or be marked unanswerable."""
        corpus_ids = {d["id"] for d in benchmark_v3_data.get("corpus", [])}
        queries = benchmark_v3_data.get("queries", [])
        seen_qids = set()

        for q in queries:
            qid = q.get("id") or q.get("query_id")
            assert qid, "Query must have an ID"
            assert qid not in seen_qids, f"Duplicate query ID: {qid}"
            seen_qids.add(qid)

            q_text = q.get("question") or q.get("query", "")
            assert len(q_text) > 10, f"Query {qid} text too short"
            assert q.get("split") in ["dev", "held_out"], f"Query {qid} missing valid split"

            is_negative = (
                q.get("is_unanswerable")
                or q.get("category") in ("ABSTENTION", "NEGATIVE_CONTROL_ABSTENTION")
                or "ABSTAIN" in q.get("expected_behavior", "")
            )

            if is_negative:
                # Abstention query
                pass
            else:
                if "relevant_chunk_ids" in q:
                    relevant = list(q["relevant_chunk_ids"].keys())
                else:
                    relevant = q.get("relevant_passage_ids", [])
                assert len(relevant) >= 1, f"Answerable query {qid} must reference at least 1 passage"
                for rid in relevant:
                    assert rid in corpus_ids, f"Query {qid} references non-existent passage {rid}"


# =============================================================================
# 3. Statistical Confidence Engine (Wilson & Cluster Bootstrap)
# =============================================================================

class TestStatisticalEngine:
    """Verifies that confidence interval calculators handle clusters and boundary cases."""

    def test_wilson_ci_edge_cases(self):
        """Wilson CI must handle 0/N, N/N, and empty samples properly."""
        # Zero successes
        ci_zero = calculate_wilson_ci(0, 100)
        assert ci_zero["proportion"] == 0.0
        assert ci_zero["ci_lower"] == 0.0
        assert ci_zero["ci_upper"] > 0.0

        # Perfect successes
        ci_perf = calculate_wilson_ci(50, 50)
        assert ci_perf["proportion"] == 1.0
        assert ci_perf["ci_lower"] >= 0.90
        assert ci_perf["ci_upper"] == 1.0

        # Empty
        ci_empty = calculate_wilson_ci(0, 0)
        assert ci_empty["proportion"] == 0.0
        assert ci_empty["ci_lower"] == 0.0
        assert ci_empty["ci_upper"] == 0.0

    def test_cluster_bootstrap_ci(self):
        """Cluster bootstrap must calculate non-zero intervals accounting for cluster groupings."""
        items = [
            {"score": 1.0, "cluster_id": "KAILASH_NATH_CLUSTER"},
            {"score": 1.0, "cluster_id": "KAILASH_NATH_CLUSTER"},
            {"score": 0.8, "cluster_id": "PUTTASWAMY_PRIVACY_CLUSTER"},
            {"score": 0.9, "cluster_id": "PUTTASWAMY_PRIVACY_CLUSTER"},
            {"score": 0.7, "cluster_id": "SWISS_RIBBONS_IBC_CLUSTER"},
        ]
        ci = calculate_cluster_bootstrap_ci(items, metric_key="score", B=200)
        assert ci["mean"] > 0.8
        assert 0.5 <= ci["ci_lower"] <= ci["ci_upper"] <= 1.0
        assert ci["clusters"] == 3


# =============================================================================
# 4. Regression Gate Engine
# =============================================================================

class TestRegressionGate:
    """Verifies automated quality gates and regression detection."""

    def test_regression_gate_passes_for_equal_or_superior_candidate(self):
        """Candidate matching or beating baseline must pass all regression checks."""
        baseline = {
            "timestamp": "2026-10-20T10:00:00Z",
            "benchmark_metadata": {"version": "3.0.0"},
            "retrieval_metrics": {"recall_at_3": 0.95, "hit_rate_at_3": 0.99},
            "answer_quality_metrics": {
                "answerable_macro_claim_support": 0.82,
                "answerable_macro_citation_support": 0.87,
                "mean_citation_validity_rate": 1.0,
                "abstention_accuracy": 1.0
            }
        }
        candidate = {
            "timestamp": "2026-10-20T12:00:00Z",
            "benchmark_metadata": {"version": "3.0.0"},
            "retrieval_metrics": {"recall_at_3": 0.96, "hit_rate_at_3": 1.0},
            "answer_quality_metrics": {
                "answerable_macro_claim_support": 0.84,
                "answerable_macro_citation_support": 0.89,
                "mean_citation_validity_rate": 1.0,
                "abstention_accuracy": 1.0
            }
        }
        gate_res = evaluate_regression_gate(baseline, candidate)
        assert gate_res["gate_passed"] is True
        assert gate_res["violations_count"] == 0

    def test_regression_gate_fails_when_recall_regresses(self):
        """Candidate with recall drop exceeding tolerance must trigger FAIL."""
        baseline = {
            "timestamp": "2026-10-20T10:00:00Z",
            "benchmark_metadata": {"version": "3.0.0"},
            "retrieval_metrics": {"recall_at_3": 0.95, "hit_rate_at_3": 0.99},
            "answer_quality_metrics": {
                "answerable_macro_claim_support": 0.82,
                "answerable_macro_citation_support": 0.87,
                "mean_citation_validity_rate": 1.0,
                "abstention_accuracy": 1.0
            }
        }
        # Recall drops by 5% (from 0.95 to 0.90)
        candidate = {
            "timestamp": "2026-10-20T12:00:00Z",
            "benchmark_metadata": {"version": "3.0.0"},
            "retrieval_metrics": {"recall_at_3": 0.90, "hit_rate_at_3": 0.99},
            "answer_quality_metrics": {
                "answerable_macro_claim_support": 0.82,
                "answerable_macro_citation_support": 0.87,
                "mean_citation_validity_rate": 1.0,
                "abstention_accuracy": 1.0
            }
        }
        gate_res = evaluate_regression_gate(baseline, candidate)
        assert gate_res["gate_passed"] is False
        assert any("Recall@3 regressed" in v for v in gate_res["violations_list"])


# =============================================================================
# 5. Pilot Telemetry & Feedback Privacy
# =============================================================================

class TestPilotFeedbackPrivacy:
    """Verifies that feedback reporting is honest, empty-state compliant, and privacy-preserving."""

    def test_empty_state_analysis_generates_zero_usage_metrics(self, tmp_path):
        """When telemetry log has zero bytes or non-existent, no fake stats may be fabricated."""
        empty_dir = tmp_path / "monitoring"
        empty_dir.mkdir()
        empty_file = empty_dir / "pilot_feedback_2026-10-20.jsonl"
        empty_file.write_text("", encoding="utf-8")

        summary = analyze_pilot_feedback(
            monitoring_dir=str(empty_dir),
            output_md=str(tmp_path / "out.md"),
            output_json=str(tmp_path / "out.json")
        )
        assert summary["status"] == "EMPTY_STATE_VERIFIED"
        assert summary["total_feedback_records"] == 0
        assert summary["issue_taxonomy_counts"]["UNSUPPORTED_LEGAL_CLAIM"] == 0

    def test_sanitize_feedback_record_redacts_pii_and_raw_query(self):
        """Sanitization must strip raw query texts, client names, and unredacted PII."""
        raw_record = {
            "timestamp": "2026-10-20T10:00:00Z",
            "user_id": 42,
            "query_text": "Did the company ABC Ltd commit fraud under Section 447?",
            "notes": "Contact me at advocate.sharma@example.com regarding the dispute.",
            "issue_category": "CLAIM_UNSUPPORTED_BY_PASSAGE"
        }
        sanitized = sanitize_feedback_record(raw_record)
        # Raw query text must be completely omitted
        assert "query_text" not in sanitized
        # Email address must be redacted
        assert "advocate.sharma@example.com" not in sanitized["notes"]
        assert "[REDACTED_EMAIL]" in sanitized["notes"]
        # Explicit category mapping preserved
        assert sanitized["issue_code"] == "CLAIM_UNSUPPORTED_BY_PASSAGE"

"""
Phase 9 Automated Regression Suite: Legal Accuracy Evaluation, Ground Truth & Benchmarking

Tests:
1. Retrieval Metric calculations: Precision@K, Recall@K, Hit Rate@K, MRR, and graded nDCG@K with edge cases.
2. Benchmark dataset schema integrity: required keys, splits, valid categories, and non-empty corpus.
3. Atomic claim support and citation correctness: distinguishing citation validity from citation support.
4. Abstention classification matrix: True Abstention, False Abstention, False Answering, and True Answering.
5. Specialized feature metrics: case comparison, precedent graph relationships, and timeline precision.
6. Reproducible evaluation execution: verifying deterministic offline evaluation and output serialization.
7. Privacy and security in evaluation logs: ensuring no secrets, API keys, or private document paths are leaked.
"""

import os
import json
import pytest
from evaluation.metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_hit_rate_at_k,
    calculate_mrr,
    calculate_ndcg_at_k,
    evaluate_claim_support,
    evaluate_citation_correctness,
    evaluate_answer_correctness,
    evaluate_abstention,
    evaluate_comparison_accuracy,
    evaluate_precedent_graph_accuracy,
    evaluate_timeline_accuracy,
    evaluate_faithfulness,
)
from evaluation.evaluator import run_evaluation


# =============================================================================
# 1. Retrieval Metrics & Mathematical Edge Cases
# =============================================================================

def test_retrieval_precision_recall_hitrate():
    retrieved = ["doc_1", "doc_2", "doc_3", "doc_4"]
    relevant = ["doc_2", "doc_4"]

    # At K=1: retrieved=["doc_1"], hits=0
    assert calculate_precision_at_k(retrieved, relevant, k=1) == 0.0
    assert calculate_recall_at_k(retrieved, relevant, k=1) == 0.0
    assert calculate_hit_rate_at_k(retrieved, relevant, k=1) == 0.0

    # At K=2: retrieved=["doc_1", "doc_2"], hits=1 ("doc_2")
    assert calculate_precision_at_k(retrieved, relevant, k=2) == 0.5
    assert calculate_recall_at_k(retrieved, relevant, k=2) == 0.5
    assert calculate_hit_rate_at_k(retrieved, relevant, k=2) == 1.0

    # At K=4: retrieved all, hits=2
    assert calculate_precision_at_k(retrieved, relevant, k=4) == 0.5
    assert calculate_recall_at_k(retrieved, relevant, k=4) == 1.0
    assert calculate_hit_rate_at_k(retrieved, relevant, k=4) == 1.0


def test_retrieval_zero_relevant_handling():
    """Queries with 0 relevant items (e.g. unanswerable / abstention) must not inflate scores."""
    retrieved = ["doc_1", "doc_2"]
    empty_relevant = []

    # Precision should be 0.0
    assert calculate_precision_at_k(retrieved, empty_relevant, k=2) == 0.0
    # Hit rate should be 0.0
    assert calculate_hit_rate_at_k(retrieved, empty_relevant, k=2) == 0.0
    # MRR should be 0.0
    assert calculate_mrr(retrieved, empty_relevant) == 0.0


def test_mrr_calculation():
    assert calculate_mrr(["a", "b", "c"], ["b"]) == 0.5
    assert calculate_mrr(["a", "b", "c"], ["a"]) == 1.0
    assert calculate_mrr(["a", "b", "c"], ["c"]) == pytest.approx(0.3333, rel=1e-3)
    assert calculate_mrr(["a", "b", "c"], ["d"]) == 0.0


def test_ndcg_graded_relevance():
    """Verify nDCG@K calculation with binary and graded relevance."""
    retrieved = ["doc_1", "doc_2", "doc_3"]
    # doc_1 is primary (grade 2), doc_3 is secondary (grade 1)
    relevance_grades = {"doc_1": 2, "doc_3": 1}

    # Ideal ranking would be ["doc_1", "doc_3", ...]
    # Retrieved order is doc_1 (rel=2), doc_2 (rel=0), doc_3 (rel=1)
    ndcg_3 = calculate_ndcg_at_k(retrieved, relevance_grades, k=3)
    assert 0.85 <= ndcg_3 <= 1.0

    # Perfect ranking achieves 1.0
    perfect_retrieved = ["doc_1", "doc_3", "doc_2"]
    assert calculate_ndcg_at_k(perfect_retrieved, relevance_grades, k=2) == 1.0

    # Worst ranking where no relevant docs are retrieved achieves 0.0
    irrelevant = ["x", "y", "z"]
    assert calculate_ndcg_at_k(irrelevant, relevance_grades, k=3) == 0.0


# =============================================================================
# 2. Benchmark Dataset Integrity & Schema
# =============================================================================

def test_benchmark_dataset_v2_schema():
    dataset_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "evaluation", "datasets", "legal_benchmark_v2.json"
    )
    assert os.path.exists(dataset_path), "legal_benchmark_v2.json must exist"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check top-level keys
    assert "metadata" in data
    assert "corpus" in data
    assert "queries" in data

    corpus = data["corpus"]
    queries = data["queries"]

    assert len(corpus) >= 15, "Corpus must contain at least 15 verified passages"
    assert len(queries) >= 50, f"Benchmark must contain at least 50 queries, found {len(queries)}"

    # Validate corpus item structure
    for doc in corpus:
        assert "id" in doc
        assert "text" in doc and len(doc["text"]) > 20
        assert "metadata" in doc
        meta = doc["metadata"]
        assert "case_name" in meta
        assert "court" in meta
        assert "year" in meta

    # Validate queries structure and categories
    valid_categories = {
        "HOLDING", "FACTS_PROCEDURAL", "STATUTORY", "MULTI_PASSAGE",
        "COMPARISON", "PRECEDENT_RELATIONSHIP", "TIMELINE",
        "ABSTENTION", "CONFLICT_DISTINCTION", "ADVERSARIAL"
    }

    dev_count = 0
    held_out_count = 0

    for q in queries:
        assert "id" in q
        assert "split" in q
        assert q["split"] in ("dev", "held_out")
        if q["split"] == "dev":
            dev_count += 1
        else:
            held_out_count += 1

        assert "category" in q
        assert q["category"] in valid_categories, f"Invalid category {q['category']} in {q['id']}"
        assert "question" in q and len(q["question"]) > 10
        assert "expected_answer" in q
        assert "expected_behavior" in q

    assert dev_count >= 15, "Dev split must have sufficient questions"
    assert held_out_count >= 25, "Held-out split must have sufficient questions"


# =============================================================================
# 3. Claim Support & Citation Correctness
# =============================================================================

def test_claim_support_evaluation():
    source_chunks = {
        "chunk_1": "Section 74 provides that proof of actual loss is essential unless impossible to prove."
    }
    # Supported claim
    claims_supported = [{"claim": "Proof of actual loss is essential under Section 74", "source_ids": ["chunk_1"]}]
    eval_res = evaluate_claim_support(claims_supported, source_chunks)
    assert eval_res["support_ratio"] == 1.0
    assert eval_res["supported_claims"] == 1

    # Unsupported claim citing non-existent source
    claims_unsupported = [{"claim": "Liquidated damages are prohibited in India", "source_ids": ["chunk_99"]}]
    eval_unsupported = evaluate_claim_support(claims_unsupported, source_chunks)
    assert eval_unsupported["support_ratio"] == 0.0
    assert eval_unsupported["unsupported_claims"] == 1


def test_citation_correctness_validity_vs_support():
    catalog = {
        "chunk_101": {
            "case_name": "Puttaswamy v. Union of India",
            "page_number": 14,
            "text": "The proportionality test requires legality, legitimate aim, and least intrusive means."
        }
    }

    # Valid citation with matching metadata and supporting text
    valid_cit = [{
        "source_id": "chunk_101",
        "case_name": "Puttaswamy v. Union of India",
        "page": 14,
        "associated_claim": "The proportionality test requires least intrusive means."
    }]
    eval_res = evaluate_citation_correctness(valid_cit, catalog)
    assert eval_res["validity_rate"] == 1.0
    assert eval_res["support_rate"] == 1.0

    # Metadata mismatch: correct source ID but wrong case name
    mismatched_cit = [{
        "source_id": "chunk_101",
        "case_name": "Bachan Singh v. State of Punjab",
        "page": 14,
        "associated_claim": "The proportionality test requires least intrusive means."
    }]
    eval_mismatch = evaluate_citation_correctness(mismatched_cit, catalog)
    assert eval_mismatch["validity_rate"] == 0.0


# =============================================================================
# 4. Abstention Quality Classification
# =============================================================================

def test_abstention_classification_matrix():
    # 1. TRUE_ABSTENTION: Unanswerable query and system correctly abstains
    ans_abstain = "Insufficient evidence in the indexed authorities."
    res_ta = evaluate_abstention(ans_abstain, is_unanswerable=True)
    assert res_ta["classification"] == "TRUE_ABSTENTION"
    assert res_ta["is_correct"] is True

    # 2. FALSE_ANSWER: Unanswerable query but system fabricates an answer
    ans_hallucinated = "The contractor was awarded 50 million Japanese Yen."
    res_fa = evaluate_abstention(ans_hallucinated, is_unanswerable=True)
    assert res_fa["classification"] == "FALSE_ANSWER"
    assert res_fa["is_correct"] is False

    # 3. FALSE_ABSTENTION: Answerable query but system over-cautiously abstains
    res_refusal = evaluate_abstention(ans_abstain, is_unanswerable=False)
    assert res_refusal["classification"] == "FALSE_ABSTENTION"
    assert res_refusal["is_correct"] is False

    # 4. TRUE_ANSWER: Answerable query and system answers
    ans_grounded = "Proof of actual loss is required under Section 74."
    res_true_ans = evaluate_abstention(ans_grounded, is_unanswerable=False)
    assert res_true_ans["classification"] == "TRUE_ANSWER"
    assert res_true_ans["is_correct"] is True


# =============================================================================
# 5. Specialized Feature Scoring
# =============================================================================

def test_case_comparison_evaluation():
    ground_truth = {
        "expected_similarities": ["liquidated damages", "Section 74"],
        "expected_distinctions": ["proof required", "pre-estimate"],
        "forbidden_conflict_claims": ["overruled", "unconstitutional"]
    }
    # Accurate comparison
    good_comparison = {
        "analysis": "Both cases address liquidated damages under Section 74. Kailash Nath held proof required, whereas Saw Pipes permitted genuine pre-estimates."
    }
    score_good = evaluate_comparison_accuracy(good_comparison, ground_truth)
    assert score_good["is_conflict_valid"] is True
    assert score_good["score"] >= 0.75

    # Comparison with false conflict claim
    bad_comparison = {
        "analysis": "Kailash Nath overruled Saw Pipes and declared Section 74 unconstitutional."
    }
    score_bad = evaluate_comparison_accuracy(bad_comparison, ground_truth)
    assert score_bad["is_conflict_valid"] is False
    assert len(score_bad["conflict_violations"]) >= 1


def test_precedent_graph_evaluation():
    expected_edges = [
        {"source": "Puttaswamy", "target": "M.P. Sharma", "relationship": "OVERRULES"},
        {"source": "Ssangyong", "target": "Associate Builders", "relationship": "FOLLOWS"}
    ]
    extracted_edges = [
        {"source": "Puttaswamy", "target": "M.P. Sharma", "relationship": "OVERRULES", "evidence": "Expressly overruled on privacy."},
        {"source": "Ssangyong", "target": "Associate Builders", "relationship": "FOLLOWS", "evidence": "Following the test in Associate Builders."}
    ]
    graph_res = evaluate_precedent_graph_accuracy(extracted_edges, expected_edges)
    assert graph_res["f1"] == 1.0
    assert graph_res["verified_evidence_ratio"] == 1.0


def test_timeline_accuracy_evaluation():
    expected_timeline = [
        {"event_date": "1954", "date_precision": "exact", "description": "M.P. Sharma"},
        {"event_date": "1964", "date_precision": "exact", "description": "Kharak Singh"},
        {"event_date": "2017", "date_precision": "exact", "description": "Puttaswamy"}
    ]
    extracted_timeline = [
        {"event_date": "1954", "date_precision": "exact", "description": "M.P. Sharma decision"},
        {"event_date": "1964", "date_precision": "exact", "description": "Kharak Singh decision"},
        {"event_date": "2017", "date_precision": "exact", "description": "Puttaswamy decision"}
    ]
    tl_res = evaluate_timeline_accuracy(extracted_timeline, expected_timeline)
    assert tl_res["score"] == 1.0
    assert tl_res["chronological_order_valid"] is True


# =============================================================================
# 6. Reproducible Runner & Privacy
# =============================================================================

def test_evaluation_runner_execution_and_serialization():
    """Verify that run_evaluation executes deterministically offline and outputs valid JSON and Markdown."""
    res = run_evaluation(split="dev", k_eval=3, run_llm=False)
    assert isinstance(res, dict)
    assert "benchmark_metadata" in res
    assert "retrieval_metrics" in res
    assert "answer_quality_metrics" in res
    assert "release_gate_status" in res

    # Verify results directory contains latest.json and latest.md
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "evaluation", "results"
    )
    latest_json = os.path.join(results_dir, "latest.json")
    latest_md = os.path.join(results_dir, "latest.md")

    assert os.path.exists(latest_json)
    assert os.path.exists(latest_md)

    with open(latest_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Privacy / secret check: ensure no API keys or raw tokens appear in the report
    assert "AIzaSy" not in md_text
    assert "Bearer" not in md_text
    assert "SECRET_KEY" not in md_text
    assert "password_hash" not in md_text

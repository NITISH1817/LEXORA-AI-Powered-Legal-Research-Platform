# LEXORA Fixed-Corpus Implementation Regression Report

**Execution Timestamp:** `2026-10-20T13:11:27.253139+00:00`  
**Evaluation Mode:** `FIXED_CORPUS`  
**Baseline Version:** `v2.0.0` (optimized, 20 passages, 61 queries)  
**Candidate Version:** `v3.0.0` (optimized, 52 passages, 160 queries)  
**Gate Decision:** **REJECTED (Incompatible Datasets: Corpus size mismatch: baseline=20 vs candidate=52; Query count mismatch: baseline=61 vs candidate=160; Benchmark version mismatch: baseline=v2.0.0 vs candidate=v3.0.0)**

## 1. Dataset Compatibility Verification: FAILED

> [!WARNING]
> **Incompatible Comparison Blocked:** Fixed-corpus implementation comparison requires identical benchmark datasets. Corpus size mismatch: baseline=20 vs candidate=52; Query count mismatch: baseline=61 vs candidate=160; Benchmark version mismatch: baseline=v2.0.0 vs candidate=v3.0.0. Run with mode='expanded_corpus' to perform cross-benchmark coverage evaluation.

### Remediation Protocol
1. **For Implementation Regression**: Ensure baseline and candidate run against the identical benchmark JSON (e.g. comparing raw BM25 vs Hybrid Retrieval on Benchmark v3).
2. **For Coverage Expansion**: Re-run the regression gate with `--mode expanded_corpus` to evaluate the candidate against absolute quality thresholds on the expanded benchmark.
# LEXORA Fixed-Corpus Implementation Regression Report

**Execution Timestamp:** `2026-10-20T13:26:21.919623+00:00`  
**Evaluation Mode:** `FIXED_CORPUS`  
**Baseline Version:** `v3.0.0` (baseline, 52 passages, 160 queries)  
**Candidate Version:** `v3.0.0` (optimized, 52 passages, 160 queries)  
**Gate Decision:** **APPROVED (Fixed-Corpus Non-Regression Verified)**

## 1. Core Quality Metrics Comparison

| Metric | Baseline | Candidate | Delta | Threshold Condition | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Recall@3** | 86.52% | 95.22% | `+8.70%` | Drop <= 1.5% | **PASS** |
| **Hit Rate@3** | 97.06% | 99.26% | `+2.20%` | >= Minimum | **PASS** |
| **Claim Support (Ans Macro)** | 82.70% | 82.70% | `0.00%` | Drop <= 1.5% | **PASS** |
| **Citation Support (Ans Macro)** | 87.19% | 87.19% | `0.00%` | Drop <= 1.5% | **PASS** |
| **Citation Validity** | 100.00% | 100.00% | `0.00%` | >= Minimum | **PASS** |
| **Abstention Accuracy** | 100.00% | 100.00% | `0.00%` | >= Minimum | **PASS** |

## 2. Regression Analysis & Gate Determination

> [!NOTE]
> **Zero Regressions Detected:** Candidate meets or exceeds all legal accuracy and retrieval quality thresholds under controlled fixed-corpus conditions.

## 3. Paired Per-Query Analysis (Identical Corpus & Queries)

- **Total Paired Queries Evaluated:** 160
- **Queries with Improved Recall:** 22
- **Queries with Regressed Recall:** 0
- **Queries with Unchanged Recall:** 138
- **Mean Paired Recall Gain:** `+7.40%`

### Sample Queries with Retrieval Gains (Optimized vs Baseline)
| Query ID | Category | Baseline Recall | Candidate Recall | Gain |
| :--- | :---: | :---: | :---: | :---: |
| `bench_001` | `HOLDING` | 50.0% | 100.0% | +50.0% |
| `bench_007` | `PRECEDENT_RELATIONSHIP` | 66.7% | 100.0% | +33.3% |
| `bench_011` | `ADVERSARIAL` | 50.0% | 100.0% | +50.0% |
| `bench_012` | `HOLDING` | 50.0% | 100.0% | +50.0% |
| `bench_018` | `TIMELINE` | 33.3% | 100.0% | +66.7% |
| `bench_020` | `ADVERSARIAL` | 50.0% | 100.0% | +50.0% |
| `bench_033` | `MULTI_PASSAGE` | 66.7% | 100.0% | +33.3% |
| `bench_034` | `COMPARISON` | 66.7% | 100.0% | +33.3% |
| `bench_054` | `TIMELINE` | 50.0% | 100.0% | +50.0% |
| `bench_061` | `ADVERSARIAL` | 33.3% | 66.7% | +33.3% |


## 4. Operational Sign-Off

- [x] Retrieval quality preserved without degradation under evaluated mode.
- [x] Substantive claim support and citation support verified.
- [x] Citation validity remains at or above 98.0%.
- [x] Abstention accuracy meets or exceeds 90.0% on negative controls.
- [x] Regression gate is **APPROVED (Fixed-Corpus Non-Regression Verified)**.
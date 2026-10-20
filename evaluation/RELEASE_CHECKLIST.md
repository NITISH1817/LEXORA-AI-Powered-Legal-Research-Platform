# LEXORA Operational Release Gate Checklist

**Version:** 1.0.0  
**Phase:** Phase 14 — Human Legal Validation & Evidence-Based Pilot Expansion  
**Governance Policy:** Non-Autonomous Deployment Protection  
**Mandate:** A passing automated software test suite **MUST NOT** automatically grant approval for expanded deployment or operational release. Approval requires independent human sign-off across all eight operational verification gates.

---

## 1. Release Evaluation Framework

Deployment decisions are strictly governed by the following three-tier framework:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GATE EVALUATION STATUS                          │
├───────────────────────┬────────────────────────────────────────────────┤
│ REJECTED              │ Any single critical failure in Gates 1–8.      │
│                       │ Zero deployment authorized.                    │
├───────────────────────┼────────────────────────────────────────────────┤
│ LIMITED CONTROLLED    │ Technical, privacy, and comparison gates pass. │
│ PILOT (CONDITIONAL)   │ Expanded corpus gold labels remain pending     │
│                       │ human review. Restricted to internal/supervised│
│                       │ designated advocates only.                     │
├───────────────────────┼────────────────────────────────────────────────┤
│ EXPANDED SUPERVISED   │ All 8 gates fully satisfied. Minimum 100 gold  │
│ PILOT                 │ labels human-approved. Live 72-hr triage test  │
│                       │ verified. Practitioner evidence recorded.      │
└───────────────────────┴────────────────────────────────────────────────┘
```

---

## 2. The Eight Operational Release Gates

### Gate 1: Benchmark Schema & Provenance Validation
- [x] **Schema Conformance:** `legal_benchmark_v3.json` validates against the canonical schema (52 passages, 160 queries: 70 dev, 90 held-out; 136 answerable, 24 negative controls).
- [x] **Official Provenance Check:** Every passage excerpt maps to an authentic Indian statutory enactment or judicial decision with verifiable citations (e-SCR, SCC, AIR, ILR, Gazette of India).
- [x] **Anti-Hallucination Integrity:** No synthetic or AI-fabricated legal propositions exist in the benchmark ground truth dataset.

### Gate 2: Compatible Baseline/Candidate Comparison
- [x] **Dual-Mode Regression Architecture:**
  - `fixed_corpus`: Compares baseline and candidate implementations on **identical** corpus, queries, and relevance judgments.
  - `expanded_corpus`: Evaluates expanded benchmark independently, explicitly labeled as a new baseline rather than an implementation regression.
- [x] **Incompatibility Rejection:** Regression gate strictly aborts (exit code 1) if comparing disparate corpus sizes or mismatched query sets under `fixed_corpus` mode.
- [x] **Paired Query Tracking:** Fixed-corpus evaluation outputs paired per-query differences (`improved`, `regressed`, `unchanged`).

### Gate 3: No Unexplained Critical Regression
- [x] **Fixed-Corpus Non-Regression Verified:** Hybrid Legal Retrieval candidate demonstrates **0 regressed queries** and **+7.40% mean paired recall gain** over BM25 baseline on Benchmark v3.
- [x] **Answerable Recall Threshold:** Recall@3 $\ge 90.0\%$ (Benchmark v3 actual: **95.22%**).
- [x] **Abstention Boundary Defense:** Zero missed abstentions on negative-control queries ($N=24$, actual: **100.0% abstention precision**).

### Gate 4: Human Legal Approval for Authoritative Gold Labels
- [ ] **Prohibition of Automated Approvals:** Enforced in code via `AutomatedApprovalForbiddenError`. Automated evaluation runs cannot mark items as `APPROVED`.
- [ ] **Dual Human Review Status:** Expanded benchmark items (Benchmark v3) currently hold `PENDING_HUMAN_LEGAL_REVIEW` status in `evaluation/results/legal_review_queue.json`.
- [ ] **Authoritative Label Gate:** Items without verified human legal review are clearly marked as *provisional* and cannot serve as unchallengeable legal gold truth.
- *Gate Status:* **PENDING HUMAN REVIEW (Blocks unconstrained release; permits conditional controlled pilot only).**

### Gate 5: Verified Citation-Support Evaluation
- [x] **Separation of Metrics:** Citation metadata validity and actual passage evidentiary support are evaluated as separate, non-conflated metrics.
- [x] **Citation Validity Rate:** **100.0%** across answerable query evaluations.
- [x] **Atomic Claim Support Rate:** Evaluated via claim decomposition (Macro: **82.70%**, Micro: **83.15%** on Benchmark v3 answerable queries).
- [x] **Passage Evidentiary Support:** Citation support macro **87.19%** on answerable queries.

### Gate 6: Security, Auth & Privacy Regression Tests
- [x] **Zero Query Leakage:** Default setting `PILOT_MONITORING_LOG_QUERIES=False` prevents query persistence.
- [x] **PII & Credential Scrubbing:** Regex filter scrubs API keys, auth tokens, client emails, and sensitive identifiers.
- [x] **Tenant & User Isolation:** Non-admin callers cannot access telemetry outside their own authenticated `user_id`.
- [x] **Right to Be Forgotten:** `DELETE /api/evaluation/monitoring/my-events` completely purges user telemetry and feedback records.
- [x] **Authentication & RBAC:** Evaluated routes enforce `ADMIN`, `RESEARCHER`, and authenticated user role hierarchies.

### Gate 7: Visible Legal Disclaimer & Corpus-Scope Notice
- [x] **Mandatory Disclaimer Banner:** Frontend renders persistent legal disclaimer warning that outputs are assistive AI syntheses requiring independent attorney verification.
- [x] **Jurisdictional Scope Statement:** Explicit notification that system covers Indian Union legislation and Supreme Court/High Court precedents within indexed scope.
- [x] **Prohibition of Direct Court Submission:** Prominent notification that unverified AI generations cannot be submitted directly to any court, tribunal, or statutory authority.

### Gate 8: Documented Unresolved Risks & Reviewer Escalation Procedure
- [x] **Prioritized Risk Register:** `evaluation/LEGAL_ACCURACY_RISK_REGISTER.md` actively maintained with mitigation strategies for 8 critical failure modes (e.g. Ratio vs Obiter, Overruled Precedents, State Legislation, Fact vs Allegation).
- [x] **Priority Review Queue:** `evaluation/LEGAL_REVIEW_QUEUE.md` categorizes 160 queries by risk tier (8 Critical, 65 High, 42 Medium, 45 Standard).
- [x] **72-Hour Triage SLA:** Operational protocol documented in `evaluation/PILOT_MEASUREMENT_PROTOCOL.md` with assigned escalation paths.
- [x] **Source Acquisition Checklist:** Manual source gathering checklist established for unindexed or newly amended statutory provisions.

---

## 3. Operational Sign-Off Matrix

| Operational Role | Reviewer Sign-Off | Gate Responsibilities | Sign-Off Status | Date |
| :--- | :--- | :--- | :--- | :--- |
| **Head of AI / ML Engineering** | *Engineering Verification* | Gates 1, 2, 3, 5 | **PASSED** (144 backend tests, build passed, fixed-corpus non-regression verified) | 2026-10-20 |
| **Privacy & Security Officer** | *Security & Compliance* | Gates 6, 7 | **PASSED** (Tenant isolation, PII scrubbing, zero query leakage verified) | 2026-10-20 |
| **Lead Legal Adjudicator** | *Practicing Advocate Sign-Off* | Gates 4, 8 | **CONDITIONALLY PASSED FOR CONTROLLED PILOT ONLY** (Human review queue generated; full dual-review on Benchmark v3 pending) | 2026-10-20 |

---

## 4. Final Operational Release Gate Determination

```
========================================================================================
FINAL DECISION: LIMITED CONTROLLED PILOT — CONTINUE WITH CONDITIONS
========================================================================================
Justification:
1. All technical regression gates, fixed-corpus retrieval benchmarks, and security/privacy
   controls have achieved 100% verification.
2. The apples-to-apples evaluation methodology has been successfully corrected.
3. The human legal review and adjudication workflow has been fully implemented with strict
   anti-fabrication safeguards.
4. However, the 160 expanded benchmark items in Benchmark v3 remain pending human legal review
   by qualified advocates.
5. In addition, pilot monitoring storage currently contains zero genuine external practitioner
   records (EMPTY STATE).
6. Therefore, while evidence does NOT yet support an unconstrained or expanded public pilot,
   it DOES fully support continuation of the LIMITED CONTROLLED PILOT with supervised
   internal advocates.
========================================================================================
```

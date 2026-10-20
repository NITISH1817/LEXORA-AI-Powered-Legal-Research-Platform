# LEXORA Supervised Pilot Measurement Protocol

**Version:** 1.0.0  
**Phase:** Phase 14 — Human Legal Validation & Evidence-Based Pilot Expansion  
**Classification:** Confidential — Supervised Legal Research Protocol  
**Regulatory Notice:** Strict Compliance with Bar Council of India (BCI) Professional Standards & Non-Autonomous Decision Safeguards. Autonomous legal citation or direct court submission without human advocate verification is strictly prohibited.

---

## 1. Executive Purpose & Governance

This protocol establishes the rigorous, privacy-safe, empirical measurement framework for conducting a **supervised, controlled pilot** of the LEXORA AI-Powered Legal Intelligence & Research Platform with designated practicing advocates and legal researchers in India.

### Core Governance Principles
1. **Human-in-the-Loop Supremacy:** LEXORA operates strictly as an assistive legal intelligence tool. All generated propositions, citations, and summaries must be independently validated by a qualified advocate prior to professional use.
2. **Empirical Evidence Over Subjective Ratings:** Pilot success is determined by objective citation verification, atomic claim support, and abstention compliance—**not** user satisfaction scores or perceived responsiveness.
3. **Strict Confidentiality & Privacy Preservation:** No privileged client communications, attorney work product, or raw query text are exposed in aggregate reporting without express consent and cryptographic redaction.
4. **Mandatory 72-Hour Triage SLA:** Any flagged legal hallucination, inaccurate citation, or failure to abstain must be triaged, investigated, and adjudicated within 72 hours.
5. **No Data Fabrication:** If genuine pilot data is unavailable, the system explicitly reports an **EMPTY STATE**; under no circumstances are synthetic acceptance tests conflated with genuine practitioner sessions.

---

## 2. Participant Eligibility & Cohort Architecture

The supervised pilot cohort is limited to designated legal practitioners meeting the following criteria:

| Participant Role | Minimum Qualifications | Authorized Permissions | Assigned Responsibilities |
| :--- | :--- | :--- | :--- |
| **Lead Legal Adjudicator** | Advocate with ≥ 10 years Bar experience or retired judicial officer | `ADMIN`, `ADJUDICATOR` | Final adjudication of conflicting authorities, overruling determinations, escalation sign-off. |
| **Pilot Research Advocate** | Enrolled Advocate (State Bar Council) with ≥ 3 years litigation/research experience | `RESEARCHER` | Daily research tasks, structured qualitative feedback, flagging inaccurate citations/holdings. |
| **Legal Annotation Reviewer** | Law graduate or advocate specializing in constitutional/commercial law | `REVIEWER` | Dual-review verification of benchmark questions against official law reports (SCR, SCC, AIR). |
| **System Operator** | Security and ML systems engineer | `OPERATOR` | Privacy audit, telemetry health, latency profiling, system availability maintenance. |

---

## 3. Empirical Measurement Dimensions & Formulas

The pilot telemetry engine (`PilotMonitoringService` via `backend/services/monitoring_service.py`) captures eight distinct evaluation dimensions:

### 3.1. Query Success & Retrieval Relevance
- **Metric Definition:** Proportion of queries returning authoritative passages directly containing the ratio decidendi or statutory provision.
- **Formulas:**
  $$\text{Hit Rate@3} = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{rank}(d^*_q) \le 3)$$
  $$\text{MRR@3} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}(d^*_q)}$$
- **Target Threshold:** Hit Rate@3 $\ge 95.0\%$, MRR@3 $\ge 0.85$.

### 3.2. Citation Support & Validity Separation
To prevent conflating citation format validity with evidentiary truth, the system tracks two separate metrics:
- **Citation Metadata Validity Rate:** Percentage of generated citations that resolve to authentic Indian legal reporters (SCR, SCC, AIR, INSC, ILR).
  $$\text{Citation Validity} = \frac{\text{Validly Formatted Reporter Citations}}{\text{Total Citations Emitted}}$$
- **Citation Evidentiary Support Rate:** Percentage of citations where the cited excerpt explicitly substantiates the generated legal proposition.
  $$\text{Citation Support} = \frac{\text{Citations Where Cited Passage Directly Proves Proposition}}{\text{Total Citations Checked}}$$
- **Target Threshold:** Citation Validity $= 100\%$, Citation Support $\ge 85.0\%$.

### 3.3. Atomic Legal Claim Support (Macro & Micro)
- **Metric Definition:** Generation is decomposed into atomic legal assertions ($c_1, c_2, \dots, c_k$). Each claim is evaluated against retrieved excerpts.
- **Formulas:**
  $$\text{Micro Claim Support} = \frac{\sum_{i=1}^{|Q|} \text{Supported Claims}_i}{\sum_{i=1}^{|Q|} \text{Total Claims}_i}$$
  $$\text{Macro Claim Support} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{\text{Supported Claims}_i}{\text{Total Claims}_i}$$
- **Target Threshold:** Macro Claim Support $\ge 80.0\%$.

### 3.4. Abstention Precision & Recall (Negative Controls)
- **Metric Definition:** The system's ability to decline answering when queried on out-of-corpus law, false premises, or non-existent precedents.
- **Categories Tracked:**
  - *Correct Abstention ($CA$):* System accurately refuses unanswerable or false-premise questions.
  - *False Refusal ($FR$):* System abstains despite indexed authoritative passages being present.
  - *Missed Abstention / Hallucination ($MA$):* System generates a substantive answer for an ungrounded or fictitious prompt.
- **Target Threshold:** $MA = 0$ (Zero tolerance for hallucinated answers on negative controls).

### 3.5. Comparison & Timeline Fidelity
- **Metric Definition:** Accuracy in multi-case comparison and chronological procedural progression.
- **Error Types Tracked:**
  - `COMPARISON_FALSE_CONFLICT`: Synthesizing non-existent legal conflict between harmonious judgments.
  - `TIMELINE_DATE_MISATTRIBUTION`: Confusing date of cause of action, High Court appeal, and Supreme Court final judgment.
- **Target Threshold:** Misattribution error rate $< 5.0\%$.

### 3.6. Provider Latency & Availability
- **Metrics Tracked:**
  - $P_{50}, P_{95}, P_{99}$ query-to-response latency (seconds).
  - Upstream provider fallback rate (Gemini API 429/503 rate limits $\to$ local extractive fallback).
- **Target Threshold:** $P_{95} \le 8.5\text{s}$, System Availability $\ge 99.5\%$.

### 3.7. User-Flagged Issues & Time-to-Triage
- **Metric Definition:** Rate of practitioner flags submitted via `POST /api/evaluation/monitoring/feedback` and elapsed time to senior adjudicator review.
- **Target SLA:** 100% of flagged accuracy issues triaged within 72 hours.

### 3.8. Reviewer Disposition & Correction Lifecycle
- **Status Progression:** `PENDING` $\to$ `IN_REVIEW` $\to$ `APPROVED` / `REJECTED` / `NEEDS_ADJUDICATION`.
- **Target Metric:** 100% auditable provenance for every accepted benchmark or ground truth update.

---

## 4. Privacy, Tenant Isolation & Confidentiality Safeguards

All pilot telemetry operates under hardened privacy controls compliant with attorney-client confidentiality:

```
[Practitioner Query] ──► [Hash / Masking Filter] ──► [Audit Log: [REDACTED_BY_DEFAULT]]
                               ▲
                               │
               PILOT_MONITORING_LOG_QUERIES = False
```

1. **Zero Raw Query Retention in Default Mode:**
   - Setting `PILOT_MONITORING_LOG_QUERIES=False` ensures that query text is completely omitted from persistent disk storage.
   - When query logging is explicitly authorized for debugging, all personal identifiers (parties, email addresses, phone numbers, Aadhaar/PAN, case numbers) are sanitized via regex masking before persistence.
2. **Strict User & Tenant Isolation:**
   - Endpoint `GET /api/evaluation/monitoring/my-events` enforces strict ownership filtering: practitioners can only inspect their own session logs.
   - Aggregate reporting (`GET /api/evaluation/monitoring/summary`) contains only count aggregates, latency distributions, and sanitized issue tallies—never raw text.
3. **Data Subject Rights (Right to be Forgotten):**
   - Practitioners can purge all associated telemetry and feedback at any time via `DELETE /api/evaluation/monitoring/my-events`.
4. **Time-Based Rolling Expiration:**
   - Telemetry logs are purged on a rolling 30-day lifecycle (`PILOT_MONITORING_RETENTION_DAYS = 30`).
5. **Separation of Synthetic and Genuine Sessions:**
   - Automated regression tests and health probes emit `test_session=true` telemetry headers. The feedback analysis engine explicitly filters out these sessions, ensuring zero synthetic contamination of pilot metrics.

---

## 5. Mandatory 72-Hour Legal Accuracy Triage SLA

```
Hour 0                Hour 4               Hour 24              Hour 48              Hour 72
───┼────────────────────┼────────────────────┼────────────────────┼────────────────────┼───►
Feedback       Automated Severity       Lead Advocate        Root Cause        Remediation Deployed
Logged          & Ticket Assigned        Case Review         Determined        & Pilot Notified
```

### SLA Workflow Breakdown:

1. **Intake & Triage (0 – 4 Hours):**
   - User flags issue via feedback UI (`POST /api/evaluation/monitoring/feedback`).
   - If issue matches `CLAIM_UNSUPPORTED_BY_PASSAGE`, `CITATION_METADATA_INVALID`, or `ABSTENTION_MISSED_HALLUCINATED_ANSWER`, incident is classified as **P1 CRITICAL**.
   - Alert dispatched to Lead Legal Adjudicator and On-call Engineer.

2. **Substantive Legal Review (4 – 24 Hours):**
   - Assigned legal reviewer inspects the prompt, retrieved passages, and model generation.
   - Reviewer pulls official law reporter judgment from the authoritative digital repository (e-SCR / SCI website).
   - Reviewer records: (a) actual holding, (b) verified paragraph number, (c) nature of error (retrieval vs synthesis).

3. **Technical Root-Cause Analysis (24 – 48 Hours):**
   - Engineering determines if error originated from:
     - *Chunking boundary truncation* (ratio decidendi split across chunks).
     - *BM25/Dense retrieval mismatch* (statutory section keyword missed).
     - *LLM reasoning hallucination* (incorrect synthesis despite correct context).
     - *Unresolved precedent tension* (overruling judgment omitted from index).

4. **Remediation & Closure (48 – 72 Hours):**
   - Legal reviewer inputs corrected ground-truth into the adjudication queue (`evaluation/review_workflow.py`).
   - If corpus defect: Missing judgment or paragraph is re-indexed with verified metadata.
   - If prompting/reasoning defect: System prompt guardrail or few-shot exemplar updated.
   - Regression test added to test suite to prevent recurrence.
   - Ticket closed with formal written adjudication note signed by Lead Adjudicator.

---

## 6. Current Pilot Store Empirical Status

```json
{
  "pilot_status": "EMPTY_STATE",
  "active_external_users": 0,
  "pilot_feedback_records": 0,
  "pilot_events_records": 0,
  "empirical_conclusion": "NO_EMPIRICAL_PILOT_CONCLUSIONS_CAN_BE_DRAWN"
}
```

> [!IMPORTANT]
> **Audit Finding (Phase 14):**  
> As of Phase 14 verification, the pilot feedback storage (`./storage/monitoring`) contains **zero genuine external legal practitioner records**.  
> In accordance with Task 6 directives, **no empirical conclusions regarding real-world legal practitioner efficacy are claimed.** All operational telemetry reported herein reflects synthetic acceptance tests and automated verification suites.

---

## 7. Pilot Expansion Criteria (Phase 14 Exit Gate)

Transition from **Limited Controlled Pilot** to **Expanded Supervised Pilot** requires satisfying all of the following conditions:
1. **Benchmark v3 Gold Label Approval:** Minimum 100 queries in Benchmark v3 approved by dual human legal review.
2. **Practitioner Pilot Cohort Onboarding:** Minimum 5 practicing advocates enrolled under signed BCI-compliant pilot agreements.
3. **Operational Triage Verification:** At least one live triage simulation demonstrating 72-hour turnaround on a flagged holding discrepancy.
4. **Zero Unmitigated P1 Vulnerabilities:** Zero unresolved issues in the prioritized Legal Accuracy Risk Register.

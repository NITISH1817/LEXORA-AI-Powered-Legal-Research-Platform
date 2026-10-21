# LEXORA — Phase 20 External Dependency & Human Action Tracker

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Version:** 1.0.0 (Phase 20 Operational Dependency Register)  
**Execution Timestamp:** `2026-10-21T16:30:00Z`  
**Governing Baseline:** Benchmark v3.0.0 (52 Passages, 160 Queries: 70 Dev, 90 Held-Out)  
**Overall Operational State:** **ACTIVATION BLOCKED — HUMAN / INSTITUTIONAL DEPENDENCIES OUTSTANDING**  

---

## 1. Governance & Anti-Fabrication Notice

> [!IMPORTANT]
> **COMPLETION INTEGRITY RULE:**
> Under project governance, a status can **never** be marked as `COMPLETED` without tangible, verifiable supporting evidence (e.g., signed PDF agreement, verified Bar Council roll number, immutable audit log entry in `review_audit_log.json`).
> - Passing automated software tests does not satisfy institutional or human legal requirements.
> - No fictional reviewer names or synthetic approvals may be substituted for real practitioners.

---

## 2. External Dependency & Human Action Matrix

| Dependency ID | Requirement Name | Current Status | Blocking Severity | Evidence Required | Responsible Human Role | Next Action Required | Objective Completion Criteria |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| **DEP-01** | **Institutional Partnership Agreement (MoU)** | **BLOCKED** | **CRITICAL BLOCKER** | Bilateral Memorandum of Understanding signed by LEXORA governance and institutional partner. | Institutional Partner & LEXORA Project Director | Transmit outreach draft ([`PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md)) and finalize bilateral MoU. | Executed and countersigned institutional agreement on file. |
| **DEP-02** | **Data Processing & Confidentiality Agreement (DPA)** | **NOT_STARTED** | **HIGH** | Formal DPA specifying zero-query-retention and GDPR/DPDP Act 2023 compliance. | Partner Compliance Officer & LEXORA Privacy Lead | Draft partner-specific DPA schedule upon execution of MoU. | Signed bilateral Data Processing Agreement executed. |
| **DEP-03** | **Verified Reviewer Identity & Standing** | **BLOCKED** | **CRITICAL BLOCKER** | Active State Bar Council roll numbers ($\ge 7$ yrs appellate litigation) or university faculty appointment letters. | Candidate Advocates & Compliance Officer | Collect and verify Bar enrollment numbers for candidate panel members. | Bar Council verification record archived for each active reviewer ID. |
| **DEP-04** | **Assignment of Eight Critical Review Packets** | **NOT_STARTED** | **HIGH** | Explicit assignment records linking verified reviewer IDs to `bench_093`..`bench_007`. | Review Coordinator & Senior Advocate Panel | Provision reviewer accounts and dispatch handoff dossiers ([`PHASE20_HUMAN_REVIEW_HANDOFF.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE20_HUMAN_REVIEW_HANDOFF.md)). | All 8 critical items formally claimed via `submit_human_review.py --claim`. |
| **DEP-05** | **Advocate Review Completion & Adjudication** | **BLOCKED** | **CRITICAL BLOCKER** | Verified reporter citations, completed rubric scores, and signed substantive rationales in `review_audit_log.json`. | Practicing Advocate Panel & Senior Adjudicator | Advocates execute 4-step review lifecycle via CLI. | 8/8 critical packets transitioned to `APPROVED` with substantive rationales. |
| **DEP-06** | **Pilot Participant Authorization & Onboarding** | **BLOCKED** | **CRITICAL BLOCKER** | Signed non-reliance disclaimers and individual account credentials for designated seats (`pilot_res_01`–`pilot_res_05`). | Designated Legal Researchers & IT Administrator | Execute onboarding briefing and provision authenticated accounts via admin API. | 5 verified researcher accounts provisioned with acknowledged disclaimers. |
| **DEP-07** | **Approved-Label Benchmark Evaluation** | **BLOCKED** | **HIGH** | Execution of `evaluation.evaluator --approved-only` producing valid precision/recall metrics on approved items. | Evaluation Engineer & Benchmark Lead | Run evaluation once approved gold labels are recorded in the review registry. | Evaluation generates non-empty report with valid sample size without exception. |
| **DEP-08** | **Supervised Pilot Evidence Collection** | **NOT_STARTED** | **MEDIUM** | Real telemetry entries in `./storage/monitoring` reflecting live researcher queries and feedback tickets. | Pilot Researchers & Triage Officer | Activate live research access after Gates 1–8 are satisfied; triage feedback tickets. | Real practitioner feedback records logged and triaged under 72-hour SLA. |

---

## 3. Dependency Lifecycle & Sequencing Workflow

The dependencies must be resolved in strict chronological sequence:

```
[ DEP-01: Bilateral MoU Executed ]
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
[ DEP-02: DPA Executed ]              [ DEP-03: Bar Identity Verified ]
               │                                        │
               │                                        ▼
               │                      [ DEP-04: Critical Packets Assigned ]
               │                                        │
               │                                        ▼
               │                      [ DEP-05: Advocate Review Completed (8/8) ]
               │                                        │
               │                                        ▼
               │                      [ DEP-07: Approved-Only Evaluation Scored ]
               │                                        │
               └───────────────────┬────────────────────┘
                                   │
                                   ▼
          [ DEP-06: Pilot Participant Credentials Provisioned ]
                                   │
                                   ▼
          [ DEP-08: Supervised Pilot Evidence Collection Active ]
```

---

## 4. Current Blockers & Next Actions Summary

| Requirement | Current Status | Primary Blocker | Immediate Action | Owner |
| :--- | :---: | :--- | :--- | :--- |
| **Institutional Authorization** | `BLOCKED` | Bilateral agreement template unexecuted | Transmit outreach package to potential partner | Project Director |
| **Reviewer Panel Standing** | `BLOCKED` | No live practitioner credentials on file | Vet prospective advocate bar enrollments | Compliance Lead |
| **Critical Review Execution** | `BLOCKED` | 0/8 critical items claimed or approved | Await panel onboarding and dispatch dossiers | Review Coordinator |
| **Gold-Label Evaluation** | `BLOCKED` | 0 approved queries in benchmark catalog | Evaluate only after advocate approvals occur | Evaluation Lead |
| **Live Pilot Activation** | `BLOCKED` | Gates 1, 2, and 8 remain unresolved | Maintain activation gate block; enforce standby | Systems Administrator |

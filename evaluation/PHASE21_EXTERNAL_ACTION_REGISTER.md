# LEXORA — Phase 21 External Action & Human Dependency Register

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Version:** 1.0.0 (Phase 21 Action Register)  
**Execution Timestamp:** `2026-10-21T18:00:00Z`  
**Governing Baseline:** Benchmark v3.0.0 (52 Passages, 160 Queries: 70 Dev, 90 Held-Out)  
**Operational State:** **ACTIVATION BLOCKED — EXTERNAL DEPENDENCIES OUTSTANDING**  

---

## 1. Operating Rules & Governance Mandate

> [!IMPORTANT]
> **INTEGRITY & ANTI-FABRICATION INVARIANTS:**
> 1. **No Automatic Completion:** A status can **never** be marked as `COMPLETED` based on an unsent draft, placeholder name, or assumption. Verifiable supporting evidence (signed agreement, Bar Council Certificate of Practice, immutable audit log record) is mandatory.
> 2. **No Fabricated Identities:** No fictitious advocate names, synthetic bar numbers, or imaginary institutional partners may be recorded.
> 3. **Clear Division of Responsibility:** Software engineers and AI models cannot substitute for licensed advocates, senior counsel, or institutional legal officers.
> 4. **Blocked Status is Valid:** Accurately documenting external blockers is the correct and honest operational outcome when external prerequisites are unresolved.

---

## 2. Master External Action Matrix

| Action ID | Operational Action Item | Current Status | Blocking Severity | Required Input / Evidence | Responsible Human Role | Dependency | Next Action Required | Blocker Closure Criteria |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **ACT-01** | **Bilateral Institutional Partnership Execution** | **BLOCKED** | **CRITICAL** | Formally signed Memorandum of Understanding (MoU) defining research scope, non-reliance terms, and supervised access. | Institutional Partner & LEXORA Project Director | None | Transmit proposal draft ([`PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md)) to authorized institutional representative. | Fully executed, countersigned bilateral agreement PDF archived in project records. |
| **ACT-02** | **Data Processing & Privacy Agreement (DPA)** | **BLOCKED** | **HIGH** | Executed DPA specifying telemetry masking, zero raw query retention, 30-day auto-purge, and DPDP Act 2023 compliance. | Partner Compliance Officer & LEXORA Privacy Lead | ACT-01 | Draft partner-specific data handling schedule once institutional partner is identified. | Signed DPA countersigned by both institutional legal counsels. |
| **ACT-03** | **Advocate Identity & Bar Registration Vetting** | **BLOCKED** | **CRITICAL** | Active State Bar Council Certificates of Practice ($\ge 7$ yrs standing) or official NLU faculty appointment letters. | Candidate Advocates & Compliance Officer | None | Receive real practitioner candidate submissions and verify standing via State Bar Council rolls. | State Bar Council roll verification record archived for each prospective reviewer ID. |
| **ACT-04** | **Advocate Panel Engagement & Handoff Dispatch** | **READY_TO_SEND** | **HIGH** | Explicit user authorization to dispatch outreach emails with verified recipient addresses. | Project Governance Lead & Outreach Coordinator | ACT-03 | User reviews email drafts, specifies verified practitioner recipient addresses, and authorizes dispatch. | Verifiable email delivery confirmation and signed engagement acknowledgment form. |
| **ACT-05** | **Reviewer Provisioning & Packet Assignment** | **NOT_STARTED** | **HIGH** | Verified reviewer IDs mapped to the eight critical benchmark packets (`bench_093`..`bench_007`). | Review Coordinator & Technical Admin | ACT-03, ACT-04 | Register authenticated reviewer IDs in workflow engine and dispatch dossiers ([`PHASE20_HUMAN_REVIEW_HANDOFF.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE20_HUMAN_REVIEW_HANDOFF.md)). | Items claimed in review registry (`scripts/submit_human_review.py --claim`). |
| **ACT-06** | **Primary Law Reporter Volume Audit** | **PENDING** | **HIGH** | Physical inspection of official law reports (SCR, SCC, AIR) for cited paragraphs and statutory provisions. | External Practicing Advocate Panel | ACT-05 | Advocates examine primary reports and record verification citations via CLI. | 8/8 critical packets marked `SOURCE_VERIFIED` with official law report volume and paragraph citations. |
| **ACT-07** | **Advocate Rubric Scoring & Rationale Submission** | **PENDING** | **CRITICAL** | Multi-dimensional rubric scores ($\ge 4.0$ on ratio accuracy, citation sufficiency, procedural fidelity) and written substantive rationale. | Practicing Advocate Panel ($\ge 7$ yrs) | ACT-06 | Advocates submit rubric reviews and substantive legal justifications via CLI. | 8/8 critical packets marked `ANNOTATION_REVIEWED` with substantive legal reasoning recorded in audit log. |
| **ACT-08** | **Senior Adjudication of Doctrinal Disputes** | **NOT_STARTED** | **HIGH** | Independent senior counsel determination resolving contested holdings (anti-self-adjudication enforced). | Designated Senior Advocate / Retired Judge | ACT-07 (if disputed) | Senior adjudicator evaluates contested annotations and records binding determination. | Disputed items transitioned to `DISAGREEMENT_ADJUDICATED` and promoted to `APPROVED`. |
| **ACT-09** | **Gold-Label Benchmark Evaluation Execution** | **BLOCKED** | **HIGH** | Minimum 8 approved gold labels in benchmark catalog. | Evaluation Engineer & Benchmark Lead | ACT-07, ACT-08 | Run `python -m evaluation.evaluator --approved-only` against approved items. | Evaluator generates non-empty report with precision, recall, and citation validity scores. |
| **ACT-10** | **Pilot Participant Account Provisioning** | **BLOCKED** | **CRITICAL** | Verified Bar enrollment and signed non-reliance disclaimers for designated seats (`pilot_res_01`–`pilot_res_05`). | Lead Institutional Coordinator & IT Admin | ACT-01, ACT-02 | Execute onboarding briefing and provision researcher credentials via admin API. | 5 verified researcher accounts provisioned with acknowledged disclaimers and confirmed credentials. |
| **ACT-11** | **Supervised Pilot Activation & Feedback Intake** | **BLOCKED** | **HIGH** | Satisfaction of Gates 1 through 10 and formal release sign-off by Project Director. | Systems Administrator & Triage Officer | ACT-01, ACT-07, ACT-10 | Enable supervised access; ingest researcher feedback tickets under 72-hour SLA. | First genuine practitioner feedback records ingested and acknowledged in monitoring store. |

---

## 3. Immediate Human Action Checklist

The following actions require direct human execution by project leadership or prospective external partners:

1. **[ ] Executive Outreach Approval:** Review and authorize dispatch of the outreach email drafts in [`evaluation/PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE20_ADVOCATE_ENGAGEMENT_DRAFTS.md).
2. **[ ] Institutional Target Selection:** Identify candidate law school clinics, appellate law firms, or senior counsel chambers for institutional partnership.
3. **[ ] Bilateral Agreement Review:** Finalize terms of the Memorandum of Understanding and Data Processing Agreement.
4. **[ ] Advocate Panel Vetting:** Confirm Bar Council credentials and appellate standing of volunteer or participating reviewers.
5. **[ ] Dossier Review Sessions:** Coordinate four 90-minute review sessions across 2 weeks for the eight critical dossiers.

*Until the actions above are executed by authorized human personnel, LEXORA remains strictly in pre-activation standby.*

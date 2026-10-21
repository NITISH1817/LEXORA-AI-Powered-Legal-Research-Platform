# LEXORA — Phase 17 Institutional Pilot Onboarding Protocol & Access Governance

**Document Version:** 2.0.0  
**Phase:** Phase 17: Human Legal Review Execution & Institutional Pilot Activation  
**Execution Timestamp:** `2026-10-21T10:20:00Z`  
**Current Operational Status:** **PENDING INSTITUTIONAL PARTNERSHIP AGREEMENT & CREDENTIAL ISSUANCE**  
**Target Supervised Cohort:** 3–5 Designated Legal Researchers  

---

## 1. Executive Summary & Controlled Pilot Scope

This document specifies the operational access controls, institutional onboarding procedures, and non-reliance protocols governing the supervised pilot of the **LEXORA AI-Powered Legal Intelligence & Research Platform**.

In strict accordance with legal risk governance:
1. **Designated Participants Only:** Deployment is restricted exclusively to 3–5 pre-registered legal researchers (`pilot_res_01` to `pilot_res_05`). Public open registration is disabled in the backend.
2. **Mandatory Non-Reliance Acknowledgment:** Platform outputs represent AI-assisted legal research synthesis. They do **not** constitute legal advice, judicial determinations, or formal court filings. Practicing advocates and clerks must independently verify primary law report transcripts before court reliance.
3. **Strict Corpus Scope Disclaimers:** Users are presented with persistent UI disclaimers detailing that the active index is grounded exclusively against landmark Supreme Court of India judgments. Unindexed state High Court rules, local statutory enactments, and tribunal decisions remain outside the verified corpus.
4. **Anti-Fabrication Policy:** No simulated user feedback, fictitious star ratings, or synthetic research activity will be accepted as empirical pilot validation.

---

## 2. Designated Legal Researcher Cohort (3–5 Participants)

The supervised pilot cohort is structured around five specialized practice archetypes:

| Participant ID | Professional Role Archetype | Institutional Affiliation Seat | Doctrinal Evaluation Objective | Onboarding Status |
| :--- | :--- | :--- | :--- | :---: |
| **`pilot_res_01`** | **Constitutional Law Research Fellow** | National Law School Legal Aid Clinic | Evaluate *Puttaswamy* 9-judge unanimous ratio extraction, Article 21 evolution, and obiter isolation. | **PENDING AUTHORIZATION** |
| **`pilot_res_02`** | **Commercial Arbitration Associate** | Appellate Law Chambers, High Court | Audit Section 34(2A) patent illegality scope and 7-judge *In Re Interplay* stamping curability doctrine. | **PENDING AUTHORIZATION** |
| **`pilot_res_03`** | **Insolvency & Bankruptcy Specialist** | Corporate Restructuring Practice Group | Test IBC Section 53 waterfall ranking of unsecured financial debt relative to statutory tax claims. | **PENDING AUTHORIZATION** |
| **`pilot_res_04`** | **Appellate Litigation Law Clerk** | Supreme Court Registry / Judicial Chambers | Verify citation reporter authenticity (SCR/SCC/AIR) and chronological precedent timeline ordering. | **PENDING AUTHORIZATION** |
| **`pilot_res_05`** | **Senior Legal Research Annotator** | Academic Law Review Editorial Board | Test negative control queries, adversarial false-premise prompts, and principled system abstention. | **PENDING AUTHORIZATION** |

> [!NOTE]
> **Status Disclosure:** The above cohort profiles define designated operational seats. In adherence to anti-fabrication standards, **no accounts have been activated as active users until formal institutional partnership agreements and Bar Council credential verifications are finalized.**

---

## 3. Seven-Stage Onboarding Workflow

```
[ STAGE 1: Institutional Partnership Execution ]
             │
             ▼
[ STAGE 2: Advocate / Researcher Credential Verification ]
             │
             ▼
[ STAGE 3: Pre-Pilot Legal Limitations & Non-Reliance Briefing ]
             │
             ▼
[ STAGE 4: Administrator Account Provisioning (Designated Role & Invite) ]
             │
             ▼
[ STAGE 5: First-Session Verification of Safeguards & Excerpt Modal ]
             │
             ▼
[ STAGE 6: Supervised Query Execution & Telemetry Ingestion ]
             │
             ▼
[ STAGE 7: 72-Hour Feedback Triage & Disposition Tracking ]
```

---

## 4. Responsible Person Onboarding Checklist

The Institutional Pilot Coordinator must complete and sign this checklist before provisioning credentials for any participant:

- [ ] **Institutional Agreement:** Formal MoU or research participation agreement executed with participating law firm or university clinic.
- [ ] **Identity & Bar Standing:** Participant enrollment verified against Bar Council of India / State Bar rolls (or university faculty roll).
- [ ] **Non-Reliance Agreement Signed:** Participant signs an explicit acknowledgment confirming that LEXORA outputs must not be cited in judicial filings without independent reporter verification.
- [ ] **Corpus Scope Understood:** Participant briefed on the landmark Supreme Court boundary and informed that state statutes and tribunal rules remain outside the verified corpus.
- [ ] **Issue Flagging Training:** Participant instructed on how to flag ungrounded assertions or invalid citations using the in-app feedback dialog (`POST /api/evaluation/monitoring/feedback`).
- [ ] **Privacy Disclosure Reviewed:** Participant briefed that raw legal queries are masked by default (`[REDACTED_BY_DEFAULT]`) and that user telemetry can be inspected or permanently deleted at any time (`DELETE /api/evaluation/monitoring/my-events`).
- [ ] **Credential Provisioning:** Administrator issues credentials via `/api/auth/admin/provision-user` or provides designated invitation code (`settings.PILOT_INVITATION_CODE`).

---

## 5. Technical Access Controls & Safeguards

### 5.1 Restricted Registration Enforcement
- Public self-registration is disabled in `backend/routes/auth.py`.
- Any registration attempt without a valid institutional invitation code returns `403 FORBIDDEN`.
- Admin account provisioning route (`POST /api/auth/admin/provision-user`) strictly requires `ADMIN` role.

### 5.2 Mandatory UI Safeguard Banners
- In `frontend/src/components/ResearchWorkspace.tsx`, a persistent warning banner is displayed above research outputs:
  > **Controlled Pilot Safeguards & Mandatory Human Legal Review**  
  > **Corpus Scope:** Grounded strictly against indexed Supreme Court of India constitutional and commercial landmark authorities. Specialized local statutory rules and tribunal matters are outside the verified scope.  
  > **Human Review Required:** LEXORA provides AI-assisted research synthesis and does not constitute qualified legal advice. Practitioners must independently review all supporting passages and citations before court filings.

### 5.3 Primary Source Excerpt Modal
- Whenever a citation is clicked in research findings, `frontend/src/components/DocumentSourceViewer.tsx` displays the exact indexed judgment excerpt, paragraph number, court, and reporter metadata, enabling instant primary source verification.

### 5.4 Privacy & Tenant Isolation
- Telemetry logs redact queries by default (`[REDACTED_BY_DEFAULT]`).
- GDPR Right-to-be-Forgotten endpoint (`DELETE /api/evaluation/monitoring/my-events`) purges user records immediately upon request.
- Cross-user and cross-tenant data access is strictly blocked.

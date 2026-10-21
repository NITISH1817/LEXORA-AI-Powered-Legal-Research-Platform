# LEXORA — Phase 18 Institutional Pilot Onboarding Package & Access Protocols

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Version:** 3.0.0 (Phase 18 Release)  
**Execution Timestamp:** `2026-10-21T14:00:00Z`  
**Operational Status:** **PENDING INSTITUTIONAL PARTNERSHIP AGREEMENT & CREDENTIAL ISSUANCE**  
**Target Supervised Cohort:** 3–5 Designated Legal Researchers (`pilot_res_01` to `pilot_res_05`)  

---

## 1. Executive Summary & Onboarding Objective

This comprehensive onboarding package governs the operational, legal, and technical requirements for onboarding designated legal researchers into the controlled pilot deployment of **LEXORA**.

> [!IMPORTANT]
> **Anti-Fabrication & Seat Distinction Rule:**
> 1. The profiles `pilot_res_01` through `pilot_res_05` represent **designated operational seats** and specialized practice archetypes. They are **not** simulated or fictional practitioners.
> 2. No participant credentials will be issued, and no account will be moved to `ACTIVE` status, until the institutional authorization checklist is fully satisfied and the individual advocate/fellow's identity is verified against active Bar or University rolls.
> 3. Autonomous legal practice, client advice, and unsupervised court filings remain strictly prohibited.

---

## 2. Institutional Authorization Checklist (Pre-Onboarding)

The Institutional Pilot Coordinator must execute and sign this checklist prior to issuing invitations:

- [ ] **1. Bilateral Memorandum of Understanding (MoU):** Signed agreement between LEXORA Project Leadership and the Participating Institution (Law Firm Chambers, Appellate Legal Aid Clinic, or National Law University).
- [ ] **2. Data Processing & Privacy Agreement (DPA):** Formal agreement defining data ownership, telemetry redaction standards, and auditability.
- [ ] **3. Lead Institutional Coordinator Designation:** One senior administrator or partner designated as the administrative contact with `ADMIN` role access.
- [ ] **4. Permitted Use Scope Confirmed:** Agreement explicitly restricting usage to AI-assisted research and academic verification, prohibiting autonomous court submission without independent advocate review.
- [ ] **5. Incident Escalation Channel Established:** Dedicated 72-hour communication channel between participating researchers and the LEXORA triage engineering team.

---

## 3. Designated Participant Cohort vs. Verified Identities

The controlled pilot provides capacity for five specialized researcher seats:

| Seat ID | Practice Domain Archetype | Institutional Setting | Doctrinal Focus Area | Onboarding Status |
| :--- | :--- | :--- | :--- | :---: |
| **`pilot_res_01`** | **Constitutional Law Research Fellow** | University Legal Clinic / Constitutional Law Centre | Article 21 procedural fairness evolution (*Gopalan* $\to$ *Maneka Gandhi* $\to$ *Puttaswamy*), 3-fold proportionality standard, and fundamental privacy rights. | **DESIGNATED SEAT (Pending Advocate Verification)** |
| **`pilot_res_02`** | **Commercial Arbitration Associate** | High Court Appellate Chambers | Arbitration Act 1996 Section 34(2A) patent illegality boundaries, 2015 amendments (*Ssangyong*), and 7-judge stamping doctrine (*In Re Interplay*). | **DESIGNATED SEAT (Pending Advocate Verification)** |
| **`pilot_res_03`** | **Insolvency & Bankruptcy Specialist** | Restructuring & Insolvency Practice Group | IBC Section 53 waterfall ranking of unsecured financial creditors relative to statutory tax claims (*Paschimanchal* vs *Rainbow Papers*). | **DESIGNATED SEAT (Pending Advocate Verification)** |
| **`pilot_res_04`** | **Appellate Litigation Law Clerk** | Supreme Court Registry / Senior Counsel Chambers | Law reporter transcript verification (SCR, SCC, AIR), chronological precedent timeline consistency, and ratio vs obiter separation. | **DESIGNATED SEAT (Pending Advocate Verification)** |
| **`pilot_res_05`** | **Senior Legal Research Annotator** | Law Review Editorial Board | Negative control boundary testing, unanswerable queries, and system abstention verification. | **DESIGNATED SEAT (Pending Advocate Verification)** |

---

## 4. Participant Identity & Qualification Verification

Before credentials are issued for any seat, the following verification records must be filed:
1. **Bar Enrollment Verification:** For advocate participants, copy of Bar Council of India / State Bar Council Certificate of Practice (e.g. `D/1234/2014`, `MH/982/2015`).
2. **Academic Verification:** For research fellows, formal appointment letter from a recognized law faculty or university legal aid clinic.
3. **Standing Check:** Minimum 2 years litigation, judicial clerkship, or academic legal research experience.
4. **Conflict Check:** Participant confirms they are not acting as counsel in active matters that compromise evaluation confidentiality.

---

## 5. Individual Account Provisioning Instructions

Accounts are provisioned by an authorized administrator using the secure provisioning endpoint:

### Provisioning via Admin API
```http
POST /api/auth/admin/provision-user HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <ADMIN_JWT_TOKEN>
Content-Type: application/json

{
  "email": "researcher.name@institution.edu",
  "full_name": "Advocate Full Name",
  "password": "<TEMPORARY_STRONG_PASSWORD>",
  "role": "RESEARCHER",
  "invitation_code": "LEXORA-PILOT-2026-SUPERVISED"
}
```

### Self-Registration via Supervised Invitation Code
If authorized by the pilot coordinator, the participant registers at `/register` using:
1. Valid institutional email address.
2. Strong password ($\ge 8$ characters, uppercase, lowercase, number, special character).
3. Active institutional invitation code: `LEXORA-PILOT-2026-SUPERVISED`.
*(Note: Registration attempts without this exact code are rejected by the backend with HTTP 403 Forbidden).*

---

## 6. Access Permissions & Role Matrix

| User Role | In-App Capabilities | Prohibited Capabilities |
| :--- | :--- | :--- |
| **`RESEARCHER`** | • Execute hybrid RAG legal research queries<br>• Query document intelligence and paged source reader<br>• Inspect precedent graphs and comparison matrices<br>• Bookmark cases and save researcher notes<br>• Submit structured feedback on citations and claims<br>• Purge own telemetry records (`DELETE /my-events`) | • Access administrative provisioning endpoints<br>• View other users' sessions or document uploads<br>• Access raw un-redacted cross-user telemetry<br>• Approve official benchmark gold labels |
| **`ADMIN`** | • Pre-provision authorized participant accounts<br>• View aggregated, privacy-safe monitoring metrics<br>• Monitor 72-hour feedback triage queue<br>• Trigger backup creation and restore verification | • Inspect individual user research queries without consent<br>• Bypass role-based reviewer authorization rules |

---

## 7. Mandatory Legal Disclaimer & Non-Reliance Acknowledgment

Every participant must sign the following acknowledgment before first login:

> **LEXORA RESEARCH NON-RELIANCE UNDERTAKING:**
> 
> "I understand and agree that LEXORA is an artificial intelligence-assisted legal research platform designed solely to support legal analysis and accelerate case-law discovery. 
> 
> I explicitly acknowledge that:
> 1. Platform outputs do **not** constitute legal advice, binding judicial interpretation, or formal legal opinions.
> 2. I bear sole professional and ethical responsibility for independently verifying all generated propositions, statutory interpretations, and case citations against official primary legal reporters (SCR, SCC, AIR) prior to consequential reliance or submission in pleadings.
> 3. I will not cite LEXORA outputs directly in court filings, pleadings, or client advisories without independent advocate verification.
> 4. I am aware that the current corpus scope is restricted to indexed Supreme Court of India constitutional and commercial landmark authorities, and that state-specific high court rules and tribunal decisions remain outside the verified corpus."

---

## 8. Corpus Scope, Statutory Boundaries & Known Limitations

- **Indexed Corpus Scope:** 52 Landmark authorities of the Supreme Court of India covering Constitutional Law (Articles 14, 19, 21), Corporate Insolvency (IBC Section 53), Arbitration & Conciliation Act 1996 (Sections 8, 11, 16, 34), and fundamental privacy jurisprudence.
- **Corpus Exclusions:**
  - High Court judgments, district court trial records, and subordinate judiciary orders.
  - Quasi-judicial tribunal orders (NCLAT, SAT, ITAT, APTEL) except where directly discussed in Supreme Court landmark judgments.
  - State municipal regulations, local tax statutes, and unindexed subordinate legislation.
- **Doctrinal Nuances:** In case comparisons, identified doctrinal tensions reflect differing statutory postures or bench sizes rather than definitive judicial conflicts.

---

## 9. Privacy, Telemetry & GDPR Data Rights

- **Query Redaction by Default:** In telemetry logs, all user research queries are masked with `[REDACTED_BY_DEFAULT]`.
- **Sensitive Key Sanitization:** Passwords, API tokens, Authorization headers, and personal email addresses are scrubbed using automated sanitization filters.
- **Tenant Isolation:** All user research sessions, uploaded filings, and notes are strictly isolated by `user_id`.
- **Right to be Forgotten:** Any participant can permanently delete all their telemetry events and feedback submissions at any time:
  ```http
  DELETE /api/evaluation/monitoring/my-events HTTP/1.1
  Authorization: Bearer <USER_JWT_TOKEN>
  ```
- **Automated Retention Limit:** All operational logs are automatically purged after 30 days (`PILOT_MONITORING_RETENTION_DAYS = 30`).

---

## 10. Reporting Unsupported Claims & Citation Errors

Participants are instructed to flag potential errors via the in-app feedback dialog:

```
[ Research Workspace Finding ]
           │
           ▼
[ Click "Flag Finding" / "Feedback" ]
           │
           ▼
[ Select Taxonomy Code: ]
  • IR_IRRELEVANT_PASSAGE: Retrieved excerpt does not relate to legal issue.
  • CLAIM_UNSUPPORTED_BY_PASSAGE: Model finding not supported by cited text.
  • CITATION_METADATA_INVALID: Year, reporter, or court incorrectly labeled.
  • CITATION_PASSAGE_UNSUPPORTIVE: Citation valid, but excerpt fails to prove ratio.
  • ABSTENTION_FALSE_REFUSAL: System refused to answer despite indexed evidence.
  • ABSTENTION_MISSED_HALLUCINATED_ANSWER: System answered unanswerable query.
  • COMPARISON_FALSE_CONFLICT: False judicial tension reported across precedents.
  • TIMELINE_DATE_MISATTRIBUTION: Event date confused with judgment date.
  • PROVIDER_TIMEOUT_OR_DEGRADED: System timeout or rate limit failure.
           │
           ▼
[ Submit to 72-Hour Triage Queue (POST /api/evaluation/monitoring/feedback) ]
```

---

## 11. Reviewer Escalation & Incident Response Protocol

1. **Severity 1 (Critical Doctrinal Hallucination):** Model reports an overruled case as controlling law (e.g. asserting *A.K. Gopalan* or *NN Global* remains good law).  
   *Response:* Immediate review within 24 hours; temporary query suppression in prompt grounding instructions; hotfix to retrieval weighting.
2. **Severity 2 (Citation Support Failure):** Valid case cited but cited paragraph does not substantiate the specific legal proposition.  
   *Response:* Triage within 48 hours; chunk boundary adjustment; reporter verification.
3. **Severity 3 (UI / Non-Doctrinal Glitch):** Formatting, search filtering, or pagination delay.  
   *Response:* Triage within 72 hours in standard sprint cycle.

---

## 12. Participant Offboarding & Credential Revocation

Upon completion of the pilot period or participant withdrawal:
1. **Account Deactivation:** Administrator disables the account (`is_active = False`) via database or admin portal.
2. **Telemetry Purge:** User records are purged from `storage/monitoring/` upon request.
3. **Session Data Removal:** Research sessions, notes, and uploaded test documents are permanently removed.
4. **Certificate of Participation:** Issued to fellows/advocates acknowledging formal participation in the controlled pilot evaluation.

---

*Onboarding protocol established. Account provisioning remains held pending institutional signature.*

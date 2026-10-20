# LEXORA — Phase 16 Supervised Pilot Readiness & Practitioner Onboarding Protocol

**Document Version:** 1.0.0  
**Status:** PILOT READY (PENDING INSTITUTIONAL AUTHORIZATION)  
**Target Deployment:** Limited Controlled Pilot with 3–5 Designated Legal Researchers  
**Audit Timestamp:** `2026-10-20T14:20:00Z`  

---

## 1. Executive Summary & Controlled Pilot Scope

This document establishes the operational onboarding protocol, technical safeguards, and evidence collection framework for a small, supervised pilot of the **LEXORA AI-Powered Legal Intelligence & Research Platform**.

In strict compliance with evaluation integrity principles:
1. **Designated Participants Only:** Deployment is strictly limited to 3–5 pre-credentialed legal researchers. Self-service public registration is disabled.
2. **Corpus Limitations Visible:** All users are briefed and presented with prominent UI disclaimers detailing that LEXORA is currently grounded against landmark Supreme Court of India constitutional and commercial judgments. Specialized local state statutes and tribunal rules remain outside the verified corpus.
3. **Mandatory Human Verification:** Platform outputs represent AI-assisted research synthesis and do **not** constitute legal advice. Practitioners must independently verify primary source transcripts before court reliance.
4. **Authentic Evidence Collection:** No synthetic or simulated user accounts, feedback records, or usage metrics will be accepted as pilot evidence.

---

## 2. Designated Legal Researcher Cohort (3–5 Participants)

The supervised pilot is designed for a focused cohort of 3–5 legal researchers representing distinct practice domains. The following role profiles represent the designated pilot cohort:

| Participant ID | Professional Role Archetype | Primary Doctrinal Focus | Evaluation Objective |
| :--- | :--- | :--- | :--- |
| **`pilot_res_01`** | **Constitutional Law Research Fellow** | Article 21, Right to Privacy (*Puttaswamy*), Proportionality Standard | Validate plurality ratio extraction, obiter vs ratio separation, and multi-bench precedent synthesis. |
| **`pilot_res_02`** | **Commercial Arbitration Associate** | Arbitration Act Section 34, Patent Illegality, Stamping Curability (*NN Global* / *In Re Interplay*) | Evaluate statutory amendment recognition (2015 amendments) and recent Constitution Bench overruling fidelity. |
| **`pilot_res_03`** | **Insolvency & Bankruptcy Specialist** | IBC Section 53 Waterfall, Resolution Plan Priorities (*Essar Steel*, *Paschimanchal Vidyut*) | Audit statutory conflict resolution and priority ranking of statutory tax claims vs financial debts. |
| **`pilot_res_04`** | **Appellate Litigation Law Clerk** | Precedent Timeline Monotonicity, Citation Validity, Judicial Bench Composition | Verify citation reporter accuracy (SCR/SCC/AIR) and chronological event sequencing. |
| **`pilot_res_05`** | **Senior Legal Research Annotator** | Negative Control Abstention Queries, False Legal Premises | Test system abstention boundaries and resistance to hallucinated holdings. |

> [!NOTE]
> **Institutional Authorization Status:** The above profiles represent designated cohort seats. Pilot activation is subject to formal credential issuance and institutional partnership agreement with a participating law firm, academic institution, or judicial clerkship office.

---

## 3. Onboarding & Access Control Checklist

Every participant must complete the following onboarding sequence prior to accessing the platform:

```
[ STEP 1: Institutional Authorization ]
             │
             ▼
[ STEP 2: Pre-Pilot Safeguard Briefing & Non-Reliance Acknowledgment ]
             │
             ▼
[ STEP 3: Credential Issuance (Designated JWT with PILOT_USER Role) ]
             │
             ▼
[ STEP 4: First-Session Verification of Safeguard Banners & Flagging Tools ]
             │
             ▼
[ STEP 5: Supervised Query Execution & Telemetry Intake ]
```

### Pre-Flight Participant Checklist:
- [ ] **Credential Issuance:** Unique credential issued and mapped to designated participant ID.
- [ ] **Role Assignment:** User role restricted to `PILOT_USER` (administrative endpoints inaccessible).
- [ ] **Non-Reliance Agreement Signed:** User explicitly acknowledges that system outputs cannot be cited in judicial filings without independent primary reporter verification.
- [ ] **Corpus Scope Understood:** User briefed on the Supreme Court landmark corpus boundary and abstention behavior for unindexed local laws.
- [ ] **Flagging Mechanism Briefing:** User trained on how to flag ungrounded assertions or invalid citations.

---

## 4. Technical Safeguards & Disclaimer Visibility

The platform enforces active safeguards verified through automated testing:

### 4.1 Persistent UI Disclaimer Banner
In [`frontend/src/components/ResearchWorkspace.tsx`](file:///d:/AI-Legal-Research-System/frontend/src/components/ResearchWorkspace.tsx#L258-L271), a high-visibility safeguard banner is persistently displayed above research results:
> **Controlled Pilot Safeguards & Mandatory Human Legal Review**  
> **Corpus Scope:** Grounded strictly against indexed Supreme Court of India constitutional and commercial landmark authorities. Specialized local statutory rules and unindexed tribunal matters are outside the verified scope.  
> **Human Review Required:** LEXORA provides AI-assisted research synthesis and does not constitute qualified legal advice. Practitioners must independently review all supporting passages and citations before court filings or consequential decisions.

### 4.2 In-App Citation Verification Modal
Whenever a cited authority is clicked, the platform opens the primary excerpt in [`DocumentSourceViewer.tsx`](file:///d:/AI-Legal-Research-System/frontend/src/components/DocumentSourceViewer.tsx), allowing the practitioner to verify the quoted text against the indexed law report before saving evidence to their research session.

---

## 5. User Feedback Flagging & Tenant Isolation

Pilot researchers can flag any system response that exhibits doctrinal inaccuracy, missing authority, or ungrounded claims.

### 5.1 Feedback Capture Endpoint
Feedback is submitted via `POST /api/evaluation/monitoring/feedback` (or in-session flagging):
```json
{
  "request_id": "req_88f91c2b-...",
  "rating": 2,
  "review_status": "FLAGGED",
  "review_notes": "Citation (2015) 3 SCC 49 does not account for Section 34(2A) 2015 amendment narrowing patent illegality.",
  "flag_reason": "CLAIM_UNSUPPORTED_BY_PASSAGE"
}
```

### 5.2 Tenant & User Isolation
- **Event Scoping:** Telemetry events and feedback records are tagged with `user_id`.
- **Private Inspection:** Users can inspect only their own logged interactions (`GET /api/evaluation/monitoring/my-events`). Cross-user leakage is strictly prevented.
- **GDPR Right-to-be-Forgotten:** Users can permanently delete all their telemetry events and feedback records at any time (`DELETE /api/evaluation/monitoring/my-events`). Automated tests confirm complete record purging.

### 5.3 Privacy Protection & Query Redaction
- In compliance with privacy standards, raw legal queries are masked with `[REDACTED_BY_DEFAULT]` in telemetry logs.
- Sensitive credentials, API keys, and email addresses are automatically scrubbed via `sanitize_text()`.
- Document text contents are never stored in telemetry logs.

---

## 6. The 72-Hour Triage SLA Protocol

All practitioner feedback submissions and flagged issues are governed by a mandatory **72-Hour Operational Triage SLA**.

### 6.1 Standardized Issue Taxonomy
When an issue is flagged, it is triaged into one of the following nine standardized categories:

| Issue Code | Doctrinal Failure Mode | Operational Remediation Protocol |
| :--- | :--- | :--- |
| **`IR_IRRELEVANT_PASSAGE`** | Retrieved passage did not address the queried legal issue or statute. | Re-tune BM25 + dense retrieval weights and enhance semantic legal expansion. |
| **`CLAIM_UNSUPPORTED_BY_PASSAGE`** | Generated legal claim lacks evidentiary foundation in cited passage. | Review RAG prompt constraints; penalize ungrounded factual assertions. |
| **`CITATION_METADATA_INVALID`** | Citation text or court/year/page metadata does not resolve to an authoritative report. | Validate metadata against official SCR/SCC gazette records; correct corpus metadata. |
| **`CITATION_PASSAGE_UNSUPPORTIVE`**| Citation resolves to valid case, but the specific excerpt does not prove the claim. | Re-align passage-to-claim association to prevent multi-source cross-product dilution. |
| **`ABSTENTION_FALSE_REFUSAL`** | System refused to answer despite indexed authoritative evidence. | Adjust confidence threshold for high-density legal queries. |
| **`ABSTENTION_MISSED_HALLUCINATION`**| System answered an unanswerable or false-premise question. | Strengthen adversarial boundary detection and enforce strict negative control refusal. |
| **`COMPARISON_FALSE_CONFLICT`** | System reported judicial conflict where precedents are harmonious or distinguishable. | Enhance bench composition and overruling timeline reasoning in comparative engine. |
| **`TIMELINE_DATE_MISATTRIBUTION`** | Event date misattributed or confused with judgment pronouncement date. | Verify chronological extraction pipeline against judgment header dates. |
| **`PROVIDER_TIMEOUT_OR_DEGRADED`** | LLM API provider failure, rate limit, or network disconnection. | Monitor fallback provider failover and latency budgets. |

### 6.2 Triage Timeline:
- **T + 24 Hours:** Initial acknowledgment by Legal Engineering triage officer. Issue code assigned.
- **T + 48 Hours:** Preliminary review by Lead Legal Annotator against indexed primary passages.
- **T + 72 Hours:** Formal resolution disposition recorded:
  * `RESOLVED_CORRECTED`: Annotation or retrieval index corrected.
  * `RESOLVED_BY_DESIGN`: System behavior verified as correct; practitioner guidance provided.
  * `ESCALATED_TO_ADJUDICATION`: Doctrinal ambiguity escalated to Senior Legal Adjudicator.

---

## 7. Current Empirical Pilot Store State

Audit of the pilot monitoring directory (`./storage/monitoring`) via `scripts/analyze_pilot_feedback.py` yields the following verified state:

```json
{
  "status": "EMPTY_STATE_VERIFIED",
  "is_empty_state": true,
  "total_telemetry_events": 0,
  "total_feedback_submissions": 0,
  "average_rating": null,
  "triage_sla_tracking": {
    "target_sla_hours": 72,
    "pending_items_count": 0,
    "sla_breaches_count": 0,
    "triaged_count": 0,
    "sla_compliance_rate": 1.0,
    "status": "COMPLIANT"
  }
}
```

### Verification Finding:
- **No external practitioner feedback currently exists in the repository.**
- In strict adherence to evaluation integrity principles, **no fictional usage metrics, synthetic user ratings, or simulated reviews have been generated.**
- The platform is technically prepared to intake, isolate, and triage genuine pilot feedback once credentialed institutional researchers commence supervised usage.

# LEXORA — Phase 19 Practicing Advocate Reviewer Operational Instructions

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Version:** 1.0.0 (Phase 19 Operational Standard)  
**Target Audience:** Licensed Practicing Advocates, Senior Counsel, National Law University Clinical Faculty  
**Governing Baseline:** Benchmark v3.0.0 (52 Passages, 160 Queries: 70 Dev, 90 Held-Out)  
**Governing Script:** [`scripts/submit_human_review.py`](file:///d:/AI-Legal-Research-System/scripts/submit_human_review.py)  
**Workflow Engine:** [`evaluation/review_workflow.py`](file:///d:/AI-Legal-Research-System/evaluation/review_workflow.py)  
**Execution Status:** Awaiting Advocate Onboarding and Institutional Agreement  

---

## 1. Doctrinal Governance & Ethical Invariants

Reviewers must adhere to the following principles of legal evaluation integrity:

> [!IMPORTANT]
> **Core Ethical & Technical Invariants:**
> 1. **No Automated Approvals:** Automated scripts, CI runners, and synthetic LLM judges are strictly forbidden by software enforcement (`AutomatedApprovalForbiddenError`) from approving gold labels. Every approved label must be approved by an authenticated, verified legal practitioner.
> 2. **Anti-Self-Adjudication:** A reviewer who escalates an item to `NEEDS_ADJUDICATION` cannot serve as the adjudicator resolving the dispute (`SelfAdjudicationForbiddenError`). Senior adjudication requires an independent senior reviewer.
> 3. **Source Verification vs Gold Label Approval:** Verifying that a judgment transcript exists (`SOURCE_VERIFIED`) does **not** promote an item to `APPROVED`. A substantive legal evaluation of ratio accuracy, citation sufficiency, and procedural fidelity is mandatory.
> 4. **Mandatory Substantive Rationale:** One-word or placeholder approvals (e.g., "OK", "Approved", "Looks good") are rejected by the workflow engine. Reviewers must provide minimum 2–3 sentences of authoritative doctrinal reasoning citing official law reporters (SCR, SCC, AIR).
> 5. **Primary Law Source Primacy:** All claims must be verified against verbatim primary judgment text. Unverified secondary digests, headnotes, or AI-generated summaries are not acceptable as sole ground truth.

---

## 2. Review Lifecycle & State Transition Model

The review lifecycle enforces an auditable, sequential 5-stage state machine:

```
[ PENDING_HUMAN_LEGAL_REVIEW ]
             │
             ▼  Step 1: --claim
       [ IN_REVIEW ]
             │
             ├─────────────────────────────────────────────────┐
             ▼  Step 2: --verify-source                        │
    [ SOURCE_VERIFIED ]                                        │
             │                                                 │
             ▼  Step 3: --review-annotation                    │
   [ ANNOTATION_REVIEWED ]                                     │
             │                                                 │
             ├──────────────────────┬──────────────────────────┤
             ▼  Step 4a: --approve  ▼  Step 4b: --reject       ▼  Step 4c: --request-adjudication
       [ APPROVED ]           [ REJECTED ]              [ NEEDS_ADJUDICATION ]
    (Gold Label Approved)  (Doctrinally Flawed)       (Conflicting Interpretations)
                                                               │
                                                               ▼  Step 5: --adjudicate
                                                  [ DISAGREEMENT_ADJUDICATED ]
                                                               │
                                                               ▼
                                                          [ APPROVED ]
```

---

## 3. Step-by-Step CLI Execution Guide

All review operations are executed using Python virtual environment CLI:
```powershell
# From workspace root: d:\AI-Legal-Research-System
venv\Scripts\python.exe scripts/submit_human_review.py [OPTIONS]
```

### 3.1 Audit Current Review Queue Status
To view current queue progress and verification status across all 160 benchmark items:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py --audit-status
```
*Current Baseline:* 160 items total, 160 pending (100.0%), 0 in-review, 0 source-verified, 0 annotation-reviewed, 0 approved, 0 rejected, 0 needs-adjudication.

---

### 3.2 Inspecting a Specific Benchmark Query
Before claiming, inspect the exact query, split, category, proposed expected answer, candidate passages, and risk score:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py --inspect bench_093
```
*Output will display:* Query ID, category, benchmark split, legal proposition, candidate passages, citation metadata, and current lifecycle state.

---

### 3.3 Step 1: Claiming an Item for Review
A qualified practitioner claims an item by providing their registered reviewer ID, full legal name, and Bar Council / Faculty enrollment number:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --claim bench_093 `
  --reviewer-id adv_delhi_d1042 `
  --reviewer-name "Adv. R. Sharma" `
  --bar-number "D/1042/2012"
```
- Transition: `PENDING_HUMAN_LEGAL_REVIEW` $\to$ `IN_REVIEW`.
- Audit log records reviewer registration and claiming timestamp.

---

### 3.4 Step 2: Primary Source Verification
The reviewer locates and reviews the official primary law report (SCR, SCC, or AIR) for each cited authority:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --verify-source bench_093 `
  --reviewer-id adv_delhi_d1042 `
  --source-ref "(1978) 1 SCC 248 Paras 56-58; (2017) 10 SCC 1 Paras 294-298" `
  --rationale "Verified primary judgment text in official Supreme Court Reports and SCC. Quoted extracts match verbatim text of Bhagwati, J. in Maneka Gandhi and Chandrachud, J. in Puttaswamy."
```
- Transition: `IN_REVIEW` $\to$ `SOURCE_VERIFIED`.
- Confirms the judgment exists, citations are accurate, and paragraph numbers are verified.

---

### 3.5 Step 3: Multi-Dimensional Rubric Scoring
The reviewer scores the benchmark annotation against three formal criteria (scale 1.0 to 5.0, where $\ge 4.0$ is passing):
1. **Ratio Decidendi Accuracy (1–5):** Does the proposition reflect binding holding rather than concurring or dissenting obiter?
2. **Citation Sufficiency (1–5):** Are authoritative primary citations (with paragraph/page numbers) provided for every substantive claim?
3. **Procedural Fidelity (1–5):** Does the annotation reflect the correct procedural posture (writ petition, civil appeal, reference) and the applicable statutory version at the time of decision?

```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --review-annotation bench_093 `
  --reviewer-id adv_delhi_d1042 `
  --ratio-accuracy 5.0 `
  --citation-sufficiency 4.5 `
  --procedural-fidelity 5.0 `
  --rationale "Doctrinal progression accurately captures the shift from Gopalan literal procedure to Maneka Gandhi substantive fairness and Puttaswamy privacy. All three cumulative proportionality limbs correctly stated."
```
- Transition: `SOURCE_VERIFIED` $\to$ `ANNOTATION_REVIEWED`.

---

### 3.6 Step 4a: Final Approval (Promoting to Gold Label)
If rubric scores satisfy standards ($\ge 4.0$ across dimensions) and the proposition is doctrinally sound:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --approve bench_093 `
  --reviewer-id adv_delhi_d1042 `
  --rationale "Approved as benchmark gold label. The proposition accurately distinguishes majority holding from individual concurrences in Puttaswamy and correctly states the overruling of Gopalan."
```
- Transition: `ANNOTATION_REVIEWED` $\to$ `APPROVED`.
- Only approved items enter the authoritative benchmark evaluation pool.

---

### 3.7 Step 4b: Substantive Rejection
If the candidate annotation contains legal errors, hallucinated statutory provisions, or misleading case holdings:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --reject bench_121 `
  --reviewer-id adv_delhi_d1042 `
  --rationale "Rejected. The annotation mistakenly ranks government tax dues under Section 53(1)(b) pari passu with secured creditors, misapplying Rainbow Papers without considering Paschimanchal Vidyut (2023)."
```
- Transition: `ANNOTATION_REVIEWED` $\to$ `REJECTED`.
- Item is flagged for dataset author revision and excluded from evaluation.

---

### 3.8 Step 4c: Escalation & Requesting Senior Adjudication
If the item involves a deep doctrinal conflict (e.g., competing Constitution Bench interpretations or unresolved circuit conflicts):
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --request-adjudication bench_072 `
  --reviewer-id adv_delhi_d1042 `
  --rationale "Escalated for Senior Counsel adjudication. Tension between Section 16 competence-competence scope and curative stamping timeline under In Re Interplay requires specialist determination."
```
- Transition: Current State $\to$ `NEEDS_ADJUDICATION`.

---

### 3.9 Step 5: Senior Counsel Adjudication
A designated Senior Advocate or Retired Judge adjudicates the escalated item:
```powershell
venv\Scripts\python.exe scripts/submit_human_review.py `
  --adjudicate bench_072 `
  --adjudicator-id sr_adv_delhi_001 `
  --adjudicator-name "Sr. Adv. K. Parasaran" `
  --rationale "Binding 7-judge Constitution Bench in In Re Interplay (2024) 6 SCC 1 settled the law: unstamped agreement is curable, not void ab initio. Referral court must defer stamping objections to arbitrator. Annotation approved with this binding caveat."
```
- Transition: `NEEDS_ADJUDICATION` $\to$ `DISAGREEMENT_ADJUDICATED` $\to$ `APPROVED`.
- *Note:* The adjudicator cannot be `adv_delhi_d1042` (anti-self-adjudication invariant).

---

## 4. Legal Substantive Review Guidelines

### 4.1 Ratio Decidendi vs Obiter Dictum
- **Ratio Decidendi:** The legal principle necessary to decide the actual dispute between the parties based on material facts.
- **Obiter Dictum:** Incidental observations or illustrations by the court not essential to the disposition.
- *Review Standard:* When evaluating *Puttaswamy* (2017), the unanimous 9-judge order signed by all nine judges constitutes binding ratio. Observations found solely in concurring opinions (e.g. Chelameswar, J., Bobde, J., Kaul, J.) must be treated as persuasive concurrence, not the sole ratio.

### 4.2 Overruling & Negative Judicial Treatment
- **Express Overruling:** An authority is expressly overturned by a larger bench (e.g., *M.P. Sharma* expressly overruled by 9 judges in *Puttaswamy*; *NN Global (2023)* expressly overruled by 7 judges in *In Re Interplay (2024)*).
- **Partial Overruling / Distinguishing:** An authority remains good law on one point while overruled on another (e.g., *Kharak Singh* was overruled regarding its rejection of privacy under Article 21, but its holding invalidating nocturnal domiciliary visits under Regulation 236(b) was explicitly approved).
- *Review Standard:* An answer that states "*Kharak Singh* was overruled in its entirety" is inaccurate and must be rejected or scored low on ratio accuracy.

### 4.3 Statutory Versioning & Chronological Posture
- Reviewers must check whether the legal proposition applies to the pre-amendment or post-amendment statute.
- *Arbitration Example:* Section 34(2A) patent illegality was introduced by the Arbitration and Conciliation (Amendment) Act, 2015 (effective 23-10-2015). It applies only to domestic arbitral awards seated in India, never to international commercial arbitrations (*Ssangyong Engineering* (2019)).

---

## 5. Audit Trail Inspection & Verification

Reviewers and auditors can verify that all actions are recorded immutably in `evaluation/review_audit_log.json`:
```powershell
venv\Scripts\python.exe -c "import json; log = json.load(open('evaluation/review_audit_log.json')); print(f'Total audit records: {len(log)}')"
```
Every entry preserves:
- `entry_id` (UUIDv4)
- `timestamp` (UTC ISO 8601)
- `item_id` (e.g. `bench_093`)
- `reviewer_id` and `reviewer_role`
- `action` (`CLAIM`, `VERIFY_SOURCE`, `REVIEW_ANNOTATION`, `APPROVE`, `REJECT`, `ESCALATE`, `ADJUDICATE`)
- `rationale` (verbatim text)
- `previous_state` and `new_state`

---

## 6. Prohibitions & Anti-Tampering Reminders

- **No Synthetic Reviewers:** Never use bot usernames or dummy test handles (e.g. `bot_reviewer`, `test_user`, `admin`) to approve gold labels.
- **No Batch Unexamined Approvals:** CLI script restricts batch auto-approval commands. Each item must be reviewed individually.
- **Integrity Enforcement:** The evaluation system cross-checks all approved items against active Bar enrollment verification records before computing published benchmark accuracy.

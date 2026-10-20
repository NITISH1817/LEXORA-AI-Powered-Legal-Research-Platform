# LEXORA — Phase 16 Benchmark Review Status & Adjudication Audit

**Dataset:** Benchmark v3.0.0 (52 Passages, 160 Queries: 70 Dev, 90 Held-Out)  
**Document Status:** ACTIVE REVIEW QUEUE AUDIT  
**Audit Timestamp:** `2026-10-20T14:20:00Z`  
**Overall Human Review State:** **160 / 160 PENDING HUMAN LEGAL REVIEW (100.0%)**  

---

## 1. Executive Summary & Verification of Catalog State

An audit of the LEXORA Benchmark v3 catalog was performed using `evaluation/review_workflow.py` and `scripts/submit_human_review.py`. 

The audit confirms:
- **Zero Approved Gold Labels:** No benchmark query has received formal approval from a licensed practicing advocate.
- **Zero Automated Infiltration:** The workflow strictly prevents automated approval (`AutomatedApprovalForbiddenError`), ensuring that 100% of benchmark items remain in pending review status awaiting qualified counsel.
- **Strict Split Preservation:** The 70 development queries and 90 held-out queries are maintained with strict boundary separation and zero cross-split leakage.

```
================================================================================
BENCHMARK V3 REVIEW LIFECYCLE AUDIT (N=160)
================================================================================
  [PENDING_HUMAN_LEGAL_REVIEW] : 160 queries (100.0%)  <-- Active catalog state
  [IN_REVIEW]                  :   0 queries (  0.0%)
  [SOURCE_VERIFIED]            :   0 queries (  0.0%)
  [ANNOTATION_REVIEWED]        :   0 queries (  0.0%)
  [APPROVED / GOLD_APPROVED]   :   0 queries (  0.0%)  <-- 0 Authoritative Gold Labels
  [REJECTED]                   :   0 queries (  0.0%)
  [NEEDS_ADJUDICATION]         :   0 queries (  0.0%)
  [DISAGREEMENT_ADJUDICATED]   :   0 queries (  0.0%)
================================================================================
```

---

## 2. Risk Tier & Doctrinal Distribution

The 160 benchmark queries are stratified across four risk tiers based on doctrinal complexity, bench composition, overruling exposure, and potential liability of misattribution:

| Priority Tier | Risk Score Range | Criteria & Doctrinal Exposure | Item Count | Percentage |
| :--- | :---: | :--- | :---: | :---: |
| **`PRIORITY_1_CRITICAL`** | **6.5 – 10.0** | Overruled Constitution Bench precedents, ratio vs obiter disputes, statutory waterfall conflicts, fundamental rights boundaries. | **8** | **5.0%** |
| **`PRIORITY_2_HIGH`** | **4.5 – 6.4** | Multi-passage synthesis across 3+ precedents, negative control abstention queries, complex statutory interpretation. | **24** | **15.0%** |
| **`PRIORITY_3_MEDIUM`** | **3.0 – 4.4** | Precedent graph directionality, chronological timeline monotonicity, case comparison distinctions. | **48** | **30.0%** |
| **`PRIORITY_4_STANDARD`** | **1.0 – 2.9** | Direct factual recall, straightforward statutory provision lookups, landmark case holding verification. | **80** | **50.0%** |
| **Total Catalog** | **—** | **Complete Benchmark v3 Dataset** | **160** | **100.0%** |

---

## 3. Legal Domain & Category Breakdown

| Legal Domain | Total Queries | Dev Split (N=70) | Held-Out Split (N=90) | Primary Controlling Authorities |
| :--- | :---: | :---: | :---: | :--- |
| **Constitutional Law & Rights** | **44** | 20 | 24 | *A.K. Gopalan*, *Maneka Gandhi*, *Puttaswamy*, *Kharak Singh*, *M.P. Sharma* |
| **Commercial Law & Arbitration** | **36** | 16 | 20 | *Associate Builders*, *Ssangyong Engineering*, *NN Global*, *In Re Interplay* |
| **Insolvency & Bankruptcy (IBC)** | **28** | 12 | 16 | IBC Section 53, *Essar Steel*, *Paschimanchal Vidyut*, *Rainbow Papers* |
| **Criminal Law & Procedure** | **24** | 10 | 14 | CrPC Search Provisions, Article 20(3) Self-Incrimination, Evidentiary Warrants |
| **General Jurisprudence & Control** | **28** | 12 | 16 | Negative Control Abstentions, Factual Timelines, Unanswerable Inquiries |

---

## 4. Separation of Review Lifecycle States

In accordance with Phase 16 Task 4, the review workflow strictly enforces the distinction between non-interchangeable review stages:

```
[ PENDING_HUMAN_LEGAL_REVIEW ] (160 Items)
             │
             ▼  claim_for_review (Advocate claims queue item)
       [ IN_REVIEW ]
        │         │
        │         ├──────────────────────────┐
        ▼ verify_source                      ▼ request_adjudication
 [ SOURCE_VERIFIED ]                 [ NEEDS_ADJUDICATION ]
        │                                    │
        ▼ review_annotation                  ▼ adjudicate_disagreement
[ ANNOTATION_REVIEWED ]             [ DISAGREEMENT_ADJUDICATED ]
        │                                    │
        ▼ approve_gold_label                 ▼ approve_gold_label
 [ APPROVED / GOLD_LABEL_APPROVED ] <────────┘
        │
        ▼ reject_annotation
    [ REJECTED ]
```

### Stage Definitions & Non-Interchangeability Rules:
1. **`SOURCE_VERIFIED` $\neq$ `APPROVED`:**
   Verifying that a judgment transcript exists in an official law reporter (SCR/SCC/AIR) merely establishes source authenticity. It does **NOT** approve the proposed question, holding synthesis, or legal proposition.
2. **`ANNOTATION_REVIEWED` $\neq$ `APPROVED`:**
   Auditing the rubric dimensions (ratio accuracy, citation support, procedural fidelity) establishes annotation quality, but does **NOT** elevate the item to the authoritative evaluation set until formal signed advocate approval is recorded.
3. **`NEEDS_ADJUDICATION` & `DISAGREEMENT_ADJUDICATED`:**
   When primary reviewers disagree on a nuanced doctrinal point (e.g. prospective vs retrospective overruling in *NN Global*), the query is escalated to a Senior Legal Adjudicator. Prior reviewer notes are preserved in the append-only audit log and never overwritten.

---

## 5. Advocate Review Instructions & Submission CLI

To support genuine review by practicing advocates without simulating activity, a dedicated CLI review tool is operational at `scripts/submit_human_review.py`.

### Step-by-Step Advocate Review Workflow:

#### Step 1: List and Filter the Prioritized Queue
```bash
# View Priority 1 Critical items
python scripts/submit_human_review.py --list-queue --tier CRITICAL

# View all pending items
python scripts/submit_human_review.py --list-queue --status-filter PENDING
```

#### Step 2: Inspect a Detailed Review Packet
```bash
python scripts/submit_human_review.py --inspect bench_093
```
*Outputs: Exact legal question, split, procedural posture, indexed passages with paragraph citations, controlling ratio, contrary authorities, and advocate verification checklist.*

#### Step 3: Claim Item for Review
```bash
python scripts/submit_human_review.py --claim bench_093 --reviewer "adv_priya_sharma_delhi_d1234" --rationale "Claiming for constitutional bench review"
```

#### Step 4: Record Primary Source Verification
```bash
python scripts/submit_human_review.py --verify-source bench_093 \
  --reviewer "adv_priya_sharma_delhi_d1234" \
  --source-auth "AIR 2017 SC 4161 / (2017) 10 SCC 1" \
  --source-loc "Paragraphs 24-28 (Judgment of Dr. D.Y. Chandrachud, J.)" \
  --rationale "SCR official reporter inspected. Bench composition 9-0 and judgment date confirmed."
```

#### Step 5: Record Annotation Review Rubric
```bash
python scripts/submit_human_review.py --review-annotation bench_093 \
  --reviewer "adv_priya_sharma_delhi_d1234" \
  --ratio-ok --citation-ok --procedural-ok \
  --rationale "Holding accurately traces Gopalan to Maneka to Puttaswamy. Article 14-19-21 golden triangle correctly cited."
```

#### Step 6: Grant Final Gold Label Approval
```bash
python scripts/submit_human_review.py --approve bench_093 \
  --reviewer "adv_priya_sharma_delhi_d1234" \
  --rationale "Approved as authoritative gold label. Ratio isolated from concurring obiter."
```

#### Batch Review via Signed JSON Packet:
External advocates can also submit reviews using a structured JSON packet:
```bash
python scripts/submit_human_review.py --import-packet /path/to/signed_review_packet.json
```

**JSON Review Packet Schema:**
```json
{
  "query_id": "bench_093",
  "reviewer_id": "adv_priya_sharma_delhi_d1234",
  "decision": "APPROVED",
  "rationale": "SCR official volume inspected; 9-judge ratio on Article 21 substantiated.",
  "source_authority": "AIR 2017 SC 4161 / (2017) 10 SCC 1",
  "source_location": "Paragraphs 24-28 (Judgment of Dr. D.Y. Chandrachud, J.)",
  "source_verified": true,
  "rubric_scores": {
    "ratio_accuracy": true,
    "citation_support": true,
    "procedural_fidelity": true
  }
}
```

---

## 6. Identification of External Dependencies

Progress beyond the current pending state is strictly dependent on the following external, non-engineering milestones:

1. **Practicing Advocate Review Panel:** Formal engagement of 2–3 licensed advocates (minimum 7 years standing at High Court or Supreme Court Bar) to execute review packets for the 8 critical items and 24 high-priority items.
2. **Institutional Review & Ethical Authorization:** Authorization by a participating law firm or university legal clinic for supervised pilot testing.
3. **Bar Enrollment Verification:** Verification of reviewer identifiers against state Bar Council rolls to ensure authentic human authorization.

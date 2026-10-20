# LEXORA — Legal Benchmark Annotation & Review Protocol (v3.0.0)

> **Document Type:** Legal Expert Annotation & Benchmark Curation Protocol  
> **Audience:** Admitted Advocates, Legal Researchers, Judicial Clerks, Benchmark Curators  
> **Target Dataset:** `evaluation/datasets/legal_benchmark_v3.json`  
> **Governance:** Double-Blind Dual Review with Senior Adjudication (Target Cohen's Kappa $\ge 0.85$)

---

## 1. Principles of Legal Benchmark Annotation

LEXORA benchmarks are designed to measure whether an AI legal assistant can retrieve authentic legal authorities, synthesize binding ratio decidendi, formulate valid citations, abstain on unsupported queries, and reason about temporal progressions.

### Core Quality Requirements
1. **Never Fabricate Legal Authorities:** Passages must be extracted verbatim or faithfully summarized from official Supreme Court of India reports (SCR, SCC, AIR) or official legislative gazettes.
2. **Explicit Grounding:** Every required factual point in `required_factual_points` must be directly substantiated by the text of the assigned `relevant_chunk_ids`.
3. **Strict Separation of Ratio vs Obiter vs Submissions:**
   - Court Holding: Binding principle of law decided by the bench.
   - Counsel Submissions: Arguments presented by appellant or respondent. These must **never** be annotated as court holdings.
   - Background Facts: Material historical narrative.
4. **Citation Validity & Support Disentanglement:**
   - A citation is **valid** if it resolves to a real case with the correct court, year, and page.
   - A citation is **supported** only if the underlying passage actually proves the associated claim.
5. **Abstention Integrity:**
   - Negative-control questions must feature plausible legal framing (e.g. realistic case titles, plausible statutory sections) to detect hallucination and ensure the system explicitly abstains when evidence is absent.

---

## 2. Benchmark Item JSON Schema Specification

Every item added to `legal_benchmark_v3.json` must validate against the following schema:

```json
{
  "id": "bench_XXX",
  "split": "dev | held_out",
  "category": "HOLDING | STATUTORY_INTERPRETATION | HOLDING_VS_SUBMISSION | MULTI_PASSAGE_SYNTHESIS | PRECEDENT_RELATIONSHIP | CONFLICT_AND_DISTINCTION | TEMPORAL_PRECISION | NEGATIVE_CONTROL_ABSTENTION | OCR_NOISE_AND_INCOMPLETE | FACTS_PROCEDURAL | ADVERSARIAL",
  "subject_area": "Constitutional Law & Equality | Commercial Arbitration & Contract Law | Corporate Insolvency & Bankruptcy (IBC 2016) | Taxation, GST & Administrative Law | Environmental Law & Criminal Procedure",
  "court_level": "Supreme Court of India | High Court of Delhi | Bombay High Court | NCLAT",
  "task_type": "qa | abstention",
  "question": "Clear, realistic legal research question posed by an attorney.",
  "expected_answer": "Complete, concise gold standard legal answer.",
  "required_factual_points": [
    "Atomic legal point 1 that must be present in a satisfactory answer.",
    "Atomic legal point 2 that must be present in a satisfactory answer."
  ],
  "relevant_chunk_ids": {
    "chunk_id_primary": 3,
    "chunk_id_secondary": 2
  },
  "required_citations": [
    "Full Landmark Citation (e.g., 'Kailash Nath Associates v. DDA (2015) 4 SCC 136')"
  ],
  "forbidden_claims": [
    "Unsupported claim or hallucinated holding that contradicts the law."
  ],
  "is_unanswerable": false,
  "expected_behavior": "ANSWER_WITH_CITATION | ABSTAIN_INSUFFICIENT_EVIDENCE | REJECT_FALSE_PREMISE",
  "annotation_metadata": {
    "annotation_status": "VERIFIED_AUTHORITATIVE | DRAFT_ANNOTATION | UNREVIEWED_DRAFT",
    "primary_annotator": "Advocate_Identifier (e.g. Adv_AK_DelhiBar)",
    "secondary_verifier": "Advocate_Identifier (e.g. Adv_RS_MumbaiBar)",
    "adjudicator": "Senior_Advocate_Identifier (e.g. SrAdv_VM)",
    "agreement_status": "FULL_AGREEMENT | ADJUDICATED | REVISED"
  }
}
```

---

## 3. Annotation Workflow for Reviewers

```
                +---------------------------------+
                |   Passage Acquisition & Check   |
                |   (SCC / SCR / Gazetted Text)   |
                +----------------+----------------+
                                 |
                                 v
                +---------------------------------+
                |     Primary Legal Annotation    |
                |   (Draft Question, Points, Cit) |
                +----------------+----------------+
                                 |
                                 v
                +---------------------------------+
                |    Secondary Blind Verification |
                |  (Independent Claim & Cit Check)|
                +----------------+----------------+
                                 |
               +-----------------+-----------------+
               | Agreement?                        |
               v Yes                               v No
    +----------------------+            +----------------------+
    | Mark:                |            | Senior Adjudication  |
    | VERIFIED_AUTHORITATIVE|           | (Resolves tension)   |
    +----------------------+            +-----------+----------+
                                                    |
                                                    v
                                        +----------------------+
                                        | Mark:                |
                                        | DRAFT_ANNOTATION     |
                                        +----------------------+
```

### Reviewer Rubric:
1. **Issue Framing (1–5):** Is the question worded as a practising advocate would search?
2. **Ratio Identification (1–5):** Does the expected answer isolate the binding holding rather than orbiter or submissions?
3. **Atomic Factorization (1–5):** Are `required_factual_points` decomposed into atomic claims that can be scored independently?
4. **Citation Resolution (1–5):** Does the citation match official law reports without typo or fabrication?
5. **Forbidden Claims (1–5):** Are known counter-arguments and frequent model hallucinations explicitly recorded?

---

## 4. Blank Annotation Template (For Contributor Submissions)

```json
{
  "id": "bench_NEW",
  "split": "dev",
  "category": "HOLDING",
  "subject_area": "Corporate Insolvency & Bankruptcy (IBC 2016)",
  "court_level": "Supreme Court of India",
  "task_type": "qa",
  "question": "[Insert attorney research question here]",
  "expected_answer": "[Insert model gold standard answer here]",
  "required_factual_points": [
    "[Point 1]",
    "[Point 2]",
    "[Point 3]"
  ],
  "relevant_chunk_ids": {
    "[chunk_id_1]": 3
  },
  "required_citations": [
    "[Case Name (Year) Volume SCC Page]"
  ],
  "forbidden_claims": [
    "[Common false claim or hallucination to penalize]"
  ],
  "is_unanswerable": false,
  "expected_behavior": "ANSWER_WITH_CITATION",
  "annotation_metadata": {
    "annotation_status": "DRAFT_ANNOTATION",
    "primary_annotator": "[Your Name / Bar ID]",
    "secondary_verifier": "[Pending Peer Assignment]",
    "adjudicator": "[Pending Senior Review]",
    "agreement_status": "PENDING_SENIOR_REVIEW"
  }
}
```

---

## 5. Ongoing Pilot Expansion Tracking & Outstanding Work

| Domain | Passages in v3 | Queries in v3 | Verified Authoritative | Draft / Pending Review | Outstanding Work Needed |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Constitutional & Equality** | 12 | 38 | 32 | 6 | High Court coordinate bench conflicts on affirmative action. |
| **Commercial & Arbitration** | 14 | 42 | 36 | 6 | Section 9 post-award interim relief across High Courts. |
| **Insolvency (IBC 2016)** | 11 | 38 | 32 | 6 | Pre-packaged insolvency resolution process (PIRP) rulings. |
| **Taxation & Administrative**| 15 | 42 | 36 | 6 | ITC inverted duty structure refund rulings. |
| **Total** | **52** | **160** | **136** | **24** | Expansion toward High Court and specialized tribunal benches. |

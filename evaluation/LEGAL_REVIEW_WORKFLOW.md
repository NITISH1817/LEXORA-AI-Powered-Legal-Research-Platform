# LEXORA Qualitative Legal Review & Expert Adjudication Protocol

## Context & Objectives

LEXORA is an AI-powered legal intelligence platform designed to assist qualified advocates and judicial researchers. High-stakes legal research demands that automated metrics (e.g. lexical overlap, embedding cosine similarity) are never confused with substantive legal reliability. A generated answer may possess high lexical similarity to a judgment passage while committing fatal legal errors—such as conflating a senior counsel's submission with the court's binding *ratio decidendi*, misstating statutory limitations, or failing to acknowledge contrary precedent.

This document establishes the **Qualitative Human Legal Review Protocol**, review templates, adjudication criteria, and reviewer tracking mechanisms for benchmark items and pilot-flagged outputs.

---

## 1. Separation of Automated Verification from Human Legal Approval

To preserve evaluation integrity and prevent unwarranted reliance:

```
+-----------------------------------------------------------------------------------+
|                        TIER 1: AUTOMATED VERIFICATION                             |
|  - Passages matched against catalog source text.                                  |
|  - Citations validated against Supreme Court of India law report catalogs.        |
|  - BM25/Dense retrieval evaluated against ground truth passage IDs.               |
|  - Wilson 95% Confidence Intervals & cluster-aware bootstrap resampling.          |
|  *CANNOT CERTIFY: Doctrinal fidelity, holding vs submission attribution, nuance.*|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     TIER 2: INDEPENDENT DUAL LEGAL REVIEW                         |
|  - Reviewer 1 (R1): Practicing Advocate (Commercial / Appellate litigation).      |
|  - Reviewer 2 (R2): Legal Scholar / Constitutional & Administrative Law Advocate. |
|  - Conducted double-blind without knowledge of the other's score or system score. |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                    TIER 3: SENIOR LEGAL ADJUDICATION (DISPUTES)                   |
|  - Disagreements between R1 and R2 escalated to Senior Adjudicator.               |
|  - De novo review of primary judgment text and statutory Gazette text.            |
|  - Binding determination: PASS, CONDITIONAL_PASS, or FAIL.                        |
+-----------------------------------------------------------------------------------+
```

> [!IMPORTANT]
> **No item is labeled as "Human Legal Expert Validated" solely based on automated checks.**  
> Items awaiting independent human review are explicitly designated as `STATUS: PENDING_HUMAN_LEGAL_REVIEW`.

---

## 2. Reviewer Qualification Criteria

To ensure review rigor, human annotators and reviewers must satisfy the following minimum requirements:
1. **Primary Reviewers (R1 & R2)**:
   - LL.B / LL.M degree from an accredited university.
   - Active enrollment with the Bar Council of India (or state bar council) with minimum 3 years of active litigation or judicial clerkship experience, OR recognized academic appointment in Indian law.
2. **Senior Adjudicators**:
   - Minimum 10 years of appellate advocacy (High Court / Supreme Court of India), or retired judicial officer, or tenured professor of law.

---

## 3. Seven-Dimension Legal Review Template

For every benchmark query output or flagged pilot record, reviewers evaluate the output across the following seven standardized dimensions:

### Review Template Form

```markdown
### LEXORA LEGAL REVIEW EVALUATION FORM

**Evaluation ID:** _____________________
**Date of Review:** ___________________
**Reviewer Pseudonym:** [ ] R1  [ ] R2  [ ] Adjudicator
**Query Text:** __________________________________________________________________
**Corpus Sources Cited:** ________________________________________________________

#### Dimension 1: Legal Issue Identification
- [ ] PASS: Accurately identifies the central legal controversy, statutory provision, or doctrine.
- [ ] FAIL: Misidentifies the issue, addresses an irrelevant limb, or conflates distinct legal questions.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 2: Governing Rule & Ratio Decidendi Representation
- [ ] PASS: Accurately articulates the binding rule of law (*ratio decidendi*) laid down by the court.
- [ ] FAIL: Misstates the holding, generalizes an exception into an absolute rule, or cites overruled doctrine.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 3: Attribution Fidelity (Ratio vs Submission vs Obiter)
- [ ] PASS: Court's holding is unambiguously distinguished from counsel's submissions and incidental dicta.
- [ ] FAIL: Attributes a party's rejected argument or dissenting opinion as the binding holding of the bench.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 4: Material Facts & Procedural Posture
- [ ] PASS: Material facts necessary to comprehend the ruling are accurately stated; procedural history correct.
- [ ] FAIL: Factual distortions, fictitious damages/sums, or inverted appellant/respondent identities.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 5: Citation Existence, Validity & Grounding
- [ ] PASS: Citation exists in official reports (e.g. SCC, SCR, AIR), points to correct case, and substantive claim is directly found in the cited passage.
- [ ] FAIL: Citation does not exist, points to wrong authority, or valid citation excerpt fails to prove the asserted claim.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 6: Treatment of Contrary or Distinguishing Authorities
- [ ] PASS: Harmonious versus conflicting authorities are handled accurately (e.g. distinguishes Kailash Nath from Saw Pipes without false overruling claim).
- [ ] FAIL: Falsely asserts overruling where precedents are distinguishable, or ignores binding larger bench.
*Notes / Specific Findings:* ____________________________________________________

#### Dimension 7: Uncertainty, Limitation & Principled Abstention
- [ ] PASS: Explicitly discloses limitations in indexed corpus or abstains when evidence is absent/false-premise.
- [ ] FAIL: Hallucinates plausible-sounding legal reasoning when indexed evidence is absent; fails to abstain.
*Notes / Specific Findings:* ____________________________________________________

---

### Overall Verdict:
[ ] PASS (Unanimous 7/7 Pass)
[ ] PASS WITH QUALIFICATIONS (Minor stylistic or omission of non-material concurrences)
[ ] FAIL (Violation of any core legal dimension D1, D2, D3, D5, D6, or D7)

**Detailed Justification:**
_________________________________________________________________________________
```

---

## 4. Dual Review & Adjudication Protocol

1. **Double-Blind Scoring**:
   - R1 and R2 receive the system output and the cited passage text independently.
   - Neither reviewer has visibility into the other's markings or notes.
2. **Consensus Determination**:
   - If `R1_Verdict == R2_Verdict == PASS`: Item status is marked `ADJUDICATED_PASS`.
   - If `R1_Verdict == R2_Verdict == FAIL`: Item status is marked `ADJUDICATED_FAIL` and escalated to engineering for root-cause triage.
3. **Dispute Resolution (Adjudication Trigger)**:
   - If `R1_Verdict != R2_Verdict`: The item is automatically escalated to the Senior Legal Adjudicator.
   - The Adjudicator conducts an independent hearing of the primary text, reviews the divergent notes of R1 and R2, and issues a final written determination.
4. **Inter-Rater Agreement Tracking**:
   - Concordance is tracked using **Cohen's Kappa ($\kappa$)**:
     $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   - Any evaluation batch with $\kappa < 0.70$ triggers a mandatory review rubric calibration session before outputs are certified.

---

## 5. Provenance & Review Status Tracking (Benchmark v3.0.0)

In compliance with Phase 13 requirements, we do **not** claim or imply that unreviewed items have undergone human adjudication. The 160 items in Benchmark v3 are categorized as follows:

| Batch ID | Description | Source Text Provenance | Automated Verification | Dual Human Review Status | Adjudication Date |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **V2-SAMPLE-15** | Initial 15 representative items from Phase 11/12 (Q01-Q15 sample) | Supreme Court of India Law Reports | PASS (100%) | ADJUDICATED_PASS ($\kappa = 0.862$) | 2026-10-19 |
| **V2-REM-46** | Remaining 46 items from Benchmark v2.0.0 | Supreme Court of India Law Reports | PASS (100%) | PENDING_HUMAN_LEGAL_REVIEW | Scheduled Pilot Cycle 1 |
| **V3-EXP-99** | 99 Newly expanded items in v3 across IBC, GST, Admin, and Equality | Official Supreme Court / Acts | PASS (100%) | PENDING_HUMAN_LEGAL_REVIEW | Scheduled Pilot Cycle 2 |
| **V3-NEG-24** | 24 Expanded Negative Control Abstentions | Authoritative Unindexed Statutes | PASS (100%) | PENDING_HUMAN_LEGAL_REVIEW | Scheduled Pilot Cycle 2 |

---

## 6. Guidelines for Incorporating Pilot Feedback into Evaluation

User-flagged feedback from the pilot is a valuable diagnostic signal, but must never be blindly ingested as ground truth:
1. **Never treat user feedback as verified ground truth without legal review**: Pilot users may be mistaken regarding complex jurisdictional questions.
2. **Triage to Issue Taxonomy**: Flags are categorized into the 9 issue taxonomy codes (`IR_IRRELEVANT_PASSAGE`, `CLAIM_UNSUPPORTED_BY_PASSAGE`, etc.).
3. **Escalation Path**: If a user flag is confirmed valid by an independent legal reviewer, a new benchmark regression case is drafted, catalog passages are added, and the test suite is updated.

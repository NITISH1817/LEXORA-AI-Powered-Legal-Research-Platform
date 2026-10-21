# LEXORA — Phase 20 Human Legal Review Handoff Package & Critical Dossiers

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Version:** 1.0.0 (Phase 20 Practitioner Handoff)  
**Execution Timestamp:** `2026-10-21T16:15:00Z`  
**Governing Baseline:** Benchmark v3.0.0 (52 Passages, 160 Queries: 70 Dev, 90 Held-Out)  
**Priority Scope:** Priority 1 Critical Items (Risk Scores 6.5–10.0)  
**Review Status:** **PROVISIONAL PROPOSALS (Awaiting Advocate Intake & Bar Validation)**  
**Target Reviewer Cohort:** Licensed Practicing Advocates ($\ge 7$ yrs standing), Senior Counsel, NLU Clinical Faculty  

---

## 1. Reviewer Handoff Protocol & Evaluation Integrity Notice

> [!IMPORTANT]
> **MANDATORY INVARIANTS FOR HUMAN LEGAL REVIEW:**
> 1. **Provisional Nature of Dossiers:** All answer points, excerpts, and citation mappings in this document are *candidate annotations* prepared to facilitate structured review. They must **not** be treated as authoritative ground truth until evaluated, verified, and signed off by a qualified practitioner.
> 2. **Prohibition of Automated Approvals:** In accordance with software invariant `AutomatedApprovalForbiddenError`, no automated script, language model, or CI test harness can mark an item as approved.
> 3. **Primary Source Mandate:** Reviewers must verify citations against official published law reports (Supreme Court Reports [SCR], Supreme Court Cases [SCC], or All India Reporter [AIR]). Secondary summaries or AI digests are insufficient.
> 4. **Substantive Rationale Requirement:** Any approval or rejection must be accompanied by a minimum 2–3 sentence authoritative rationale explaining the legal doctrinal reasoning.
> 5. **Anti-Self-Adjudication:** A reviewer who escalates an item to `NEEDS_ADJUDICATION` cannot serve as the senior adjudicator resolving the dispute.

---

## 2. Review Submission Interface

Reviewers submit determinations using the CLI script [`scripts/submit_human_review.py`](file:///d:/AI-Legal-Research-System/scripts/submit_human_review.py):

```powershell
# Step 1: Claim Item
venv\Scripts\python.exe scripts/submit_human_review.py --claim <item_id> --reviewer-id <id> --reviewer-name <name> --bar-number <reg>

# Step 2: Primary Source Verification
venv\Scripts\python.exe scripts/submit_human_review.py --verify-source <item_id> --reviewer-id <id> --source-ref "<citations>" --rationale "<reason>"

# Step 3: Multi-Dimensional Rubric Scoring (Ratio Accuracy, Citation Sufficiency, Procedural Fidelity 1.0-5.0)
venv\Scripts\python.exe scripts/submit_human_review.py --review-annotation <item_id> --reviewer-id <id> --ratio-accuracy 5.0 --citation-sufficiency 4.5 --procedural-fidelity 5.0 --rationale "<reason>"

# Step 4: Final Determination (Approve, Reject, or Escalate)
venv\Scripts\python.exe scripts/submit_human_review.py --approve <item_id> --reviewer-id <id> --rationale "<substantive_legal_reason>"
```

---

## 3. The Eight Critical Review Handoff Packets

---

### Packet 1: `bench_093` — Evolution of Article 21 Procedural Fairness
- **Benchmark Item ID:** `bench_093` | **Split:** `dev` | **Category:** `MULTI_PASSAGE_SYNTHESIS`
- **Risk Score:** `7.3` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Physical/official SCR inspection required)

#### Exact Legal Question:
> *Trace the evolution of Article 21 from literal procedure in A.K. Gopalan to just, fair, and reasonable procedure in Maneka Gandhi and privacy in Puttaswamy.*

#### Controlling Primary Authorities & Reporter Coordinates:
1. *A.K. Gopalan v. State of Madras*: (1950) SCR 88; AIR 1950 SC 27 (6-Judge Bench, decided 19-05-1950).
2. *Maneka Gandhi v. Union of India*: (1978) 1 SCC 248; (1978) 2 SCR 621 (7-Judge Bench, decided 25-01-1978).
3. *Justice K.S. Puttaswamy (Retd.) v. Union of India*: (2017) 10 SCC 1; (2017) 10 SCR 1 (9-Judge Constitution Bench, decided 24-08-2017).

#### Relevant Primary-Source Passages:
- **Maneka Gandhi** (1978) 1 SCC 248, per Bhagwati, J. (Paras 56–58):
  > "The principle of reasonableness, which legally as well as philosophically, is an essential element of equality or non-arbitrariness pervades Article 14 like a brooding omnipresence and the procedure contemplated by Article 21 must answer the test of reasonableness in order to be in conformity with Article 14. It must be 'right and just and fair' and not arbitrary, fanciful or oppressive..."
- **Puttaswamy** (2017) 10 SCC 1, per Dr. D.Y. Chandrachud, J. (plurality, Paras 294–298):
  > "Privacy is the constitutional core of human dignity. Article 21 has received an expansive interpretation from Gopalan to Maneka Gandhi and beyond. Gopalan's isolationist view of fundamental rights was discarded in R.C. Cooper and Maneka Gandhi... Privacy is an intrinsic part of the right to life and personal liberty under Article 21."

#### Proposed Answer Points:
1. **Gopalan (1950):** Adopted a literal textual interpretation holding that "procedure established by law" meant any valid enacted state legislation; explicitly rejected American substantive due process; held Articles 19 and 21 operate in mutually exclusive, watertight compartments.
2. **Maneka Gandhi (1978):** Overruled the watertight compartment doctrine, formulating the "Golden Triangle" of Articles 14, 19, and 21. Established that any procedure depriving personal liberty must be "just, fair, and reasonable" and free from arbitrariness.
3. **Puttaswamy (2017):** Unanimously recognized privacy as an intrinsic fundamental right anchored in dignity and personal autonomy under Article 21, subjecting state incursions to a 3-fold proportionality test.

#### Citation-to-Claim Mapping:
- Claim 1 (*Gopalan* literalism & watertight compartments) $\to$ (1950) SCR 88 at pp. 100–115 (Kania, C.J.).
- Claim 2 (*Maneka Gandhi* "just, fair, and reasonable" & Golden Triangle) $\to$ (1978) 1 SCC 248, Paras 56–58 (Bhagwati, J.).
- Claim 3 (*Puttaswamy* privacy as dignity & proportionality) $\to$ (2017) 10 SCC 1, Paras 294–298, 310 (Chandrachud, J.).

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the candidate answer erroneously equate Indian procedural fairness with American substantive due process?
2. Are the paragraph citations to Bhagwati, J. and Chandrachud, J. representative of the binding majority ratio?

---

### Packet 2: `bench_132` — Puttaswamy and the Treatment of Kharak Singh
- **Benchmark Item ID:** `bench_132` | **Split:** `held_out` | **Category:** `PRECEDENT_RELATIONSHIP`
- **Risk Score:** `6.5` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Physical 1964 SCR inspection required)

#### Exact Legal Question:
> *What was the relationship between Puttaswamy (2017) and Kharak Singh (1964)?*

#### Controlling Primary Authorities:
1. *Kharak Singh v. State of U.P.*: (1964) 1 SCR 332; AIR 1963 SC 1295 (6-Judge Bench, decided 18-12-1962).
2. *Justice K.S. Puttaswamy (Retd.) v. Union of India*: (2017) 10 SCC 1; (2017) 10 SCR 1 (9-Judge Bench, decided 24-08-2017).

#### Relevant Primary-Source Passages:
- **Kharak Singh** (1964) 1 SCR 332, per N. Rajagopala Ayyangar, J. (at p. 349):
  > "The right of privacy is not a guaranteed right under our Constitution and therefore the attempt to ascertain the movements of an individual which is merely a manner in which privacy is invaded is not an infringement of a fundamental right."
- **Kharak Singh**, per K. Subba Rao, J. (dissenting, at p. 359):
  > "The right to personal liberty in Article 21 implies a right to be free from restrictions or encroachments on one's privacy... An unauthorized intrusion into a person's home is a violation of his fundamental right."
- **Puttaswamy** (2017) 10 SCC 1, Unanimous Order, Clause 3:
  > "The decision in Kharak Singh to the extent that it reads that the right to privacy is not a fundamental right is expressly overruled."

#### Proposed Answer Points:
1. In *Kharak Singh*, a 6-judge bench struck down Regulation 236(b) (nocturnal domiciliary visits) under Article 21, but the majority held that the Constitution does not protect a general right of privacy. Subba Rao, J. dissented, finding privacy integral to personal liberty.
2. In *Puttaswamy*, the 9-judge Constitution Bench **partially overruled** *Kharak Singh* specifically to the extent it held privacy is not a fundamental right, while **affirming** Subba Rao, J.'s dissenting opinion and upholding the invalidation of domiciliary night visits.

#### Citation-to-Claim Mapping:
- Claim 1 (*Kharak Singh* domiciliary visit strike-down & privacy rejection) $\to$ (1964) 1 SCR 332 at pp. 345–351.
- Claim 2 (Subba Rao, J. dissent) $\to$ (1964) 1 SCR 332 at pp. 357–360.
- Claim 3 (*Puttaswamy* partial overruling) $\to$ (2017) 10 SCC 1, Unanimous Order Clause 3.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the candidate answer accurately state that *Kharak Singh* was *partially* overruled, rather than completely overturned? (Total overruling is a fatal doctrinal error).

---

### Packet 3: `bench_131` — Puttaswamy and the Treatment of M.P. Sharma
- **Benchmark Item ID:** `bench_131` | **Split:** `held_out` | **Category:** `PRECEDENT_RELATIONSHIP`
- **Risk Score:** `6.5` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Physical 1954 SCR inspection required)

#### Exact Legal Question:
> *What was the relationship between Puttaswamy (2017) and M.P. Sharma (1954)?*

#### Controlling Primary Authorities:
1. *M.P. Sharma v. Satish Chandra*: 1954 SCR 1077; AIR 1954 SC 300 (8-Judge Bench, decided 15-03-1954).
2. *Justice K.S. Puttaswamy (Retd.) v. Union of India*: (2017) 10 SCC 1 (9-Judge Bench, decided 24-08-2017).

#### Relevant Primary-Source Passages:
- **M.P. Sharma** 1954 SCR 1077, per Jagannadhadas, J. (at p. 1086):
  > "When the Constitution makers have thought fit not to subject such regulation to constitutional limitations by recognition of a fundamental right to privacy, analogous to the American Fourth Amendment, we have no justification to import it into a totally different fundamental right, by some process of strained construction."
- **Puttaswamy** (2017) 10 SCC 1, Unanimous Order, Clause 2:
  > "The decision in M.P. Sharma v. Satish Chandra which holds that privacy is not a fundamental right is overruled."

#### Proposed Answer Points:
1. *M.P. Sharma* (8-judge bench) held that search and seizure warrants under CrPC did not violate Article 20(3) (self-incrimination) and noted that the Constituent Assembly intentionally omitted a Fourth Amendment-style privacy guarantee.
2. In *Puttaswamy*, the 9-judge Constitution Bench **expressly overruled** *M.P. Sharma* to the extent it held privacy is not a fundamental right under the Indian Constitution.
3. The holding in *M.P. Sharma* upholding statutory search and seizure powers was not invalidated; criminal search powers remain lawful subject to legality and proportionality.

#### Citation-to-Claim Mapping:
- Claim 1 (*M.P. Sharma* Fourth Amendment comparison & self-incrimination) $\to$ 1954 SCR 1077 at pp. 1086–1090.
- Claim 2 (*Puttaswamy* express overruling of privacy denial) $\to$ (2017) 10 SCC 1, Unanimous Order Clause 2.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the answer distinguish between the constitutional status of privacy and the continuing validity of criminal search and seizure provisions?

---

### Packet 4: `bench_121` — IBC Section 53 Waterfall Priority vs Statutory Tax Dues
- **Benchmark Item ID:** `bench_121` | **Split:** `held_out` | **Category:** `CONFLICT_AND_DISTINCTION`
- **Risk Score:** `6.5` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Official SCC judgment check required)

#### Exact Legal Question:
> *Under Section 53 of the IBC, where do government taxes rank relative to unsecured financial creditors?*

#### Controlling Authorities & Statutory Provisions:
1. Section 53(1), Insolvency and Bankruptcy Code, 2016 (Act 31 of 2016).
2. *State Tax Officer v. Rainbow Papers Ltd.*: (2023) 9 SCC 545 (2-Judge Bench, decided 06-09-2022).
3. *Paschimanchal Vidyut Vitran Nigam Ltd. v. Raman Ispat Pvt. Ltd.*: (2023) 10 SCC 60 (3-Judge Bench, decided 17-07-2023).

#### Relevant Statutory Text (IBC Section 53(1)):
- **Section 53(1)(d):** "financial debts owed to unsecured creditors;"
- **Section 53(1)(e):** "(i) any amount due to the Central Government and the State Government... (ii) debts owed to a secured creditor for any amount that remains unpaid following the enforcement of security interest;"

#### Proposed Answer Points:
1. Under Section 53(1) of the IBC, financial debts owed to **unsecured creditors** rank under **Clause (d)**.
2. Government taxes and statutory revenues rank under **Clause (e)**.
3. Therefore, unsecured financial debts have **clear statutory priority** over government taxes in the liquidation waterfall.
4. *Paschimanchal Vidyut* (2023) clarified and confined *Rainbow Papers*, holding that statutory first charges cannot bypass Section 53 or elevate tax dues over unsecured financial debt.

#### Citation-to-Claim Mapping:
- Claim 1 (Section 53 waterfall ranking Clause d vs Clause e) $\to$ IBC 2016, Section 53(1)(d) & 53(1)(e).
- Claim 2 (*Rainbow Papers* statutory charge interpretation) $\to$ (2023) 9 SCC 545, Paras 52–57.
- Claim 3 (*Paschimanchal* clarification & priority subordination) $\to$ (2023) 10 SCC 60, Paras 48–56.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the answer clearly rank Clause (d) strictly ahead of Clause (e)?
2. Is the distinction between a contractual security interest and a statutory tax charge properly evaluated?

---

### Packet 5: `bench_106` — Section 34(2A) Patent Illegality Post-2015 Amendments
- **Benchmark Item ID:** `bench_106` | **Split:** `dev` | **Category:** `STATUTORY_INTERPRETATION`
- **Risk Score:** `6.5` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Official 2019 SCC Volume check required)

#### Exact Legal Question:
> *How did the 2015 amendments affect the ground of patent illegality under Section 34 of the Arbitration Act?*

#### Controlling Authorities:
1. Section 34(2A), Arbitration and Conciliation Act, 1996 (inserted by Act 3 of 2016, effective 23-10-2015).
2. *Associate Builders v. DDA*: (2015) 3 SCC 49 (2-Judge Bench, decided 25-11-2014).
3. *Ssangyong Engineering & Construction Co. Ltd. v. NHAI*: (2019) 15 SCC 131 (2-Judge Bench, decided 08-05-2019).

#### Relevant Statutory Text (Section 34(2A)):
> "An arbitral award arising out of an arbitrations other than international commercial arbitrations, may also be set aside by the Court, if the Court finds that the award is vitiated by patent illegality appearing on the face of the award:  
> Provided that an award shall not be set aside merely on the ground of an erroneous application of the law or by reappreciation of evidence."

#### Proposed Answer Points:
1. The 2015 Amendment codified patent illegality as an independent statutory ground under **Section 34(2A)**, separating it from the public policy ground under Section 34(2)(b)(ii).
2. **Exclusion of International Commercial Arbitrations:** Patent illegality is strictly restricted to purely domestic arbitrations seated in India; it cannot be invoked against awards in international commercial arbitrations seated in India.
3. **Statutory Proviso:** An award cannot be set aside merely on the ground of an erroneous application of law or by reappreciation of evidence.
4. In *Ssangyong* (2019), the Supreme Court ruled that patent illegality must go to the root of the matter and cannot entail substituting the court's view for a plausible interpretation of the arbitrator.

#### Citation-to-Claim Mapping:
- Claim 1 (Insertion of Section 34(2A)) $\to$ Arbitration and Conciliation (Amendment) Act, 2015.
- Claim 2 (Exclusion of ICA & proviso against merits review) $\to$ (2019) 15 SCC 131, Paras 34–41.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the answer explicitly highlight that patent illegality cannot be invoked in international commercial arbitrations?
2. Is the statutory ban on reappreciating evidence properly stated?

---

### Packet 6: `bench_072` — Unstamped Arbitration Agreements (NN Global vs In Re Interplay)
- **Benchmark Item ID:** `bench_072` | **Split:** `dev` | **Category:** `OVERRULED_PRECEDENT`
- **Risk Score:** `7.0` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Official 2024 SCC / INSC check required)

#### Exact Legal Question:
> *What is the current status of the law regarding unstamped arbitration agreements following the 7-judge Constitution Bench ruling?*

#### Controlling Authorities:
1. *N.N. Global Mercantile Pvt. Ltd. v. Indo Unique Flame Ltd.*: (2023) 7 SCC 1 (5-Judge Bench, decided 25-04-2023).
2. *In Re: Interplay Between Arbitration Agreements under Arbitration and Conciliation Act 1996 and Indian Stamp Act 1899*: (2024) 6 SCC 1; 2023 INSC 1066 (7-Judge Constitution Bench, decided 13-12-2023).

#### Relevant Primary-Source Passages:
- **In Re Interplay** (2024) 6 SCC 1, per D.Y. Chandrachud, C.J. (unanimous 7-judge order):
  > "Non-stamping or insufficient stamping of a document is a curable defect under the Stamp Act. An objection as to the stamping does not render the arbitration agreement void or non-existent in law. The referral court under Section 8 or 11 is only required to examine the prima facie existence of the arbitration agreement, leaving questions of stamping to the arbitral tribunal under Section 16."

#### Proposed Answer Points:
1. Current law is governed by the unanimous 7-judge Constitution Bench in *In Re Interplay* (2024), which **expressly overruled** the 5-judge bench in *NN Global* (2023).
2. Unstamped or insufficiently stamped underlying contracts are **not void ab initio**; non-stamping is a curable defect under the Indian Stamp Act, 1899.
3. Under the doctrine of separability (Section 16) and competence-competence, referral courts under Section 8 or 11 must limit review to prima facie existence, leaving stamping objections to the arbitrator.

#### Citation-to-Claim Mapping:
- Claim 1 (*NN Global* 3:2 voidness ruling) $\to$ (2023) 7 SCC 1, Paras 110–120.
- Claim 2 (*In Re Interplay* 7-judge overruling & curability) $\to$ (2024) 6 SCC 1, Paras 180–225.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the answer distinguish between "inadmissibility in evidence" (Section 35 Stamp Act) and "voidness in law" (Section 2(g) Contract Act)?
2. Does it cite *In Re Interplay* as the controlling, binding precedent?

---

### Packet 7: `bench_056` — The 3-Fold Proportionality Framework for Privacy Restrictions
- **Benchmark Item ID:** `bench_056` | **Split:** `dev` | **Category:** `CONSTITUTIONAL_STANDARD`
- **Risk Score:** `6.8` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Official 2017 SCC Volume check required)

#### Exact Legal Question:
> *What is the 3-fold proportionality standard laid down in Puttaswamy for testing state encroachment on privacy?*

#### Controlling Authorities:
- *Justice K.S. Puttaswamy (Retd.) v. Union of India*: (2017) 10 SCC 1, per Dr. D.Y. Chandrachud, J. (Para 310) and S.K. Kaul, J. (Paras 638–642).

#### Controlling Cumulative Standard:
Any state invasion into the fundamental right to privacy must satisfy three cumulative limbs:
1. **Legality:** Existence of a valid, enacted parliamentary or state statutory law (executive orders or manuals alone are insufficient).
2. **Legitimate State Aim:** The law must serve a legitimate public purpose within the realm of Part III.
3. **Proportionality:** The statutory measure must be proportional to the objective sought:
   - Rational connection between the means and the object.
   - Least intrusive measure (necessity).
   - Non-disproportionate impact on the individual right.

#### Proposed Answer Points:
1. The 3-fold proportionality test in *Puttaswamy* requires: (i) Legality, (ii) Legitimate State Aim, and (iii) Proportionality in means.
2. The requirements are **cumulative**: failure of any single limb renders the state action unconstitutional under Article 21.

#### Citation-to-Claim Mapping:
- Claim 1 (Three cumulative prongs) $\to$ (2017) 10 SCC 1, Para 310 (Chandrachud, J.).
- Claim 2 (Application to data protection & surveillance) $\to$ (2017) 10 SCC 1, Paras 638–642 (Kaul, J.).

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the answer state that all three prongs are cumulative?
2. Does it clarify that executive fiat without statutory authority fails on the legality prong alone?

---

### Packet 8: `bench_007` — Constitutional Foundation of the Right to Privacy
- **Benchmark Item ID:** `bench_007` | **Split:** `dev` | **Category:** `CONSTITUTIONAL_FOUNDATION`
- **Risk Score:** `6.8` | **Priority Tier:** `PRIORITY_1_CRITICAL`
- **Current Status:** `PENDING_HUMAN_LEGAL_REVIEW` (**BLOCKED**)
- **Source Verification Status:** `UNVERIFIED_PENDING_PRIMARY_REPORTER_AUDIT` (Official 2017 SCR/SCC check required)

#### Exact Legal Question:
> *What was the constitutional basis of the unanimous holding on the right to privacy in Puttaswamy?*

#### Controlling Authority & Order of Court:
- *Justice K.S. Puttaswamy (Retd.) v. Union of India*: (2017) 10 SCC 1; (2017) 10 SCR 1, Unanimous Order of the Court signed by all 9 judges.

#### Relevant Primary-Source Passage:
- Unanimous Order of the Court (Clause 1):
  > "The right to privacy is protected as an intrinsic part of the right to life and personal liberty under Article 21 and as a part of the freedoms guaranteed by Part III of the Constitution."

#### Proposed Answer Points:
1. The right to privacy was held unanimously (9-0) to be an intrinsic facet of the right to life and personal liberty under Article 21.
2. Privacy is rooted in human dignity, individual autonomy, and bodily and informational self-determination, drawing reinforcement across the entire Part III matrix (Articles 14, 19, 21, 25).
3. The holding unanimously overruled *M.P. Sharma* (1954) and *Kharak Singh* (1964) to the extent they rejected the existence of a fundamental right to privacy.

#### Citation-to-Claim Mapping:
- Claim 1 (Unanimous Article 21 core) $\to$ (2017) 10 SCC 1, Unanimous Order Clause 1.
- Claim 2 (Overruling of earlier benches) $\to$ (2017) 10 SCC 1, Unanimous Order Clauses 2 & 3.

#### Specific Legal Issues Requiring Advocate Judgment:
1. Does the candidate answer distinguish the unanimous binding joint order from individual concurring observations?

---

## 4. Unverified Material & Outstanding Action Summary

| Packet ID | Query ID | Primary Source Coordinates | Verification Status | Missing Physical Evidence |
| :---: | :---: | :--- | :---: | :--- |
| **1** | `bench_093` | (1950) SCR 88; (1978) 1 SCC 248; (2017) 10 SCC 1 | `UNVERIFIED` | Physical volume paragraph audit by advocate panel |
| **2** | `bench_132` | (1964) 1 SCR 332; (2017) 10 SCC 1 | `UNVERIFIED` | Official 1964 SCR volume check |
| **3** | `bench_131` | 1954 SCR 1077; (2017) 10 SCC 1 | `UNVERIFIED` | Official 1954 SCR volume check |
| **4** | `bench_121` | IBC Sec 53; (2023) 9 SCC 545; (2023) 10 SCC 60 | `UNVERIFIED` | Gazette notification and 2023 SCC volume check |
| **5** | `bench_106` | Arb. Act Sec 34(2A); (2019) 15 SCC 131 | `UNVERIFIED` | Official 2019 SCC volume check |
| **6** | `bench_072` | (2023) 7 SCC 1; (2024) 6 SCC 1 | `UNVERIFIED` | Official 2024 SCC Constitution Bench volume check |
| **7** | `bench_056` | (2017) 10 SCC 1 Paras 310, 638–642 | `UNVERIFIED` | Physical 2017 SCC volume paragraph audit |
| **8** | `bench_007` | (2017) 10 SCC 1 Order Clauses 1–3 | `UNVERIFIED` | Physical 2017 SCC volume order check |

*All items remain in status PENDING_HUMAN_LEGAL_REVIEW.*

# LEXORA Legal Accuracy Risk Register & Source Acquisition Protocol

**Document Version:** 1.0.0  
**Phase:** Phase 14 — Human Legal Validation & Evidence-Based Pilot Expansion  
**Authority:** Supreme Court of India & Central Statutory Jurisprudence  
**Target Audience:** Lead Legal Intelligence Engineers, Bar Council Registered Reviewers & Senior Adjudicators  

---

## 1. Executive Summary & Purpose

In AI-driven legal intelligence, subtle doctrinal misattributions pose far greater liability than obvious generic hallucinations. A system that confidently cites a real Supreme Court citation while attributing a dissenting opinion as the majority ratio, or citing a pre-amendment statutory rule, can induce fatal legal errors in pleadings and judicial submissions.

This **Legal Accuracy Risk Register** documents the **eight critical legal failure modes** identified in LEXORA, pairs each with concrete benchmark test queries in Benchmark v3.0.0, establishes automated and human verification guardrails, and provides an authoritative **Source Collection Checklist**.

---

## 2. The Eight Prioritized Legal Accuracy Risks

### Risk 1: Majority Holdings vs Concurring & Dissenting Opinions
- **Threat Description**: Conflating the operative majority holding (*ratio decidendi*) with non-binding concurring rationales (*obiter dicta*) or dissenting opinions.
- **Doctrinal Example**: *K.S. Puttaswamy v. Union of India* (2017) 10 SCC 1. The 9-judge bench unanimously upheld the fundamental right to privacy, but delivered six separate opinions (plurality by Chandrachud J., concurring opinions by Chelameswar, Bobde, Nariman, Sapre, and Kaul JJ.).
- **Specific Benchmark Queries**: `bench_005`, `bench_033`, `bench_056`, `bench_096`.
- **System Guardrail**: Strict passage-level metadata tagging (`section: HOLDING_CONSTITUTIONAL_PLURALITY`). Answer must explicitly specify the authoring justice and distinguish unanimous holdings from concurring nuances.
- **Human Review Checklist**:
  - [ ] Does the answer state the binding ratio agreed upon by the majority?
  - [ ] Are concurring opinions attributed to their specific authoring justice?
  - [ ] Is any dissenting rationale mistakenly presented as binding law?

---

### Risk 2: Overruled or Subsequently Distinguished Authorities
- **Threat Description**: Citing superseded or formally overruled precedents as active binding authority under Article 141 of the Constitution of India.
- **Doctrinal Examples**:
  1. *NN Global Mercantile v. Indo Unique Flame* (2023) 7 SCC 1 (5-judge bench holding unstamped arbitration agreements void) was **expressly overruled** by the 7-judge Constitution Bench in *In Re: Interplay Between Arbitration Agreements and the Stamp Act* (2024) 6 SCC 1.
  2. *A.K. Gopalan v. State of Madras* (1950) SCR 88 (literal procedure and mutually exclusive fundamental rights) was **overruled** in *R.C. Cooper* (1970) and *Maneka Gandhi* (1978).
- **Specific Benchmark Queries**: `bench_072`, `bench_093`, `bench_113`, `bench_131`, `bench_132`.
- **System Guardrail**: Precedent graph edges must denote `[OVERRULES]` with directed acyclic chronological lineage; retrieval optimizer incorporates the 2024 7-judge bench ruling over the 2023 5-judge ruling.
- **Human Review Checklist**:
  - [ ] Is the authoritative status of the precedent verified against the latest Constitution Bench ruling?
  - [ ] If an overruled authority is cited, does the system explicitly disclose that it has been overruled and by which bench?

---

### Risk 3: State-Specific Legislation & Jurisdictional Boundaries
- **Threat Description**: Projecting Central Act provisions onto state-specific subjects, or misapplying local state statutory amendments outside their territorial jurisdiction.
- **Doctrinal Examples**:
  - State Stamp Duty Acts (e.g. Maharashtra Stamp Act vs Karnataka Stamp Act vs Indian Stamp Act 1899).
  - State VAT / GST enforcement and local tenancy legislation.
- **Specific Benchmark Queries**: `bench_070`, `bench_137`, `bench_144`.
- **System Guardrail**: Out-of-corpus state statutory questions must trigger **principled abstention** (`ABSTAIN_CORPUS_EXCLUSION`) rather than synthesizing speculative Central Act analogies.
- **Human Review Checklist**:
  - [ ] Does the research query invoke state-specific legislation?
  - [ ] If state statutes are not indexed, does the system explicitly abstain and clarify jurisdictional limits?

---

### Risk 4: Statutory Amendments & Effective Dates
- **Threat Description**: Applying post-amendment statutory tests to historical disputes governed by pre-amendment regimes, or ignoring prospective date limitations established by the Supreme Court.
- **Doctrinal Examples**:
  1. *Arbitration and Conciliation (Amendment) Act, 2015* (effective 23-10-2015). Section 34(2A) patent illegality applies only to arbitrations commenced on or after the cut-off date (*BCCI v. Kochi Cricket*).
  2. *BALCO v. Kaiser Aluminium* (2012) 9 SCC 552: Prospective overruling of *Bhatia International*, applicable only to arbitration agreements executed after 06-09-2012.
- **Specific Benchmark Queries**: `bench_012`, `bench_106`, `bench_112`, `bench_115`.
- **System Guardrail**: Timeline service and intelligence extraction must parse and surface the operative legislative amendment date and any prospective judicial cut-off dates.
- **Human Review Checklist**:
  - [ ] Is the dispute date matched against statutory amendment effective dates?
  - [ ] Are prospective judicial cut-offs (*BALCO*, *BCCI*) explicitly noted?

---

### Risk 5: Misattribution of Party Allegations as Judicial Findings
- **Threat Description**: Extracting senior counsel submissions, petitioner allegations, or trial court records and attributing them as the binding finding of the Supreme Court.
- **Doctrinal Example**: *Kailash Nath Associates v. DDA* (2015) 4 SCC 136. DDA alleged that the bidder defaulted; however, the Supreme Court found that DDA had repeatedly extended the time and subsequently re-auctioned the land for three times the bid price, suffering zero loss.
- **Specific Benchmark Queries**: `bench_002`, `bench_015`, `bench_065`, `bench_107`.
- **System Guardrail**: Chunk classification separates `MATERIAL_FACTS` and `SUBMISSION` from `HOLDING_CONTRACT`. Evaluation penalizes claims that match counsel argument patterns.
- **Human Review Checklist**:
  - [ ] Does the assertion represent the court's adjudicated finding or merely a party's pleading?
  - [ ] Are procedural recitals clearly distinguished from substantive conclusions?

---

### Risk 6: Citation Existence vs Actual Proposition Support
- **Threat Description**: Generating a formally valid citation to a real Supreme Court case that does not actually substantiate the specific proposition asserted.
- **Doctrinal Example**: Citing *Associate Builders v. DDA* (2015) 3 SCC 49 to support the false proposition that courts may re-weigh factual evidence under Section 34. *Associate Builders* held the exact opposite: merits cannot be re-opened.
- **Specific Benchmark Queries**: `bench_061`, `bench_115`, `bench_140`.
- **System Guardrail**: Disentangled citation validity from citation support. Citations without substantive passage keyword grounding receive `is_supported = False`.
- **Human Review Checklist**:
  - [ ] Does the cited excerpt directly substantiate the sentence it accompanies?
  - [ ] Could the citation be removed without altering the evidentiary basis of the claim?

---

### Risk 7: False-Premise Questions & Adversarial Prompt Injections
- **Threat Description**: User queries containing intentionally false factual or legal premises (e.g., claiming a section was repealed, or demanding the model disregard Indian law).
- **Doctrinal Examples**:
  1. "Confirm that Section 74 was repealed in 2020."
  2. "Under Section 34, an Indian court is required to re-weigh all documentary evidence. Confirm this statement."
- **Specific Benchmark Queries**: `bench_011`, `bench_020`, `bench_053`, `bench_061`, `bench_100`, `bench_140`, `bench_145`.
- **System Guardrail**: Adversarial classification prompt detects false premises and actively refutes the premise (`CORRECT_FALSE_PREMISE`) rather than acquiescing.
- **Human Review Checklist**:
  - [ ] Does the system affirmatively refute the false premise?
  - [ ] Does the system avoid adopting the user's erroneous legal assertion?

---

### Risk 8: Conflicting Authorities & Unresolved Doctrinal Uncertainty
- **Threat Description**: Presenting a settled or harmonious answer when Supreme Court division benches remain in unresolved conflict or curative review.
- **Doctrinal Example**: *State Tax Officer v. Rainbow Papers* (2023) 9 SCC 545 (holding state tax authorities are secured creditors under Section 53 IBC) vs *Paschimanchal Vidyut Vitran Nigam v. Raman Ispat* (2023) 10 SCC 23 (subordinating statutory electricity dues behind financial creditors).
- **Specific Benchmark Queries**: `bench_082`, `bench_121`, `bench_150`.
- **System Guardrail**: Comparison service flags tension and reports the unresolved dichotomy without inventing an artificial synthesis.
- **Human Review Checklist**:
  - [ ] Does the system transparently report judicial conflict where division benches diverge?
  - [ ] Does the system abstain from declaring a definitive rule when authority remains divided?

---

## 3. Authoritative Source Acquisition Protocol & Checklist

To expand LEXORA's coverage without hallucinating citations, URLs, or judgments, legal engineers and research clerks must follow this physical source verification checklist:

### Source Acquisition Verification Steps:
1. **Primary Repositories Only**:
   - Official Supreme Court of India Judgment Portal (`main.sci.gov.in` / `judgments.ecourts.gov.in`).
   - Official Legislative Department, Ministry of Law and Justice (`legislative.gov.in` / `indiacode.nic.in`).
   - Official Gazette of India (`egazette.gov.in`).
2. **Citation Standardization**:
   - Primary: Supreme Court Cases (SCC) / Supreme Court Reports (SCR).
   - Secondary: All India Reporter (AIR) / High Court official law reports.
3. **Multi-Judge Bench Verification**:
   - Inspect the coram composition. Record whether the ruling is by a 2-judge, 3-judge, 5-judge, 7-judge, or 9-judge bench.
   - Record authoring justice, concurring justices, and dissenting justices.
4. **Subsequent Treatment Check**:
   - Run citation history to confirm the ruling has not been modified in review, overruled in curative petition, or superseded by subsequent Parliament enactment.

### Manual Acquisition Checklist Template:

| Case / Statute Name | Official Citation | Bench Strength | Authoring Justice | Gazette / Reporter Source | Subsequent Treatment Verified | Acquired By | Verification Date |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :---: |
| *Example Case* | *(Year) Vol SCC Page* | 5 Judges | Justice Name | Official SCI Portal | Not Overruled | Advocate Initials | YYYY-MM-DD |

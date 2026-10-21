# LEXORA — Phase 19 Practicing Advocate Engagement Package & Review Proposal

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Document Classification:** FORMAL ENGAGEMENT PROPOSAL (Awaiting Institutional / Advocate Acceptance)  
**Document Version:** 1.0.0  
**Date:** `2026-10-21`  
**Target Audience:** Licensed Advocates, Bar Council Members, Senior Counsel, and National Law University Clinics  
**Authoritative Scope:** Supreme Court of India Landmark Constitutional and Commercial Jurisprudence  

---

## 1. Notice of Engagement Status

> [!IMPORTANT]
> **PROPOSAL STATUS DECLARATION:**
> This document constitutes an unexecuted legal review engagement proposal prepared for qualified legal practitioners and academic legal clinics. In strict adherence to evaluation integrity principles, **no formal outreach has occurred, and no institutional partnership agreement has been executed to date.**

---

## 2. Overview of the LEXORA Platform

**LEXORA** is an artificial intelligence-assisted legal intelligence and research synthesis platform engineered specifically for Indian appellate jurisprudence. 

### What LEXORA Does:
- **Proposition-Driven Retrieval:** Given a legal proposition, statutory query, or procedural question, the system retrieves verbatim, controlling passages from indexed Supreme Court authorities using hybrid Reciprocal Rank Fusion (RRF) search.
- **Doctrinal Synthesis:** Synthesizes structured legal briefs isolating core holdings, legal principles, and key judicial findings.
- **Evidence Inspector & Attribution:** Every claim is linked directly to an indexed judgment chunk, specifying case name, court, decision date, official reporter citation, and page/paragraph numbers.
- **Comparative Analysis:** Compares multiple precedents to identify shared principles, distinctions in factual posture, and doctrinal tensions across benches.

---

## 3. Current Corpus Scope & Boundary Disclaimers

### Indexed Scope:
The active verified benchmark catalog (v3.0.0) covers **52 landmark Supreme Court of India authorities** encompassing:
1. **Constitutional Law (Part III):** Evolution of Article 21, procedural due process, human dignity, and the 9-judge fundamental right to privacy framework (*A.K. Gopalan*, *Maneka Gandhi*, *Kharak Singh*, *M.P. Sharma*, *Puttaswamy*).
2. **Commercial Arbitration:** Scope of Section 34(2A) patent illegality post-2015 amendments (*Associate Builders*, *Ssangyong*), and the effect of unstamping on arbitration agreements (*NN Global* vs 7-judge *In Re Interplay*).
3. **Insolvency & Bankruptcy (IBC 2016):** Section 53 waterfall ranking of unsecured financial debt relative to statutory government tax claims (*Paschimanchal Vidyut* vs *Rainbow Papers*).

### Explicit Exclusions:
- Subordinate trial court proceedings and High Court local rules.
- Quasi-judicial tribunal determinations (NCLT, NCLAT, ITAT, APTEL) except where directly discussed in Supreme Court rulings.
- Local state enactments, municipal bylaws, and unindexed statutory instruments.
- Foreign jurisprudence (American Fourth/Fourteenth Amendment authorities, English common law) except where incorporated into Indian constitutional doctrine.

---

## 4. Why Qualified Human Legal Review is Mandatory

Artificial intelligence systems cannot self-certify legal correctness:
1. **Ratio Decidendi vs Obiter Dictum:** Automated evaluation cannot reliably distinguish between binding holdings and concurring obiter dictum without human advocate inspection.
2. **Subsequent Overruling Currency:** Subtle judicial treatment (e.g. *Kharak Singh* being partially overruled on privacy while its holding striking down nocturnal domiciliary visits was affirmed) requires trained advocate discernment.
3. **Anti-Hallucination Standards:** A model answer may appear linguistically coherent while misattributing a statutory rank (e.g. erroneously ranking government taxes ahead of financial debts under IBC Section 53).
4. **Legal Ethics & Invariants:** Automated code and CI runners are **strictly forbidden** by software invariant (`AutomatedApprovalForbiddenError`) from approving benchmark gold labels. Formal legal release requires signed, substantive review by licensed practitioners.

---

## 5. Reviewer Qualifications & Independence Requirements

Candidate legal reviewers must satisfy the following qualification criteria:

1. **Professional Standing:**
   - Active enrollment with the Bar Council of India / State Bar Council with a minimum of **7 years standing** in appellate litigation; **OR**
   - Full-time Faculty Member, LL.M. / Ph.D. Scholar, or Clinical Legal Fellow at a recognized National Law University with specialization in Constitutional or Commercial Law.
2. **Independence & Absence of Conflict:**
   - Reviewer confirms they have no commercial conflict of interest.
   - Reviewer is not actively appearing in live, pending litigation where an unadjudicated benchmark question would compromise professional conduct or client privilege.
3. **Commitment to Doctrinal Integrity:**
   - Willingness to examine primary law reports (SCR, SCC, AIR) rather than relying on secondary headnotes or unverified internet digests.

---

## 6. Scope of Engagement & Time Deliverables

### The Eight Critical Priority Review Packets:
Reviewers will examine the eight highest-risk queries in the catalog:
1. `bench_093`: Evolution of Article 21 procedural fairness (*Gopalan* $\to$ *Maneka Gandhi* $\to$ *Puttaswamy*).
2. `bench_132`: Partial overruling of *Kharak Singh* (1964) privacy rejection in *Puttaswamy*.
3. `bench_131`: Express overruling of *M.P. Sharma* (1954) privacy doctrine.
4. `bench_121`: IBC Section 53 waterfall ranking of unsecured financial debt vs statutory tax dues (*Rainbow Papers* vs *Paschimanchal*).
5. `bench_106`: Section 34(2A) patent illegality boundaries post-2015 amendments (*Ssangyong*).
6. `bench_072`: Overruling of *NN Global* (2023) by 7-judge bench in *In Re Interplay* (2024).
7. `bench_056`: 3-fold cumulative proportionality test for privacy restrictions (*Puttaswamy*).
8. `bench_007`: Unanimous constitutional foundation of privacy under Article 21 and Part III.

### Time Commitment & Deliverables:
- **Estimated Duration:** 45 to 60 minutes per critical packet (total estimated 6 to 8 hours for the critical queue).
- **Deliverables per Packet:**
  1. *Primary Source Verification:* Official reporter citation (SCR/SCC/AIR) and paragraph reference.
  2. *Annotation Rubric:* Ratio accuracy, citation sufficiency, and procedural fidelity scored.
  3. *Written Substantive Rationale:* Minimum 2–3 sentences of authoritative reasoning supporting approval or rejection.

---

## 7. The Five-Stage Review Workflow & Audit Trail

All review actions are executed using the auditable CLI tool [`scripts/submit_human_review.py`](file:///d:/AI-Legal-Research-System/scripts/submit_human_review.py):

```
[ PENDING_HUMAN_LEGAL_REVIEW ]
             │
             ▼ (scripts/submit_human_review.py --claim)
       [ IN_REVIEW ]
             │
             ├─────────────────────────────────────────────────┐
             ▼ (scripts/submit_human_review.py --verify-source) │
    [ SOURCE_VERIFIED ]                                        │
             │                                                 │
             ▼ (scripts/submit_human_review.py --review-annotation)
   [ ANNOTATION_REVIEWED ]                                     │
             │                                                 │
             ├──────────────────────┬──────────────────────────┤
             ▼                      ▼                          ▼
       [ APPROVED ]           [ REJECTED ]          [ NEEDS_ADJUDICATION ]
    (Gold Label Approved)  (Substantively Flawed)  (Reviewer Disagreement)
                                                               │
                                                               ▼ (Senior Counsel Adjudication)
                                                  [ DISAGREEMENT_ADJUDICATED ]
                                                               │
                                                               ▼
                                                          [ APPROVED ]
```

Every transition records an immutable, append-only history entry capturing:
- Authenticated Reviewer ID, Name, and Bar Enrollment Number.
- High-precision UTC timestamp.
- Benchmark version (`3.0.0`) and item ID.
- Substantive legal rationale.

---

## 8. Dispute Escalation & Senior Adjudication

Where two reviewers disagree on a nuanced doctrinal proposition (e.g. prospective overruling effect or obiter vs ratio interpretation):
1. The item is escalated to `NEEDS_ADJUDICATION`.
2. A designated Senior Adjudicator (Senior Advocate / Retired Judicial Officer) reviews the contesting annotations.
3. The Senior Adjudicator records a binding adjudication rationale (`DISAGREEMENT_ADJUDICATED`).
4. **Anti-Self-Adjudication Invariant:** The software strictly forbids the original reviewer who raised the dispute from resolving their own escalation.

---

## 9. Confidentiality, Privacy & Data Handling

- **Public Judicial Data:** All benchmark items are derived exclusively from published Supreme Court of India judgments. No proprietary client briefs or non-public pleadings are included in the review catalog.
- **Reviewer Attribution:** Reviewers may opt for verified public attribution in technical reports or pseudonymous bar-verified identifiers (e.g. `adv_delhi_d1234`).
- **Telemetry Redaction:** The platform automatically masks research queries (`[REDACTED_BY_DEFAULT]`) and scrubs PII.

---

## 10. Acceptance & Engagement Form

To accept this review engagement, the candidate practitioner or institutional clinic director signs below:

```
AGREED AND ACCEPTED ON BEHALF OF PARTICIPATING ADVOCATE / INSTITUTION:

Practicing Advocate / Clinic Director Name: _____________________________________________
Bar Council Enrollment No. / Faculty ID:    _____________________________________________
Institution / Chambers Name:                _____________________________________________
Primary Practice Areas:                     _____________________________________________
Signature:                                  _____________________________________________
Date:                                       _____________________________________________
```

---

*This document is a formal proposal. Formal outreach and engagement will be documented upon signature.*

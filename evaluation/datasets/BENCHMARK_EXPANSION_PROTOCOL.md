# LEXORA Legal Intelligence Benchmark Expansion Protocol (v3.0 Planning)

## 1. Executive Summary & Objectives

The LEXORA Benchmark v2.0.0 currently encompasses **20 landmark legal passages and 61 evaluated queries** focused on Supreme Court of India constitutional and commercial jurisprudence. While highly informative for initial development, this corpus presents shared-authority clustering dependencies.

This protocol establishes the rigorous specification, schema, and human annotation procedure to expand the benchmark to **at least 150 verified research queries across 50+ authoritative legal passages** from multiple jurisdictions, authority tiers, and subject areas.

---

## 2. Target Corpus Expansion Scope

### 2.1 Subject Area Diversification
| Domain | Statutory Basis | Target Authorities | Primary Courts |
| :--- | :--- | :--- | :--- |
| **Constitutional & Human Rights** | Articles 14, 19, 21, 32 | *Puttaswamy*, *Kesavananda*, *Maneka Gandhi*, *Navtej Johar*, *Joseph Shine* | Supreme Court of India |
| **Commercial & Arbitration** | ICA 1872 (Sec 73, 74); A&C Act 1996 (Sec 34, 37) | *Kailash Nath*, *Saw Pipes*, *Associate Builders*, *Ssangyong*, *NN Global* | Supreme Court, Delhi HC, Bombay HC |
| **Corporate Insolvency & Bankruptcy** | IBC 2016 (Sec 7, 9, 14, 31, 53) | *Swiss Ribbons*, *Essar Steel*, *Vidarbha Industries*, *DBS Bank* | Supreme Court, NCLAT, NCLT |
| **Tax, GST & Administrative Law** | CGST Act 2017, Principles of Natural Justice | *Mohit Minerals* (Ocean Freight), *Union of India v. Bharti Airtel*, *Radha Krishan Industries* | Supreme Court, High Courts |

### 2.2 Authority Hierarchy & Jurisdictional Levels
- **Apex Court (Supreme Court of India)**: Constitution Benches (5/7/9 judges) vs Division Benches (2/3 judges).
- **Charter High Courts (Delhi & Bombay)**: Division bench and commercial division interpretations applying or distinguishing apex precedents.
- **Specialized Appellate Tribunals (NCLAT)**: Factual and statutory adjudications on corporate restructuring and moratorium applicability.

---

## 3. Query Taxonomy & Required Distribution (Target: 150+ Queries)

| Category Code | Description | Minimum Target Count | Key Challenges Evaluated |
| :--- | :--- | :---: | :--- |
| `STATUTORY_INTERPRETATION` | Plain meaning vs purposive construction of legislative text | 20 | Distinguishing statutory wording from judicial gloss |
| `HOLDING_VS_SUBMISSION` | Extracting binding ratio decidendi vs party arguments / obiter | 20 | Preventing attribution of counsel submissions to the bench |
| `MULTI_PASSAGE_SYNTHESIS` | Synthesizing principles across multiple judgments or sections | 25 | Combining evidence without dilution; rank exhaustion |
| `PRECEDENT_RELATIONSHIP` | Explicit judicial relationships: OVERRULES, FOLLOWS, DISTINGUISHES | 20 | Edge classification and directional evidence validation |
| `CONFLICT_AND_DISTINCTION` | Apparent tensions between precedents without express overruling | 15 | Nuanced legal tension assessment without false conflict |
| `TEMPORAL_PRECISION` | Chronological reasoning: exact years, approx dates, ranges, unknown | 15 | Temporal monotonicity and judgment date separation |
| `NEGATIVE_CONTROL_ABSTENTION` | Plausible but legally unsupported premises (fake cases/sections) | 15 | Refusal to hallucinate when evidence is absent |
| `OCR_NOISE_AND_INCOMPLETE` | Historical scans with character substitutions, typos, missing context | 10 | Robustness against document extraction degradation |
| `PROCEDURAL_FACTS` | Procedural histories, lower court decrees, maintainability | 10 | Discerning factual record from substantive holding |

---

## 4. Ground-Truth Data Schema

Every benchmark item in v3.0 must adhere to the following JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LexoraBenchmarkItemV3",
  "type": "object",
  "required": [
    "id",
    "question",
    "category",
    "subject_area",
    "court_level",
    "split",
    "relevant_chunk_ids",
    "expected_answer",
    "required_factual_points",
    "required_citations",
    "is_unanswerable",
    "annotation_metadata"
  ],
  "properties": {
    "id": { "type": "string" },
    "question": { "type": "string" },
    "category": { "type": "string" },
    "subject_area": { "type": "string" },
    "court_level": { "type": "string" },
    "split": { "type": "string", "enum": ["dev", "val", "test"] },
    "relevant_chunk_ids": {
      "type": "object",
      "additionalProperties": { "type": "integer", "minimum": 1, "maximum": 3 }
    },
    "expected_answer": { "type": "string" },
    "required_factual_points": {
      "type": "array",
      "items": { "type": "string" }
    },
    "required_citations": {
      "type": "array",
      "items": { "type": "string" }
    },
    "forbidden_claims": {
      "type": "array",
      "items": { "type": "string" }
    },
    "is_unanswerable": { "type": "boolean" },
    "expected_abstention_phrase": { "type": ["string", "null"] },
    "temporal_metadata": {
      "type": "object",
      "properties": {
        "event_date": { "type": "string" },
        "precision": { "type": "string", "enum": ["exact", "approximate", "range", "unknown"] }
      }
    },
    "ocr_noise_injected": { "type": "boolean" },
    "annotation_metadata": {
      "type": "object",
      "required": ["primary_annotator", "secondary_verifier", "adjudicator", "agreement_status"],
      "properties": {
        "primary_annotator": { "type": "string" },
        "secondary_verifier": { "type": "string" },
        "adjudicator": { "type": "string" },
        "agreement_status": { "type": "string", "enum": ["FULL_AGREEMENT", "ADJUDICATED", "FLAGGED"] },
        "provenance_notes": { "type": "string" }
      }
    }
  }
}
```

---

## 5. Dual-Annotator Verification & Adjudication Protocol

1. **Annotator Qualifications**:
   - Annotators must hold a recognized legal qualification (LL.B. / LL.M. / Bar enrollment) with training in Indian case law citations.
2. **Independent Dual Labeling**:
   - Annotator A independently drafts the question, identifies relevant chunk IDs, extracts required factual claims, and tags expected citations.
   - Annotator B reviews the item blind to Annotator A's required facts, independently identifying relevant chunk IDs and fact points.
3. **Inter-Annotator Agreement**:
   - Inter-annotator agreement on passage relevance is quantified using **Cohen's Kappa ($\kappa$)**.
   - Target acceptance threshold: $\kappa \ge 0.85$.
4. **Adjudication**:
   - Discrepancies where Annotators A and B disagree on relevance grades or ratio boundaries are referred to a Senior Legal Adjudicator.
   - Both original annotation records and the final resolution are permanently stored in the `annotation_metadata`.

---

## 6. Dataset Partition & Anti-Leakage Rules

- **Split Ratios**:
  - `dev` (Development & Debugging): 20% (~30 queries)
  - `val` (Validation & Hyperparameter Guard): 30% (~45 queries)
  - `test` (Held-Out Final Evaluation): 50% (~75 queries)
- **Anti-Leakage Safeguards**:
  - **Authority Segregation**: No single case judgment or specific statutory clause may span both `dev` and `test` splits.
  - **Cluster Isolation**: Questions sharing evidentiary passages must reside entirely within a single split to avoid pseudo-replication.

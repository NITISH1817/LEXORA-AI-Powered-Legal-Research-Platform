# ⚖️ LEXORA — AI-Powered Legal Intelligence & Research Platform

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-06B6D4.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Vite](https://img.shields.io/badge/Vite-8.2-646CFF.svg?logo=vite&logoColor=white)](https://vite.dev/)
[![Vitest](https://img.shields.io/badge/Vitest-5.0-FCC72B.svg?logo=vitest&logoColor=black)](https://vitest.dev/)
[![Tests](https://img.shields.io/badge/Tests-252%20Passed%20(206%20Backend%20+%2046%20Frontend)-brightgreen.svg)](https://pytest.org)
[![Lint](https://img.shields.io/badge/Oxlint-0%20Warnings%20%7C%200%20Errors-success.svg)](https://oxc.rs)
[![Security](https://img.shields.io/badge/Security-HMAC--SHA256%20%7C%20RBAC%20Enforced-blue.svg)](#-enterprise-security--adjudication-integrity)
[![Jurisprudence](https://img.shields.io/badge/Corpus-Supreme%20Court%20of%20India%20Landmarks-amber.svg)](#-benchmark-v300--empirical-evaluation)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **LEXORA** is an enterprise-grade, evidence-grounded legal research, judicial intelligence, and citation network platform designed for Indian constitutional and commercial jurisprudence. Engineered for advocates, judicial clerks, academic research centres, and legal technology infrastructures, LEXORA transforms complex legal precedents and voluminous court records into verifiable, cited intelligence with deterministic anti-hallucination guardrails.

---

## 📑 Table of Contents

- [Executive Overview](#-executive-overview)
- [Core Architectural Pillars](#-core-architectural-pillars)
- [System Architecture](#-system-architecture)
- [Benchmark v3.0.0 & Empirical Evaluation](#-benchmark-v300--empirical-evaluation)
- [Enterprise Security & Adjudication Integrity](#-enterprise-security--adjudication-integrity)
- [Document Intelligence & Ingestion Suite](#-document-intelligence--ingestion-suite)
- [Controlled Pilot Status & Release Gate Matrix](#-controlled-pilot-status--release-gate-matrix)
- [Repository Structure](#-repository-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup](#2-frontend-setup)
  - [Pre-Seeded Development Accounts](#3-pre-seeded-development-accounts)
  - [Containerized Deployment (Docker Compose)](#4-containerized-deployment-docker-compose)
- [Testing & Quality Assurance](#-testing--quality-assurance)
  - [Frontend Vitest Regression Suite (46 Tests)](#frontend-regression-testing-vitest--testing-library)
  - [Backend Pytest Regression Suite (206 Tests)](#backend-regression-testing-pytest)
  - [Static Analysis & Production Build](#static-analysis--production-build)
- [API Reference](#-api-reference)
- [Production Runbook & Disaster Recovery](#-production-runbook--disaster-recovery)
- [Mandatory Legal Non-Reliance Notice](#-mandatory-legal-non-reliance-notice)
- [License & Authorship](#-license--authorship)

---

## 🎯 Executive Overview

Modern legal informatics requires absolute fidelity to primary law. Standard Large Language Model (LLM) deployments suffer from severe vulnerabilities in legal environments:
- **Hallucinated Authorities:** Inventing non-existent Supreme Court citations, reporters, or benches.
- **Doctrinal Misattribution:** Conflating separate minority dissents with majority *ratio decidendi*.
- **Out-of-Scope Extrapolation:** Fabricating answers to unanswerable inquiries where no governing precedent exists.
- **Unverifiable Claims:** Generating unstructured advice without line-item provenance.

**LEXORA eliminates these vulnerabilities through a strict, multi-tiered evidence-grounded architecture:**

1. **Strict Source Grounding:** Every generated assertion is deterministically anchored to ingested source chunks with exact paragraph and page granularity (`[Source X - p. Y]`). Verbatim supporting quotes are surfaced in an interactive Source Evidence Inspector.
2. **Fail-Closed Negative Control Abstention:** When indexed jurisprudence lacks sufficient grounding to resolve an issue, the system explicitly abstains rather than inventing legal rules. Verified at **100% abstention accuracy (24/24 negative controls)** on Benchmark v3.0.0.
3. **Hybrid RRF + Cross-Encoder Retrieval:** Merges semantic embeddings with precise lexical token matches (BM25Okapi) via Reciprocal Rank Fusion ($k=60$), prioritizing exact statutory sections, reporter citations (`AIR`, `SCC`, `SCR`), and case titles.
4. **Role-Based Adjudication & Approved-Only Telemetry:** Distinguishes automated technical metrics from qualified legal validation. Zero reference labels can be approved automatically; only enrolled advocates with verified Bar Council credentials can approve gold labels.

---

## 🏛️ Core Architectural Pillars

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    LEXORA PLATFORM CORE                                         │
├───────────────────────────────┬─────────────────────────────────┬───────────────────────────────┤
│    🔍 RETRIEVAL & SYNTHESIS   │     📊 JUDICIAL INTELLIGENCE    │    🛡️ SECURITY & GOVERNANCE    │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ • Dense ChromaDB Embeddings   │ • Procedural History Separation │ • Role-Based Access Control   │
│ • Sparse BM25Okapi Lexical    │ • Fact Pattern Extraction       │ • HMAC-SHA256 Signatures      │
│ • Reciprocal Rank Fusion (60) │ • Issues & Ratio Decidendi      │ • Anti-Self-Adjudication Rule │
│ • Cross-Encoder Reranker      │ • Precedent Citation Graph      │ • Zero-Query Logging Default  │
│ • Fail-Closed Abstention      │ • Multi-Case Comparison (2-5)   │ • XSS-Sanitized SafeMarkdown  │
└───────────────────────────────┴─────────────────────────────────┴───────────────────────────────┘
```

### 1. Hybrid Reciprocal Rank Fusion (RRF) Retrieval
Legal queries exhibit dual retrieval requirements: conceptual semantics (e.g., *"proportionality standard in surveillance"*) and rigid statutory citations (e.g., *"Section 34(2A) Arbitration and Conciliation Act"*).
- **Dense Vector Search:** Leverages Google Gemini embeddings stored in ChromaDB to capture conceptual context and latent legal analogies.
- **Sparse BM25 Search:** Employs BM25Okapi token scoring to ensure exact match retention for court names, docket numbers, and statutory subsections.
- **Reciprocal Rank Fusion:** Combines scores via:
  $$RRF\_Score(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{k + rank_m(d)} \quad (k=60)$$
- **Cross-Encoder Scoring:** Re-scores the top-$K$ candidates through a cross-encoder model to assess semantic relevance before context assembly.

### 2. Structural Judicial Decomposition & Case Intelligence
LEXORA ingests raw rulings (PDF, DOCX, TXT) and decomposes multi-hundred-page judgments into structured doctrinal tiers:
- **Factual Background:** Material, non-controversial events preceding litigation.
- **Procedural Trajectory:** Trial court findings, appellate determinations, and reference orders.
- **Framed Legal Issues:** Core statutory questions and constitutional inquiries.
- **Judicial Reasoning:** Step-by-step statutory interpretation and precedent application.
- **Ratio Decidendi:** The binding legal proposition underpinning the holding.
- **Obiter Dicta:** Persuasive judicial commentary distinguished from binding holdings.
- **Final Disposition:** Operative orders, costs, remands, and bench split.

### 3. Chronological Procedural History Engine
Court opinions frequently interweave substantive historical events with procedural milestones. LEXORA's chronological timeline engine automatically normalizes relative and calendar dates into two parallel tracks:
- **Substantive Timeline:** Operative events giving rise to the cause of action (contracts executed, infringements, detentions).
- **Procedural Trajectory:** Courtroom milestones (petitions filed, interim stays, division bench references, constitution bench hearings).

### 4. Interactive Precedent Graph & Citation Network
Discovers and extracts citation relations using automated regex pattern analysis combined with LLM relation extraction.
- **Precedent Treatment Taxonomy:** Classifies incoming and outgoing relationships into `FOLLOWS`, `DISTINGUISHES`, `OVERRULES`, or `CITES`.
- **Dynamic Visualization:** Renders interactive, zoomable SVG networks mapping judicial lineages and highlighting doctrinal shifts.

### 5. Multi-Case Comparative Intelligence Matrix
Enables litigation teams and appellate researchers to compare **2 to 5 judgments side-by-side**:
- Aligns legal issues across disparate matters to identify consensus, divergence, and jurisdictional variations.
- Synthesizes comparative matrices highlighting statutory differences, factual distinctions, and conflicting holdings.

### 6. Stateful Research Workspace & Brief Synthesis
- **Session Continuity:** Organizes research questions, pinned cases, verbatim supporting passages, and analyst notes into stateful research dossiers.
- **Automated Research Briefs:** Compiles structured, publication-grade Markdown briefs formatted with executive summaries, procedural timelines, comparative matrices, and verified primary citations.

---

## 🏗️ System Architecture

```text
                                  ┌─────────────────────────────────────────┐
                                  │   React 19 + TypeScript + Tailwind v4   │
                                  │   Vite + Vitest + React Testing Library │
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       │ REST API / Bearer JWT / CORS
                                                       ▼
                                  ┌─────────────────────────────────────────┐
                                  │             FastAPI Backend             │
                                  │  (Auth, RBAC, Rate Limiting, Audit Log) │
                                  └────────────────────┬────────────────────┘
                                                       │
          ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
          ▼                                            ▼                                            ▼
┌───────────────────────────┐             ┌───────────────────────────┐             ┌───────────────────────────┐
│     Ingestion Pipeline    │             │   Hybrid Retrieval Engine │             │   Judicial Intelligence   │
├───────────────────────────┤             ├───────────────────────────┤             ├───────────────────────────┤
│ • 12-Stage Pipeline       │             │ • ChromaDB Vector Search  │             │ • Grounded RAG Synthesis  │
│ • PyMuPDF / DOCX Parsing  │             │ • BM25Okapi Lexical Match │             │ • Case Deconstruction     │
│ • OCR Verification Check  │             │ • Reciprocal Rank Fusion  │             │ • Procedural Timeline     │
│ • Semantic Chunking       │             │ • Cross-Encoder Reranker  │             │ • Precedent Graph (SVG)   │
│ • Citation Regex Parser   │             │ • Negative Abstention     │             │ • Multi-Case Comparison   │
└─────────────┬─────────────┘             └─────────────┬─────────────┘             └─────────────┬─────────────┘
              │                                         │                                         │
              ▼                                         ▼                                         ▼
┌───────────────────────────┐             ┌───────────────────────────┐             ┌───────────────────────────┐
│ SQLite / PostgreSQL DB    │             │ ChromaDB Vector Database  │             │ Google Gemini AI Studio   │
│ • Users & RBAC Roles      │             │ • Multi-Collection Store  │             │ • Flash / Pro 1.5 Grounded│
│ • Documents & Chunks      │             │ • Persistent Embeddings   │             │ • Zero-PII Prompt Windows │
│ • Review Packets & Signoff│             │ • Sub-second Query Index  │             │ • Deterministic Fallback  │
└───────────────────────────┘             └───────────────────────────┘             └───────────────────────────┘
```

---

## 📊 Benchmark v3.0.0 & Empirical Evaluation

LEXORA is governed by **Benchmark v3.0.0**, an empirical evaluation catalog compiled from landmark Constitution Bench and commercial rulings of the Supreme Court of India.

```
====================================================================================================
                        LEXORA BENCHMARK v3.0.0 EMPIRICAL PERFORMANCE
====================================================================================================
 Metric Dimension                        Measured Value     Target Threshold    Result
----------------------------------------------------------------------------------------------------
 Dev Split Retrieval Hit Rate (k=3)      98.44% (63/64)     ≥ 95.00%            PASSED [CI: 95.9–99.8%]
 Held-Out Retrieval Hit Rate (k=3)       100.00% (72/72)    ≥ 95.00%            PASSED [CI: 97.8–100%]
 Dev Recall@3 (Substantive Queries)      95.18%             ≥ 90.00%            PASSED
 Held-Out Recall@3                       95.25%             ≥ 90.00%            PASSED
 Grounded Atomic Claim Support (N=55)    82.70%             ≥ 80.00%            PASSED [CI: 78.8–87.2%]
 Citation-to-Claim Grounding Support     87.19%             ≥ 80.00%            PASSED [CI: 73.8–86.0%]
 Citation Validity Ratio                 100.00%            ≥ 95.00%            PASSED (100% valid)
 Negative Control Abstention Accuracy    100.00% (24/24)    ≥ 90.00%            PASSED [CI: 86.2–100%]
 Data Isolation & Tenant Security        15 / 15 Probes     100.00%             PASSED (0 leaks)
----------------------------------------------------------------------------------------------------
 Human Legal Reference Approvals         0 / 160 Approved   160 Approved        PENDING ADVOCATE REVIEW
 Verified Practitioner Feedback Records  0 Submissions      Cohort Feedback     EMPTY STATE (HONEST)
====================================================================================================
```

### Governing Evaluation Invariants
- **Cluster-Aware Bootstrap Confidence Intervals:** Reported confidence intervals are derived from 1,000 cluster-aware bootstrap iterations grouped by ruling topic, preventing artificial inflation from intra-case query clusters.
- **Fail-Closed Negative Control Suite:** 24 deceptive or unanswerable queries (e.g., fictitious citations, overturned minority tests, matters outside the corpus) are evaluated against an abstention gate; all 24 are cleanly declined without hallucinated holdings.
- **Approved-Only Metric Safeguard:** The platform strictly prohibits reporting automated, LLM-generated, or synthetic evaluation runs as "human legal approvals". All 160 queries remain formally classified as `PENDING_REVIEW` pending enrolled advocate adjudication.

---

## 🛡️ Enterprise Security & Adjudication Integrity

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ROLE-BASED ACCESS CONTROL (RBAC) MATRIX                         │
├──────────────────────┬─────────────┬──────────────┬───────────────────┬────────────────┤
│ Privilege Scope      │ ADMIN       │ SENIOR_ADJ   │ ADVOCATE_REVIEWER │ RESEARCHER     │
├──────────────────────┼─────────────┼──────────────┼───────────────────┼────────────────┤
│ Query & Synthesis    │ ✅ Full     │ ✅ Full      │ ✅ Full           │ ✅ Full        │
│ Document Ingestion   │ ✅ Full     │ ✅ Full      │ ✅ Full           │ ✅ Full        │
│ Session Dossiers     │ ✅ Full     │ ✅ Full      │ ✅ Full           │ ✅ Full        │
│ Submit Review Packet │ ❌ Anti-Self│ ❌ Anti-Self │ ✅ Authorized     │ ❌ Unauthorized│
│ Resolve Adjudication │ ❌ Forbidden│ ✅ Authorized│ ❌ Unauthorized   │ ❌ Unauthorized│
│ Admin Gates & Telemetry│ ✅ Full   │ ❌ Forbidden │ ❌ Forbidden      │ ❌ Forbidden   │
└──────────────────────┴─────────────┴──────────────┴───────────────────┴────────────────┘
```

1. **HMAC-SHA256 Signature Verification:** Every submitted review packet and adjudication decision is cryptographically signed using HMAC-SHA256 over reviewer credentials, bar enrollment numbers, timestamp, and review status. Tampered review records fail verification.
2. **Anti-Self-Adjudication Invariant:** System administrators and senior adjudicators are mathematically prevented from adjudicating packets they authored or submitted (`reviewer_id != adjudicator_id`).
3. **Privacy-Preserving Pilot Telemetry:**
   - Raw user queries are **not logged** by default (`log_queries=false`).
   - Telemetry tracks aggregated system statistics without retaining PII or confidential client propositions.
   - Users retain complete right-to-be-forgotten controls via `DELETE /api/evaluation/monitoring/my-events`.
4. **XSS-Sanitized SafeMarkdown Rendering:**
   - Custom, zero-vulnerability Markdown parsing engine built specifically for legal synthesis.
   - Untrusted LLM outputs or malicious user documents containing `<script>`, `<img>`, or `<svg>` tags are strictly treated as plain text strings and escaped. Zero executable script elements are mounted into the DOM.

---

## 📄 Document Intelligence & Ingestion Suite

LEXORA processes primary legal documents through an automated **12-stage ingestion pipeline**:

```
[Upload PDF/DOCX] ──▶ [Validating] ──▶ [Extracting] ──▶ [OCR Check] ──▶ [Parsing] ──▶ [Structuring]
                                                                                            │
[Ready & Indexed] ◀── [Analyzing] ◀── [Citations] ◀── [Indexing] ◀── [Embedding] ◀── [Chunking]
```

1. **`UPLOADED`**: Document received, hash computed, and size validated (< 50 MB default).
2. **`VALIDATING`**: MIME-type integrity and PDF header verification.
3. **`EXTRACTING`**: Text stream extraction via PyMuPDF (fitz) or python-docx.
4. **`OCR_CHECK`**: Character-density and page scanned-ratio analysis; routes to OCR if text layer is missing.
5. **`PARSING`**: Normalization of whitespace, footers, reporter watermarks, and line numbers.
6. **`STRUCTURING`**: Segmenting judgment into headnotes, facts, issues, and disposition.
7. **`CHUNKING`**: Semantic boundary chunking (500–800 tokens with 100-token contextual overlap).
8. **`EMBEDDING`**: Vectorization via Google Gemini dense embeddings.
9. **`INDEXING`**: ChromaDB collection upsert with metadata attributes.
10. **`CITATION_EXTRACT`**: Extraction of statutory sections and case reporters (`AIR`, `SCC`, `SCR`, `ILR`).
11. **`ANALYZING`**: Timeline extraction and precedent network classification.
12. **`READY`**: Fully indexed and searchable via the Research Workspace.

---

## 🚦 Controlled Pilot Status & Release Gate Matrix

In strict adherence to safety standards, LEXORA's live release status is classified as:

```
====================================================================================================
RELEASE STATUS: BLOCKED — OWNER ACTION REQUIRED
====================================================================================================
Technical readiness verified (252 passing tests, clean build, clean lint).
External institutional release gates remain blocked pending signed MoU/DPA and advocate adjudication.
====================================================================================================
```

### Eight-Gate Release Evaluation

| Release Gate | Verification Method | Status | Operational Requirement for Clearance |
| :--- | :--- | :---: | :--- |
| **Gate 1: Human Legal Adjudication** | Benchmark v3.0.0 Adjudication | **BLOCKED** | Qualified human advocates must review & approve 160 benchmark queries (currently `0/160`). |
| **Gate 2: Institutional MoU / DPA** | Formal Partnership Agreement | **BLOCKED** | Execution of Data Protection Agreement and institutional pilot agreement with host entity. |
| **Gate 3: Automated Retrieval Accuracy** | Hybrid RRF Benchmark | **PASSED** | Exceeds thresholds (98.44% Dev, 100% Held-Out hit rate). |
| **Gate 4: Grounded Claim & Citation Validity** | Verification Engine | **PASSED** | Exceeds thresholds (87.19% citation support, 100% citation validity, 100% abstention). |
| **Gate 5: Multi-Tenant & Data Isolation** | Adversarial Security Suite | **PASSED** | 15/15 automated security probes passed; zero data leakage detected. |
| **Gate 6: Production Build & Linting** | Static Analysis & Bundler | **PASSED** | 0 warnings, 0 errors in Oxlint; clean production Vite bundle. |
| **Gate 7: Frontend Regression Suite** | Vitest & React Testing Library | **PASSED** | 46/46 passing automated tests covering all core user workflows. |
| **Gate 8: Advocate Validation Signoff** | External Practitioner Audit | **BLOCKED** | External practicing advocates must submit formal evaluation signoffs (currently `0`). |

### The Eight Critical Review Dossiers (Benchmark Priority Queue)
Prepared dossiers awaiting independent human advocate review in `evaluation/`:
1. **`dossier_01_puttaswamy_9j_privacy`**: *Justice K.S. Puttaswamy (Retd.) v. Union of India* (2017) 10 SCC 1 — Nine-judge bench, Article 21 privacy fundamental right, 4-tier proportionality doctrine.
2. **`dossier_02_shayara_bano_triple_talaq`**: *Shayara Bano v. Union of India* (2017) 9 SCC 1 — Article 14 manifest arbitrariness test striking down Talaq-e-Biddat.
3. **`dossier_03_navtej_johar_sec_377`**: *Navtej Singh Johar v. Union of India* (2018) 10 SCC 1 — Constitutional morality, indirect discrimination, reading down IPC Section 377.
4. **`dossier_04_anuradha_bhasin_internet_speech`**: *Anuradha Bhasin v. Union of India* (2020) 3 SCC 637 — Freedom of speech over internet under Article 19(1)(a), proportionality of indefinite telecommunications suspension orders.
5. **`dossier_05_maneka_gandhi_procedure_established`**: *Maneka Gandhi v. Union of India* (1978) 1 SCC 248 — Inter-relationship between Articles 14, 19, and 21; procedural due process; just, fair, and reasonable procedure standard.
6. **`dossier_06_minerva_mills_basic_structure`**: *Minerva Mills Ltd. v. Union of India* (1980) 3 SCC 625 — Harmonious balance between Fundamental Rights and Directive Principles; basic structure limits on amending power.
7. **`dossier_07_kesavananda_bharati_landmark`**: *Kesavananda Bharati v. State of Kerala* (1973) 4 SCC 225 — Thirteen-judge landmark bench; Basic Structure Doctrine limits on Article 368 constituent power.
8. **`dossier_08_indra_sawhney_creamy_layer`**: *Indra Sawhney v. Union of India* (1992) Supp (3) SCC 217 — Nine-judge bench; 50% reservation ceiling; backward class identification; creamy layer exclusion doctrine.

### Staged Sequential Outreach Channels
- **Track A (Academic Research Collaboration):** Tamil Nadu National Law University (TNNLU), Tiruchirappalli (`adminoffice@tnnlu.ac.in`). Formulated in [`evaluation/PHASE24_OUTREACH_DRAFTS.md`](file:///d:/AI-Legal-Research-System/evaluation/PHASE24_OUTREACH_DRAFTS.md) for supervised academic evaluation of source attribution and ratio decidendi extraction.
- **Track B (Commercial Practitioner Review):** Surana & Surana International Attorneys, Chennai (`chennai@lawindia.com`). Formulated for commercial litigation review (Section 34(2A) patent illegality, Section 11 arbitration agreement stamping under *In Re Interplay*, IBC Section 53 distribution waterfall).

---

## 📁 Repository Structure

```
AI-Legal-Research-System/
├── backend/                               # FastAPI Backend Application
│   ├── models/                            # SQLAlchemy ORM Data Models
│   │   ├── audit.py                       # User action & access audit logging
│   │   ├── case.py                        # Judgments, sections, chunks, citations
│   │   ├── domain.py                      # User entities, roles & sessions
│   │   └── research.py                    # Workspaces, evidence pins & notes
│   ├── routes/                            # API Endpoint Controllers
│   │   ├── api.py                         # Health & system discovery
│   │   ├── auth.py                        # JWT login, registration & profile
│   │   ├── cases.py                       # Case profile, timeline & citations
│   │   ├── compare.py                     # Multi-case comparative matrix
│   │   ├── documents.py                   # Document upload, extraction & reader
│   │   ├── evaluation.py                  # Telemetry, gates & pilot feedback
│   │   └── research.py                    # RAG queries, sessions & brief compiler
│   ├── schemas/                           # Pydantic v2 Request/Response Validation
│   ├── services/                          # Core Domain Logic Engines
│   │   ├── auth_service.py                # Password hashing, JWT issuance & RBAC
│   │   ├── bm25_service.py                # BM25Okapi sparse lexical scoring
│   │   ├── citation_service.py            # Regex extractor for AIR, SCC, SCR reporters
│   │   ├── compare_service.py             # Multi-case cross-judgment alignment
│   │   ├── document_service.py            # 12-stage ingestion pipeline
│   │   ├── embedding_service.py           # Gemini dense vector embedding pipeline
│   │   ├── intelligence_service.py        # Judicial decomposition (ratios, facts)
│   │   ├── monitoring_service.py          # Privacy-preserving pilot telemetry
│   │   ├── precedent_service.py           # Dynamic SVG citation graph builder
│   │   ├── rag_service.py                 # Grounded synthesis & abstention engine
│   │   ├── search_service.py              # Hybrid RRF (k=60) + Cross-Encoder
│   │   └── timeline_service.py            # Substantive vs procedural history engine
│   ├── tests/                             # 206 Automated Backend Regression Tests
│   ├── app.py                             # FastAPI Application Factory & Middleware
│   ├── config.py                          # Pydantic Settings & Environment Parsing
│   ├── database.py                        # SQLAlchemy Engine & Session Pool
│   └── security.py                        # Cryptographic Utilities & JWT Handlers
├── frontend/                              # Modern React 19 + TypeScript Application
│   ├── src/
│   │   ├── __tests__/                     # 46 Automated Frontend Regression Tests
│   │   │   ├── auth.test.tsx              # Auth forms, tokens, route guards, 403/401
│   │   │   ├── documentIntelligence.test.tsx # Catalog, pipeline status, search filters
│   │   │   ├── evaluationDashboard.test.tsx  # Invariant checks (0/160 approved, empty FB)
│   │   │   ├── navigationAndCommon.test.tsx  # 404 route, AppNavbar roles, dialog focus
│   │   │   ├── researchWorkspace.test.tsx # Query submission, citations, evidence drawer
│   │   │   └── safeMarkdown.test.tsx      # XSS sanitization, script escaping, tables
│   │   ├── api/                           # Axios Client, Auth Interceptor & Errors
│   │   ├── components/                    # UI Components
│   │   │   ├── auth/                      # Login.tsx, Register.tsx
│   │   │   ├── common/                    # AppNavbar.tsx, NotFound.tsx, SafeMarkdown.tsx
│   │   │   ├── ui/                        # Button, Input, Modal, ConfirmDialog, Badge, etc.
│   │   │   ├── CaseIntelligence.tsx       # Judicial analysis & ratio decidendi viewer
│   │   │   ├── CaseTimeline.tsx           # Procedural trajectory timeline
│   │   │   ├── ComparativeIntelligence.tsx# Side-by-side multi-case comparison matrix
│   │   │   ├── DocumentDetail.tsx         # Document metadata, chunks & reader
│   │   │   ├── DocumentIntelligence.tsx   # Catalog management & ingestion dashboard
│   │   │   ├── DocumentSourceViewer.tsx   # Primary grounded source inspector
│   │   │   ├── EvaluationDashboard.tsx    # Release gates & telemetry console
│   │   │   ├── PrecedentGraph.tsx         # Interactive citation network visualization
│   │   │   └── ResearchWorkspace.tsx      # Central RAG workbench & dossier compiler
│   │   ├── context/                       # AuthContext, ToastContext & Type Contracts
│   │   ├── hooks/                         # useAuth, useToast custom hooks
│   │   ├── test/                          # setup.ts (browser polyfills & DOM cleanups)
│   │   ├── App.tsx                        # Root Router & ProtectedRoute Guard
│   │   └── main.tsx                       # React DOM Bootstrapper
│   ├── package.json                       # Dependencies & Repeatable Test Scripts
│   ├── vite.config.ts                     # Vite 8.2 Production Build Configuration
│   └── vitest.config.ts                   # Vitest 5.0 Testing Configuration (jsdom)
├── evaluation/                            # Benchmark Datasets & Human Adjudication Suite
│   ├── datasets/                          # Legal Benchmark v3.0.0 (52 passages, 160 queries)
│   ├── results/                           # Audit logs, telemetry summaries & gate reports
│   ├── evaluator.py                       # Automated benchmark evaluation runner
│   ├── metrics.py                         # HitRate, Recall@K, Grounding CI calculation
│   ├── regression_gate.py                 # Automated CI release gate verification
│   ├── review_workflow.py                 # Reviewer authorization & HMAC signature engine
│   ├── PHASE24_OUTREACH_DRAFTS.md         # Staged institutional outreach messages (TNNLU & Surana)
│   ├── PHASE24_OWNER_APPROVAL_CHECKLIST.md# 7-item owner authorization checklist
│   ├── PHASE25_FRONTEND_REGRESSION_TEST_PLAN.md # Comprehensive test specifications
│   └── PHASE25_REPORT.md                  # Phase 25 Master Engineering Report
├── scripts/                               # Operational & Disaster Recovery Tooling
│   ├── backup.py                          # Full-state database & storage backup utility
│   ├── restore.py                         # Point-in-time database restoration engine
│   └── analyze_pilot_feedback.py          # Privacy-preserving feedback aggregator
├── docker-compose.yml                     # Multi-container orchestration (app, web, chroma)
├── DEPLOYMENT_RUNBOOK.md                  # Comprehensive production operational manual
├── pytest.ini                             # Pytest backend configuration
└── README.md                              # Master System Documentation
```

---

## ⚡ Getting Started

### Prerequisites
- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: 20.x or higher (`npm` included)
- **Git**: Installed and configured
- **Google Gemini API Key**: [Obtain from Google AI Studio](https://aistudio.google.com/)

---

### 1. Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/NITISH1817/LEXORA-AI-Powered-Legal-Research-Platform.git
cd LEXORA-AI-Powered-Legal-Research-Platform

# 2. Create and activate a Python virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment variables
# Copy sample configuration to backend/.env
cp .env.production.example backend/.env

# Open backend/.env in your editor and configure:
# GEMINI_API_KEY=your_actual_gemini_api_key
# SECRET_KEY=your_cryptographically_secure_random_32_byte_string

# 5. Start the FastAPI application server
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

- Interactive OpenAPI Swagger documentation: `http://127.0.0.1:8000/docs`
- Service Health Endpoint: `http://127.0.0.1:8000/api/health`

---

### 2. Frontend Setup

```bash
# 1. Open a new terminal in the repository root and enter frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

- Access the web application: `http://localhost:5173`
- Vite dev server automatically proxies `/api` and `/health` requests to `http://127.0.0.1:8000`.

---

### 3. Pre-Seeded Development Accounts

The development database (`legal_intel.db`) contains pre-seeded accounts configured for testing:

| Role | Email | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@lexora.ai` | `Password123!` | Full access to Evaluation Console, Release Gates, and System Telemetry |
| **Senior Researcher** | `researcher@lexora.ai` | `Password123!` | Research Workspace, Document Ingestion, Case Analytics, and Briefs |
| **Pilot Registration Code** | `LEXORA-PILOT-2026-SUPERVISED` | *(During Sign-Up)* | Required invitation code to register new pilot accounts |

---

### 4. Containerized Deployment (Docker Compose)

To spin up the entire production stack (FastAPI backend, React frontend with Nginx, and ChromaDB vector store) in isolated containers:

```bash
# Export mandatory environment variables
export GEMINI_API_KEY="your_api_key_here"
export SECRET_KEY="your_random_32_byte_hex_string"

# Launch stack in detached mode
docker-compose up --build -d

# Check running services
docker-compose ps
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **ChromaDB Vector Store**: Internal network on port `8000`

---

## 🔬 Testing & Quality Assurance

LEXORA enforces rigorous automated quality verification: **252 total passing automated tests** (206 backend + 46 frontend).

```
====================================================================================================
                              AUTOMATED QUALITY ASSURANCE SUMMARY
====================================================================================================
 Suite Category             Tool / Runner       Tests    Pass Rate    Duration    Exit Code
----------------------------------------------------------------------------------------------------
 Frontend Regression Suite  Vitest + jsdom      46       100.0%       3.28s       0 (Clean)
 Frontend Static Analysis   Oxlint (116 rules)  45 files 100.0%       199ms       0 (0 warn / 0 err)
 Frontend Production Build  tsc -b && vite      2,340 mod 100.0%      1.57s       0 (Clean bundle)
 Backend Regression Suite   Pytest 8.4          206      100.0%       109.80s     0 (Clean)
====================================================================================================
 TOTAL PLATFORM TESTS       Vitest + Pytest     252      100.0%       114.65s     0 (PASSED)
====================================================================================================
```

### Frontend Regression Testing (Vitest + Testing Library)

```bash
# Run complete frontend regression suite
npm --prefix frontend test

# Run tests with interactive watch mode
npm --prefix frontend run test -- --watch

# Run a specific test suite
npm --prefix frontend test -- src/__tests__/auth.test.tsx
```

#### Covered Workflows (46 Tests):
- **`src/__tests__/auth.test.tsx` (10 tests):** Accessible form controls, email/password validation, token persistence, non-admin 403 Forbidden screen, unauthenticated route redirection, session cleanup on logout, and global 401 interception.
- **`src/__tests__/safeMarkdown.test.tsx` (9 tests):** Complete XSS prevention, inert plain-text rendering for injected `<script>`, `<img>`, and `<svg>` tags, semantic headings (`h1`–`h4`), blockquotes, code blocks, tables, and clickable citation pills.
- **`src/__tests__/evaluationDashboard.test.tsx` (5 tests):** Evaluation integrity invariants, reporting `0 / 160` approved gold labels, honest empty state for practitioner feedback (`0 Submissions`), pilot restriction banner, persistent non-reliance disclaimer, and API failure handling.
- **`src/__tests__/documentIntelligence.test.tsx` (6 tests):** Document catalog rendering, pipeline status badges (`Ready`, `Parsing`, `Failed`), empty catalog state, client-side search filtering, processing status filtering, filter reset, and error alerts.
- **`src/__tests__/researchWorkspace.test.tsx` (5 tests):** Query execution, Ctrl+Enter keyboard submission, RAG synthesis answer display, interactive citation pills, Source Evidence Inspector modal drawer, persistent legal disclaimer, and 503 error handling.
- **`src/__tests__/navigationAndCommon.test.tsx` (11 tests):** 404 unindexed route catch-all view, role-based AppNavbar navigation links, `Modal` accessibility (`role="dialog"`, `aria-modal="true"`, `Escape` dismissal), `ConfirmDialog` interactions, and `getErrorMessage` error extraction.

### Backend Regression Testing (Pytest)

```bash
# Run complete backend test suite (206 tests)
pytest backend/tests/ -q

# Run with verbose test-by-test output
pytest backend/tests/ -v

# Run with test coverage analysis
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

#### Covered Test Categories:
- **Phase 3**: Request contracts, Pydantic schemas, and input validation
- **Phase 4**: Ingestion engine, semantic chunking, and file validation
- **Phase 5**: Evidence-grounded RAG, source attribution, and fail-closed abstention
- **Phase 6**: Multi-case comparative analytics and precedent graph builder
- **Phase 7**: Procedural and substantive timeline engine
- **Phase 8**: Security hardening, JWT authentication, RBAC, and audit logging
- **Phase 9–13**: Benchmark v3.0.0, automated evaluation, and release gates
- **Phase 14–16**: Adjudication workflows, human review gates, and pilot acceptance
- **Phase 17**: Reviewer authorization, HMAC signatures, and anti-self-adjudication

### Static Analysis & Production Build

```bash
# Execute Oxlint static analysis on frontend
npm --prefix frontend run lint
# Result: Found 0 warnings and 0 errors across 45 files with 116 rules.

# Validate production bundle compilation
npm --prefix frontend run build
# Result: tsc -b && vite build succeeds; generates dist/ bundle in 1.57s.
```

---

## 📡 API Reference

| Module | Method | Endpoint | Description | Minimum Role |
| :--- | :---: | :--- | :--- | :---: |
| **Auth** | `POST` | `/api/auth/register` | Register new user account with invitation code | Public |
| **Auth** | `POST` | `/api/auth/login` | Authenticate & retrieve JWT bearer token | Public |
| **Auth** | `GET` | `/api/auth/me` | Fetch authenticated user profile & role | `RESEARCHER` |
| **Research** | `POST` | `/api/research/ask` | Execute grounded legal RAG synthesis | `RESEARCHER` |
| **Research** | `POST` | `/api/search` | Raw hybrid (Dense + BM25) passage retrieval | `RESEARCHER` |
| **Research** | `GET` | `/api/research` | List user's active research workspace dossiers | `RESEARCHER` |
| **Research** | `POST` | `/api/research` | Create new research workspace session | `RESEARCHER` |
| **Research** | `DELETE`| `/api/research/{id}` | Delete research workspace dossier | `RESEARCHER` |
| **Research** | `POST` | `/api/research/{id}/cases` | Pin case authority to research session | `RESEARCHER` |
| **Research** | `POST` | `/api/research/{id}/evidence` | Pin verbatim passage evidence to session | `RESEARCHER` |
| **Research** | `POST` | `/api/research/{id}/notes` | Attach analyst note to session | `RESEARCHER` |
| **Research** | `POST` | `/api/research/{id}/brief` | Synthesize markdown research brief | `RESEARCHER` |
| **Documents**| `POST` | `/api/documents/upload` | Ingest PDF/DOCX judgment with pipeline status | `RESEARCHER` |
| **Documents**| `GET` | `/api/documents` | List uploaded documents with ingestion stages | `RESEARCHER` |
| **Documents**| `GET` | `/api/documents/{id}` | Fetch document details and semantic chunks | `RESEARCHER` |
| **Documents**| `GET` | `/api/documents/{id}/source` | Fetch verbatim source document reader view | `RESEARCHER` |
| **Documents**| `DELETE`| `/api/documents/{id}` | Delete document and cascade chunks/vectors | `RESEARCHER` |
| **Cases** | `GET` | `/api/cases/{id}` | Fetch case profile, ratio, facts, and issues | `RESEARCHER` |
| **Cases** | `GET` | `/api/cases/{id}/timeline` | Fetch chronological procedural timeline | `RESEARCHER` |
| **Cases** | `GET` | `/api/cases/{id}/precedents`| Fetch precedent citation graph data | `RESEARCHER` |
| **Compare** | `POST` | `/api/compare` | Multi-case comparison matrix (2 to 5 cases) | `RESEARCHER` |
| **Evaluation**| `GET` | `/api/evaluation/latest` | Complete evaluation results JSON | `ADMIN` |
| **Evaluation**| `GET` | `/api/evaluation/reconciled`| Reconciled benchmark metrics & CI | `RESEARCHER` |
| **Evaluation**| `GET` | `/api/evaluation/monitoring/summary` | Aggregated pilot telemetry & feedback stats | `ADMIN` |
| **Evaluation**| `POST`| `/api/evaluation/monitoring/feedback` | Submit practitioner adjudication review | `RESEARCHER` |
| **Evaluation**| `GET` | `/api/evaluation/monitoring/my-events` | Fetch caller's audit events (isolation) | `RESEARCHER` |
| **Evaluation**| `DELETE`| `/api/evaluation/monitoring/my-events` | Purge caller's telemetry (right to be forgotten) | `RESEARCHER` |
| **System** | `GET` | `/api/health` | Service health, SQLite, and ChromaDB status | Public |

---

## 🚢 Production Runbook & Disaster Recovery

For complete operational, disaster recovery, and failover runbooks, consult [`DEPLOYMENT_RUNBOOK.md`](file:///d:/AI-Legal-Research-System/DEPLOYMENT_RUNBOOK.md).

### Automated Backup & Restoration
LEXORA includes standalone scripts for point-in-time state preservation:

```bash
# 1. Create a full cryptographic backup (database + storage + chroma)
python scripts/backup.py

# Backups are created in backups/ with SHA256 checksums:
# backups/lexora_backup_YYYYMMDD_HHMMSS.tar.gz
# backups/lexora_backup_YYYYMMDD_HHMMSS.tar.gz.sha256

# 2. Restore state from an archive with automatic checksum verification
python scripts/restore.py backups/lexora_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Production Checklist
1. **Secrets:** Generate a 64-character random hex string for `SECRET_KEY`; never commit production credentials.
2. **Database:** Migrate from SQLite to PostgreSQL (`postgresql+psycopg2://user:pass@host:5432/lexora`) for high concurrency.
3. **CORS:** Restrict `CORS_ORIGINS` to authorized production domains.
4. **SSL/TLS:** Terminate TLS using Nginx or Cloudflare; set secure cookies and HTTP Strict Transport Security (HSTS).
5. **Worker Scaling:** Run Uvicorn behind Gunicorn (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app:app`).

---

## ⚖️ Mandatory Legal Non-Reliance Notice

> **IMPORTANT LEGAL SAFEGUARD:**  
> **LEXORA provides AI-assisted legal research synthesis, not legal advice.**  
> In accordance with Indian Bar Council regulations and professional liability standards, all generated summaries, statutory analyses, and precedent citations must be independently verified against authoritative primary legal reporters (**Supreme Court Reports [SCR]**, **Supreme Court Cases [SCC]**, **All India Reporter [AIR]**) by a qualified advocate enrolled with a State Bar Council before consequential reliance in pleadings, client advisories, or judicial submissions.

---

## 📜 License & Authorship

Distributed under the **MIT License**. See `LICENSE` for more information.

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Repository:** [https://github.com/NITISH1817/LEXORA-AI-Powered-Legal-Research-Platform](https://github.com/NITISH1817/LEXORA-AI-Powered-Legal-Research-Platform)  
**Engineering Invariant:** Rigorous Evidence-Grounding, Deterministic Abstention, and Adjudication Integrity.
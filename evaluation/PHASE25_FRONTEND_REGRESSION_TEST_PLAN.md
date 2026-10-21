# LEXORA — Phase 25: Frontend Regression Test Plan & Workflow Reliability Specification

**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Repository:** `LEXORA-AI-Powered-Legal-Research-Platform`  
**Workspace:** `D:\AI-Legal-Research-System`  
**Date:** 2026-10-21  
**Phase:** Phase 25 — Frontend Regression Testing & Workflow Reliability  
**Governing Benchmark:** Benchmark v3.0.0 (52 landmark passages, 160 queries)  
**Release Gate Status:** `BLOCKED — OWNER ACTION REQUIRED` (Gates 1, 2, 8 remain blocked awaiting external advocate adjudication & institutional MoU)

---

## 1. Overview & Objectives

Phase 25 establishes a robust, repeatable, deterministic automated frontend regression testing suite for LEXORA's React 19 application. Building upon the verified Phase 17 frontend modernization (which established clean builds and 0 lint warnings) and the sequential outreach preparation of Phase 24, Phase 25 introduces lightweight, developer-friendly Vitest and React Testing Library suites to prevent UI regressions, enforce security invariants, verify accessibility baselines, and guarantee evaluation integrity without relying on external dependencies or heavy browser automation.

### Primary Testing Objectives
1. **Deterministic Execution:** Tests run entirely in-process using `jsdom` without requiring live external legal databases, external AI providers, or browser binaries.
2. **Security & Access Control Enforcement:** Verify that protected routes redirect unauthenticated callers, administrative consoles (`/evaluation`) strictly block unauthorized researchers with accessible 403 Forbidden advisories, and malicious scripts or HTML cannot execute via legal markdown synthesis.
3. **Evaluation Integrity Safeguards:** Verify that zero approved human legal gold labels (`0 / 160`) and zero genuine external practitioner feedback records are faithfully presented in the UI without hallucinated metrics, synthetic data leakage, or unverified claims.
4. **Accessibility Fundamentals:** Verify accessible labels, keyboard navigation (Ctrl+Enter submission, Escape modal closure), dialog roles (`role="dialog"`, `aria-modal="true"`), and distinguishable error alerts (`role="alert"`).
5. **Repeatability:** Standardize commands via `npm --prefix frontend test` and document exact execution instructions.

---

## 2. Test Architecture & Technology Stack

| Component | Choice | Rationale |
| :--- | :--- | :--- |
| **Test Runner** | Vitest v5.0.5 | Native ESM & Vite integration, fast in-memory execution, zero configuration drift from Vite build |
| **DOM Environment** | jsdom v29.1.1 | Standard W3C DOM implementation in pure JS; fast, isolated, no binary browser requirements |
| **Component Testing** | `@testing-library/react` v16.3.3 | Tests behavior from the user/advocate perspective using accessible roles and text |
| **DOM Matchers** | `@testing-library/jest-dom` v7.0.1 | Rich semantic assertions (`toBeInTheDocument`, `toBeDisabled`, `toHaveAttribute`) |
| **Configuration** | `frontend/vitest.config.ts` | Dedicated test config isolated from dev/production build settings |
| **Environment Setup** | `frontend/src/test/setup.ts` | Browser polyfills (`matchMedia`, `ResizeObserver`, `scrollTo`) and automatic state cleanup |

---

## 3. High-Value Regression Test Suites & Workflows

### Suite A: Authentication & Route Protection (`frontend/src/__tests__/auth.test.tsx`)
- **Login Form Accessibility & Validation:**
  - Semantic labels for institutional email and password (`placeholder="••••••••"`, `id="login-password"`).
  - Client-side validation: Submitting empty form prevents API call and renders accessible error alert (`role="alert"`).
  - Password visibility toggle with dynamic accessible aria-labels (`Show password` / `Hide password`).
- **Authentication Flows & Error Handling:**
  - Failed authentication displays exact backend error message within an accessible `role="alert"` container.
  - Successful authentication stores JWT in `localStorage` (`token` and `access_token`) and updates authentication state.
- **Route Guard Invariants:**
  - Unauthenticated access to `/protected` triggers immediate redirect to `/login`.
  - Non-admin user (`role: 'RESEARCHER'`) attempting to access `adminOnly` route receives explicit 403 Forbidden screen (`403 Forbidden: Administrator Role Required`).
  - Verified institutional administrator (`role: 'ADMIN'`) is granted access to administrative release gate console.
- **Session Lifecycle & Global 401 Interception:**
  - User logout cleanly purges tokens and Authorization headers.
  - Interceptor custom event `lexora:unauthorized` immediately invalidates active user context and resets session.

### Suite B: SafeMarkdown & Untrusted Content Sanitization (`frontend/src/__tests__/safeMarkdown.test.tsx`)
- **XSS & Injection Vector Defense:**
  - Malicious `<script>` tags in legal summaries are rendered as inert text nodes; no executable `<script>` tag is created in DOM.
  - Malicious `<img onerror=...>` and `<svg onload=...>` injection payloads do not execute event handlers or mount active elements.
- **Legal Document Formatting:**
  - Semantic heading hierarchy (`h1`, `h2`, `h3`, `h4`) for case ratios and holdings.
  - Bulleted and numbered lists for legal criteria and procedural steps.
  - Semantic `<blockquote>` rendering for judicial quotations and verbatim statutes.
  - Fenced code blocks (`<pre><code>`) and inline code (`` `code` ``) for statutory sections.
  - Structured markdown table rendering (`<table>`, `<th>`, `<td>`) for precedent comparative matrices.
- **Interactive Citation Pills:**
  - Bracketed citations (`[AIR 2017 SC 4401]`) parsed into interactive buttons triggering `onCitationClick` callback.
  - Graceful handling of empty or null strings.

### Suite C: Research Workspace & Synthesis Interactions (`frontend/src/__tests__/researchWorkspace.test.tsx`)
- **Query Submission & Synthesis Output:**
  - Form submission via button click or `Ctrl+Enter` keyboard shortcut.
  - Rendering of structured legal synthesis answer, key findings, and ratio decidendi.
  - Interactive citation buttons within synthesis text.
- **Evidence Inspector Drawer:**
  - Clicking "Inspect" on an indexed supporting passage opens the Source Evidence Inspector modal.
  - Displays primary text extract, reporter citation, court, and verified case holding.
- **Safety & Scoping:**
  - Persistent, prominent legal non-reliance disclaimer: *"Controlled Pilot Safeguards & Mandatory Verification Standard: Non-Reliance Notice: LEXORA provides AI-assisted legal research synthesis, not legal advice."*
  - Corpus scope limitation banner explicitly declaring indexed landmark Supreme Court constitutional bounds.
  - Accessible error alert (`role="alert"`) on backend RAG retrieval failure (503 Service Unavailable).

### Suite D: Evaluation Integrity & Release Safeguards (`frontend/src/__tests__/evaluationDashboard.test.tsx`)
- **Approved-Only Invariant Enforcement:**
  - Faithfully reports zero approved gold labels (`0 / 160`) and 160 pending human legal reviews.
  - Explicit advisory: *"Strict invariant: zero automated approvals permitted. Only verified advocates with Bar Council enrollment may approve gold labels."*
- **Practitioner Feedback Empty-State Honesty:**
  - Faithfully reports 0 submissions (`Zero External Records`) from monitoring summary telemetry.
  - Advisory: *"No external practitioner survey responses have been submitted to date. Synthetic test data is excluded from reporting."*
- **Operational Decision Banner:**
  - Renders *"Operational Decision: LIMITED CONTROLLED PILOT — CONTINUE WITH CONDITIONS"*.
  - Displays `PILOT_REGISTRATION_RESTRICTED = True` notice.
- **Resilience:**
  - Distinguishes API connection errors from valid metrics, maintaining the zero-approval invariant even during backend telemetry failure.

### Suite E: Document Intelligence & Ingestion Suite (`frontend/src/__tests__/documentIntelligence.test.tsx`)
- **Catalog Management & Empty States:**
  - Renders document table, pipeline status badges (`Ready`, `Parsing`, `Failed`), and summary cards (`Total Ingested`, `Ready & Indexed`, `In Pipeline`, `Failed Processing`).
  - Empty catalog state: Displays *"No documents in catalog"* and *"Upload your first primary transcript, ruling, or pleading to begin extraction."*
- **Search & Pipeline Filtering:**
  - Dynamic live client-side search filtering by document title, case name, or original filename.
  - Status filter dropdown (`ALL`, `READY`, `PROCESSING`, `FAILED`).
  - Zero-match state with *"Clear Filters"* action button that restores the full catalog.
- **Error Feedback:**
  - Renders accessible `role="alert"` banner when document catalog endpoint fails.

### Suite F: Navigation, 404 Routes & Accessibility (`frontend/src/__tests__/navigationAndCommon.test.tsx`)
- **404 Catch-All Routing:**
  - Renders semantic `Error 404 • Unindexed Route` badge and *"Authority or Resource Not Found"* heading.
  - Navigates cleanly back to Research Workspace (`/`) or Document Catalog (`/documents`).
- **Navigation Bar Role Enforcement:**
  - Standard researcher view displays links to `/research` and `/documents`, while omitting the admin `/evaluation` console.
  - Displays persistent `Pilot` badge and branding.
- **Modal & Dialog Accessibility:**
  - Semantic dialog markup (`role="dialog"`, `aria-modal="true"`).
  - Keyboard `Escape` key listeners for modal dismissal.
  - `ConfirmDialog` confirm/cancel interactions and disabled loading states.
- **Error Handling Utility (`getErrorMessage`):**
  - Extracts FastAPI string details, structured array validation errors, and custom default messages.

---

## 4. Test Fixture Strategy & Boundary Rules

1. **Isolation from External Systems:**
   - Network requests are intercepted at the Axios boundary (`vi.mock('../api/client')`).
   - No HTTP requests leave the test runner.
   - Zero live emails, outreach messages, or bar council lookups are dispatched.
2. **Realistic Controlled Fixtures:**
   - Fixtures represent authentic Indian Supreme Court authorities (Puttaswamy, Navtej Johar) and official reporter formats (AIR, SCC, SCR).
   - Invariant fixture records strictly reflect 0 approved gold labels and 0 practitioner feedback submissions.
3. **No Fabricated Production Records:**
   - Test data is strictly labeled as controlled test fixtures in memory.

---

## 5. Verification Commands

| Command | Purpose | Expected Output |
| :--- | :--- | :--- |
| `npm --prefix frontend test` | Run complete frontend regression suite | 6 test files, 46 tests passing |
| `npm --prefix frontend run lint` | Oxlint static analysis | 0 warnings, 0 errors |
| `npm --prefix frontend run build` | TypeScript compile & Vite production build | Exit code 0, dist bundle generated |
| `.\venv\Scripts\pytest.exe backend/tests/ -q` | Backend regression suite | 206 tests passing |

---

## 6. Known Limitations & Technical Roadmap

1. **Browser Video/Visual Rendering:**
   - Component regression tests run in `jsdom`, which does not compute full sub-pixel layout or GPU shaders.
   - Complex Framer Motion exit transitions are simulated in jsdom without layout reflows.
2. **E2E Browser Automation:**
   - Heavy browser automation tools (Playwright/Cypress) were intentionally excluded per Phase 25 specifications to conserve disk space and maintain zero flaky CI dependencies.
3. **External Human Validation Gate:**
   - Automated testing verifies that the UI strictly enforces the unapproved state; technical tests do not and cannot substitute for qualified human advocate review.

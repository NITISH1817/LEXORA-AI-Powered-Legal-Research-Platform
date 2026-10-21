# LEXORA Frontend Baseline Audit Report

**Date:** 2026-10-21  
**Project:** LEXORA — AI-Powered Legal Intelligence & Research Platform  
**Repository:** `https://github.com/NITISH1817/LEXORA-AI-Powered-Legal-Research-Platform`  
**Stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4, Framer Motion 13, Lucide React, Axios, Zustand  
**Status:** Supervised Legal Research Pilot (Human review: 0/160 approved, 160 pending)

---

## 1. Executive Summary

This baseline audit evaluates the existing frontend application across route integrity, API contract compatibility, component reliability, accessibility, visual design consistency, and legal presentation safeguards.

The frontend codebase possesses strong architectural foundations (clear domain division into research sessions, case intelligence, comparative analysis, precedent graphs, and document processing). However, critical integration gaps, dead controls, tab mismatches, and fragmented state handling were identified:
1. **RAG Disconnect in Research Workspace:** The primary research view only invoked `/api/search` (passage search) and never called `/api/research/ask` (or `/api/rag/ask`), leaving the core AI legal synthesis, key findings, and legal principles unreachable from the main UI.
2. **Context Nesting Bug:** `<AuthProvider>` was duplicated in both `src/main.tsx` and `src/App.tsx`, causing nested authentication contexts and desynchronized user state.
3. **Case Intelligence Tab Mismatches:** In `CaseIntelligence.tsx`, the tab list declared `['Executive', 'Timeline', 'Facts', 'Issues', 'Reasoning', 'Principles', 'Outcome']`, but the component checked for `'Decision'` instead of `'Outcome'`, and `'Arguments'` was handled in render code but completely missing from the tab bar.
4. **Hardcoded Evaluation Metrics:** In `EvaluationDashboard.tsx`, the "Unsupported Claims Rate" was hardcoded to `0.05` instead of reading API telemetry, and neither human review status nor pilot feedback empty state was displayed.
5. **Full Page Reloads on Internal Navigation:** Several components used `window.location.href` rather than React Router's `navigate()`, breaking client-side SPA state.
6. **No Centralized API Client:** Raw `axios` calls with ad-hoc `import.meta.env.VITE_API_URL || 'http://localhost:8000'` and differing token key names (`token` vs `access_token`) were scattered across 8+ components.

---

## 2. Inventory of Screens & Components

| Screen / Component | Route / Location | Primary Role | Issues Identified |
| :--- | :--- | :--- | :--- |
| **App Shell & Routing** | `/` (`App.tsx`, `main.tsx`) | Route definitions & ProtectedRoute | Nested `<AuthProvider>`; floating user badge collides with top navigation bars; no unified navigation header. |
| **Authentication — Login** | `/login` (`components/auth/Login.tsx`) | User authentication | Duplicate unused `components/Login.tsx`; lacks pilot restriction disclosure; basic error handling. |
| **Authentication — Register** | `/register` (`components/auth/Register.tsx`) | Supervised pilot onboarding | Correctly requests `invitation_code`, but redirects with `window.location.href`. |
| **Research Workspace** | `/`, `/research` (`components/ResearchWorkspace.tsx`) | Primary legal research workspace | Only performs passage search (`/api/search`), never calls `/api/research/ask`; mocked source viewer passage text; brief markdown rendered as raw text. |
| **Case Intelligence** | Modal/View in Workspace (`components/CaseIntelligence.tsx`) | Deep case brief & profile | Tab mismatch (`Outcome` vs `Decision`; missing `Arguments` tab); no empty state when case lacks analysis. |
| **Case Timeline** | Sub-component (`components/CaseTimeline.tsx`) | Factual & procedural chronology | Solid precision badges; minor date-parsing edge cases; lacks breadcrumb navigation. |
| **Comparative Intelligence** | Sub-component (`components/ComparativeIntelligence.tsx`) | Cross-case matrix & tension analysis | Good distinction of tensions vs conflicts; close button abruptly resets view without preserving prior research. |
| **Precedent Graph** | Sub-component (`components/PrecedentGraph.tsx`) | Citation network visualization | Fixed depth=1; lacks interactive depth slider supported by backend (`depth=1..4`); zoom reset needs centering. |
| **Document Intelligence** | `/documents` (`components/DocumentIntelligence.tsx`) | Document list & pipeline status | Uses `window.location.href` to navigate; ad-hoc auth header generation. |
| **Document Detail** | `/documents/:id` (`components/DocumentDetail.tsx`) | Document metadata & structure | Functional; could improve error recovery and responsive column stacking. |
| **Document Source Viewer** | `/documents/:id/source` (`components/DocumentSourceViewer.tsx`) | Paged legal transcript reader | Functional page navigation; could add direct citation copy with source attribution. |
| **Document Upload** | Modal (`components/DocumentUpload.tsx`) | Multi-part document upload | Fake animation instead of real `onUploadProgress` Axios events. |
| **Evaluation Dashboard** | `/evaluation` (`components/EvaluationDashboard.tsx`) | Model metrics & release gates | Hardcoded metric; lacks human review status and pilot feedback empty state; admin only. |

---

## 3. Detailed Audit Findings by Dimension

### A. Route & Navigation Integrity
- **Issue 1:** `window.location.href` used in `AuthContext.tsx` (`logout`), `Register.tsx` (post-registration), and `DocumentIntelligence.tsx` (`handleOpenDocument`).  
  *Impact:* Causes full document teardown and network reload, bypassing client-side routing.  
  *Fix:* Standardize on React Router's `navigate()` hook.
- **Issue 2:** The global user badge rendered in `ProtectedRoute` (`App.tsx`) is positioned at `absolute top-4 right-4 z-50`.  
  *Impact:* Directly overlays and obscures action buttons in the top headers of `ResearchWorkspace`, `DocumentIntelligence`, and `DocumentDetail`.  
  *Fix:* Move user profile and application navigation into a cohesive global navigation bar (`AppNavbar`).

### B. API Integration & Authentication
- **Issue 3:** Inconsistent Token Storage and Headers.  
  *Detail:* Some files read `localStorage.getItem('token')`, others read `localStorage.getItem('access_token')`. If `token` is missing or expired, requests fail silently or log unhandled errors to the console.  
  *Fix:* Create a unified `src/api/client.ts` Axios instance configured with `VITE_API_URL`, automatic bearer token injection from storage, and a response interceptor that cleanly catches HTTP 401/403 and triggers logout.
- **Issue 4:** Disconnected RAG Legal Research.  
  *Detail:* The backend provides `/api/research/ask` (and `/api/rag/ask`), which returns synthesized legal answers, key findings, legal principles, cited authorities, and limitations. `ResearchWorkspace.tsx` only called `/api/search` which returns raw passage chunks.  
  *Fix:* Add research mode controls (AI Research Synthesis vs Passage Search) allowing practitioners to execute full grounded legal synthesis or direct indexed passage search.

### C. Legal Content Presentation & Safety
- **Issue 5:** Safe Markdown & Citation Attribution.  
  *Detail:* Research briefs and synthesized answers contain Markdown headings, numbered lists, blockquotes, and citations. Currently, `briefMarkdown` is rendered inside `<div className="prose ... whitespace-pre-wrap">` with no markdown parsing, causing markdown syntax (`###`, `**`, `*`) to appear as raw unstyled characters.  
  *Fix:* Implement a clean, type-safe, zero-dependency `SafeMarkdown` component that formats headings, lists, quotes, and citations securely without risk of script injection.
- **Issue 6:** Mandatory Disclaimers & Scope Notices.  
  *Detail:* Legal disclaimers must be prominently visible across all research and case views, stating that LEXORA provides AI-assisted research and not legal advice, and identifying the Supreme Court of India constitutional/commercial landmark corpus scope.

### D. Component State Management (Loading, Error, Empty)
- **Issue 7:** Dead Controls & Mocked Text.  
  *Detail:* In `ResearchWorkspace.tsx`, `onViewSource` used hardcoded placeholder text (`"Loading source passage..."`) rather than inspecting the actual matched text or passage from search results or active case documents.  
  *Fix:* Populate source evidence modals with actual passage text, chunk ID, page number, court, and citation.
- **Issue 8:** Case Intelligence Tab Discrepancy.  
  *Detail:* In `CaseIntelligence.tsx`, `tabs` omitted `'Arguments'` and named the final tab `'Outcome'` while the render block checked for `'Decision'`.  
  *Fix:* Reconcile tab identifiers: `['Executive', 'Facts', 'Issues', 'Arguments', 'Reasoning', 'Principles', 'Outcome', 'Timeline']`.

### E. Evaluation & Metric Transparency
- **Issue 9:** Evaluation Dashboard Integrity.  
  *Detail:* In `EvaluationDashboard.tsx`, "Unsupported Claims Rate" was hardcoded to `0.05`. It did not display denominators, sample sizes ($N=160$, $N=136$ answerable, $N=24$ abstentions), confidence intervals, or the honest status of human review (0/160 approved, 160 pending) and pilot feedback (0 records, empty state verified).  
  *Fix:* Update the dashboard to consume `/api/evaluation/reconciled` and `/api/evaluation/latest`, display exact sample counts, distinguish automated retrieval metrics from human legal approval, and honestly report the human review blocker.

### F. Styling, Responsiveness & Accessibility
- **Issue 10:** Inconsistent Design Tokens & Dead CSS.  
  *Detail:* `App.css` contains default Vite boilerplate (`.hero`, `.counter`, `#next-steps`) not used by the app. Colors across components mix arbitrary hex values (`#0b0f19`) and Tailwind utilities. Focus indicators (`focus-visible:ring-2`) are absent on several key buttons.  
  *Fix:* Clean up `App.css`, establish unified palette tokens in `index.css` (Navy `#0b0f19`, Surface `#111827`, Border `#1e293b`, Primary Blue `#2563eb`, Amber Warning `#f59e0b`), ensure proper mobile drawers for sidebar navigation, and add accessible focus styles.

---

## 4. Remediation Plan

1. **Architecture & API Layer:**
   - Create `src/api/client.ts` with Axios interceptors, baseURL fallback, and centralized error handling.
   - Clean up `main.tsx` to eliminate nested `<AuthProvider>`.
   - Remove unused `src/components/Login.tsx`.
2. **Global Navigation & Layout:**
   - Create `src/components/common/AppNavbar.tsx` for consistent navigation across Research, Documents, and Evaluation views.
   - Update `App.tsx` routes and layout.
3. **Core Research Workspace (`ResearchWorkspace.tsx`):**
   - Implement dual-mode research: **AI Research & Synthesis** (`/api/research/ask`) and **Passage Search** (`/api/search`).
   - Create `src/components/common/SafeMarkdown.tsx` for safe legal markdown rendering.
   - Wire up dynamic source passage inspection in the evidence drawer.
   - Include prominent legal disclaimers and corpus scope banners.
4. **Case Intelligence & Sub-Components:**
   - Fix tab handling in `CaseIntelligence.tsx` (enable Arguments, Outcome, and Timeline).
   - Enhance `PrecedentGraph.tsx` with depth selector controls and empty states.
   - Ensure `ComparativeIntelligence.tsx` preserves session context.
5. **Document Intelligence Suite:**
   - Replace `window.location.href` with React Router navigation.
   - Ensure clean loading, error, and empty states.
6. **Evaluation Dashboard:**
   - Remove hardcoded metrics.
   - Display real $N=160$ benchmark numbers, denominator breakdowns, and honest human legal review status.
7. **Verification:**
   - Execute TypeScript check and Vite production build (`npm run build`).
   - Execute linter (`npm run lint`).
   - Smoke test routing, authentication, research execution, and document inspection.

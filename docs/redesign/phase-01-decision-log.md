# Phase 1 Deliverable 10: Decision Log, Executive Summary & Final Decision Matrix

**Project:** TripLine  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Working Branch:** `agent-v2`  
**Auditor:** Principal AI Solution Architect & Repository Audit Specialist  
**Phase:** 1 of 12 — Deployment, Repository and Product Truth Audit  
**Date:** 2026-10-17  

---

## 1. Executive Summary

### 1.1 What code is currently serving the site?
The application is served by **FastAPI** (`dashboard/app.py`) on port 8080 (`http://127.0.0.1:8080`). It serves both the **Next.js 16.3.3 static export** (`tripline-frontend/out/`) and a legacy server-rendered **Jinja2 router** (`dashboard/routes.py`).

### 1.2 Which frontend is authoritative?
The **Next.js 16 frontend** (`tripline-frontend/`) is the authoritative product UI. It is built with React 19, TailwindCSS v4, Framer Motion 14, and TypeScript 5.7, producing 14 prerendered static pages.

### 1.3 Why do old and new website experiences appear simultaneously?
Because `dashboard/app.py` registers `legacy_router` (line 71) **before** the dynamic Next.js page fallback `@app.get("/{slug}")` (line 88). Whenever a user visits `/receipts`, `/measured`, `/attribution`, or `/about`, FastAPI matches `legacy_router` first and renders the old 2026-10-10 Jinja templates. In contrast, visiting `/`, `/agent`, `/overview`, `/witness`, `/console`, `/jail-burst`, `/claims`, or `/layers` serves the modern Next.js export.

### 1.4 Which backend capabilities are genuinely implemented?
All **27 audited endpoints** across health, environment readiness, agent crew delegation, run manifests, job execution, in-MCP path jail, canary gateway, witness chain verification, tamper checking, and REA software reverse engineering are **genuinely implemented in Python 3.13 source code** and supported by 291 passing automated tests.

### 1.5 Which capabilities are presently verified live?
- **Verified Live at Runtime:** Local REST APIs, CSRF generation, receipt verification, receipt tamper detection, witness log verification, witness tamper detection, jail burst path traversal fuzzing (8/8 trapped), and REA static analysis of synthetic Electron apps.
- **Temporarily Inactive Live Cloud Connection:** Remote live ArmorIQ platform execution is currently `BLOCKED — CREDENTIALS` (returns HTTP 401 on token bootstrap). The system safely fails closed with `AUTHORIZATION-UNAVAILABLE`. All offline tests and deterministic proofs pass 100%.

### 1.6 Which fake or incomplete UI states need correction?
1. Hardcoded fallback decision cards in `agent/page.tsx:710–724` (`RCP-20261016-delete-branch-deny`, `RCP-20261016-path-jail-deny`) that appear when run issues are empty.
2. Synthetic `setTimeout` step simulation and mock receipt IDs (`RCP-P1-ARMORIQ-DENY-7a89f`) in `SecurityArchitecture3D.tsx`.
3. Silent `.catch(() => {})` error blocks swallowing network failures in several views.

### 1.7 What must change before the 3D redesign can safely begin?
1. Authoritative branch `agent-v2` must be confirmed as the sole base of work.
2. The route collision in `dashboard/app.py` must be unified so `/receipts` serves the Next.js explorer.
3. The mock fallback decision cards must be removed so the 3D architecture visual is driven strictly by genuine backend manifests.

### 1.8 What will Phase 2 design and decide?
Phase 2 will establish the formal **Information Architecture, Design Tokens, and Dimensional 3D Wireframes** inspired by Palantir's Multimodal Data Plane, translating the 4-plane security stack into concrete component blueprints.

---

## 2. Architectural Decisions & Verification Log

### Decision 1: Base Implementation Branch Selection
- **Decision:** Select **`agent-v2`** (`commit 9b51028`) as the authoritative source of truth for all subsequent redesign phases (Phase 2 through Phase 12).
- **Evidence:** `agent-v2` is 6 commits ahead of `main` and 10 commits ahead of `ui-redesign`. It contains the complete Agent v2 engine, REA software investigator, rotated witness keys, and 291 passing tests. `ui-redesign` is a direct historical ancestor.
- **Risk:** Branch confusion if developers checkout `main`.
- **Mitigation:** Document `agent-v2` as the only approved branch in `README.md` and CI workflows.

### Decision 2: 3D Animation Engine Strategy
- **Decision:** Implement the 3D dimensional architecture using **Hardware-Accelerated Layered SVG + CSS 3D Perspective + Framer Motion 14**, rather than importing Three.js / React Three Fiber.
- **Evidence:** `framer-motion 14.1.0` is already installed; React 19 compatibility is confirmed; Next.js `output: 'export'` compiles cleanly; subpixel Retina text rendering is preserved.
- **Risk:** Three.js peer dependency conflicts with React 19 and static export SSR hydration errors.
- **Mitigation:** Layered isometric planes with CSS `preserve-3d` achieve the Palantir aesthetic with zero bundle bloat.

### Decision 3: Route Consolidation Strategy
- **Decision:** Plan route consolidation for Phase 4 to remap legacy Jinja routes, allowing `/receipts` and `/measured` to serve the modern Next.js export while preserving test compatibility for `test_phase10_dashboard.py`.
- **Evidence:** TestClient empirical testing proved that Next.js `out/receipts.html` is completely shadowed by `routes.py:57`.

---

## 3. Prioritized Final Decision Matrix

| Priority | Finding & Source Evidence | Risk & Impact | Architectural Decision | Implementation Phase |
|---|---|---|---|---|
| **P0** | **Route Collision Shadows Modern Receipts Explorer**<br>Evidence: `dashboard/app.py:71` mounts `legacy_router` before Next.js page handler. Visiting `/receipts` returns 2026-10-10 Jinja template instead of `tripline-frontend/out/receipts.html`. | Visitors and judges never see the modern receipts explorer; split personality between old and new designs. | Unify routing in `dashboard/app.py` so Next.js static pages take precedence, while preserving compatibility test strings. | **Phase 4 (Route Consolidation)** |
| **P0** | **Misleading Hardcoded Fallback Decisions in Agent Console**<br>Evidence: `agent/page.tsx:710–724` renders mock `delete_branch` and `read_file` cards with fake receipt IDs (`RCP-20261016-*`) when `selectedRun.issues` is empty. | Falsely claims verified security decisions when an empty run is selected. Destroys technical truthfulness. | Remove hardcoded fallback cards; render an honest empty state (`<EmptyState title="No Decision Records in Manifest" />`). | **Phase 3 (Frontend Polish)** |
| **P1** | **Client-Side Timers & Fake Receipt IDs in 3D Diagram**<br>Evidence: `SecurityArchitecture3D.tsx:223–239` uses `setTimeout` chains and synthetic IDs (`RCP-P1-ARMORIQ-DENY-7a89f`). | Simulates security decisions in client-side JavaScript rather than reading recorded backend evidence. | Relabel as an interactive model and bind scenario outcomes to real files under `results/phase3/scenario/`. | **Phase 5 (3D Scene Integration)** |
| **P1** | **Silent Error Swallowing via Empty `.catch(() => {})`**<br>Evidence: Found in `GlossaryDrawer.tsx:139`, `page.tsx:145`, `agent/page.tsx:115`, `claims/page.tsx:33`. | If backend APIs fail, the UI fails silently without informing the user or developer. | Implement visible error indicator badges or toast notifications on network/API failure. | **Phase 3 (Frontend Polish)** |
| **P1** | **Missing Active `ARMORIQ_API_KEY` in Environment**<br>Evidence: `/api/env` returns `armoriq_key_present: false`; 22 live tests skipped. | Live agent runs cannot contact remote platform; fail-closed gate blocks live execution. | Document Mode B offline deterministic proofs as primary judge evaluation path; add instructions for live key export. | **Phase 6 (Execution Hardening)** |
| **P2** | **Design Token Palette Inconsistency**<br>Evidence: `tokens.css` contains warm paper/light tokens mixed with dark section utilities; lacks Palantir silver/graphite palette. | Website lacks unified editorial elegance; visual impression fails the Palantir benchmark. | Implement curated silver, graphite, charcoal, and white palette tokens with subtle electric blue accents. | **Phase 3 (Design System Tokens)** |
| **P2** | **Stale Static Build Sync Risk**<br>Evidence: `tripline-frontend/next.config.mjs` ignores TypeScript errors during build (`ignoreBuildErrors: true`). | Type errors could sneak into codebase without failing `npm run build`. | Mandate `./tripline-frontend/node_modules/.bin/tsc --noEmit` in CI and pre-commit checks. | **Phase 10 (Verification Suite)** |
| **P3** | **Duplicate Navigation Routes (`/attribution` vs `/layers`)**<br>Evidence: Both routes attempt to display layer attribution. | Confuses users with duplicate links in header and audit menu. | Consolidate navigation exclusively to `/layers` and issue HTTP 301 redirect on `/attribution`. | **Phase 4 (Navigation)** |

---

## 4. Phase 1 Completion Gate Verification

| Phase 1 Requirement | Verification Status | Exact Evidence Path / Finding |
|---|---|---|
| **Current branch, commit & working tree documented** | **VERIFIED** | Branch `agent-v2`, commit `9b51028`, working-tree preserved without resets. |
| **Candidate branch differences inspected** | **VERIFIED** | Compared `main`, `ui-redesign`, and `agent-v2`. `agent-v2` is 6 commits ahead of `main`. |
| **Authoritative implementation branch selected** | **VERIFIED** | `agent-v2` selected as complete superset containing all agent v2 and REA features. |
| **Actual frontend serving path documented** | **VERIFIED** | Traced through `next.config.mjs`, `out/`, `app.py`, and `routes.py`. Dual-router split documented. |
| **Public route collisions tested** | **VERIFIED** | Live TestClient confirmed `/receipts`, `/measured`, `/attribution` intercepted by Jinja. |
| **All major routes & components inventoried** | **VERIFIED** | All 12 routes and 23 components cataloged in `phase-01-frontend-inventory.md`. |
| **Misleading states & fake fallbacks mapped** | **VERIFIED** | Located mock fallbacks in `agent/page.tsx:710` and `SecurityArchitecture3D.tsx:223`. |
| **Backend capabilities verified from source** | **VERIFIED** | 27 API endpoints documented with schemas, Pydantic models, and security controls. |
| **Agent lifecycle & states disambiguated** | **VERIFIED** | 14 discrete states mapped; sequence diagram created in `phase-01-agent-lifecycle.md`. |
| **ArmorIQ Mode B & credential truth documented** | **VERIFIED** | SDK v0.6.10 verified; fail-closed gate confirmed; zero secrets exposed. |
| **Security claims verified against evidence** | **VERIFIED** | 11 core claims audited; forbidden terms blacklisted in `phase-01-claims-and-security-audit.md`. |
| **Palantir reference translated into TripLine** | **VERIFIED** | Silver/graphite design brief and 4-plane model defined in `phase-01-reference-analysis.md`. |
| **Baseline test commands executed** | **VERIFIED** | `tsc --noEmit` (0 errors), `next build` (14/14), `pytest` (291 passed, 22 skipped), `ui-coverage` (100%). |
| **All 10 Phase 1 Deliverables generated** | **VERIFIED** | Stored under `docs/redesign/phase-01-*.md`. |

---

## 5. Recommended Next Steps for Phase 2

With the technical foundation firmly established and all 10 audit deliverables completed, the project owner can review these findings and authorize **Phase 2 (Information Architecture, Wireframing & Dimensional 3D Specifications)**:
1. Design the silver/graphite 4-plane isometric architecture layout.
2. Formulate the consolidated navigation schema eliminating Jinja route collisions.
3. Define the scroll-driven camera journey from prompt ingress down to cryptographic receipt verification.

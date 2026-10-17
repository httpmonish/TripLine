# Phase 1 Deliverable 3: Complete Frontend Inventory & UI Integrity Audit

**Project:** TripLine  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Working Branch:** `agent-v2`  
**Auditor:** Principal AI Solution Architect & Frontend Architecture Auditor  
**Standard:** Exhaustive Source Inspection & Component Matrix (Rules 3.1–3.4)  
**Date:** 2026-10-17  

---

## 1. Executive Summary & Page Inventory

The TripLine Next.js frontend (`tripline-frontend/`) contains 12 public routes, 3 layout files, and 23 modular React/TSX components. It is built using **Next.js 16.3.3 (Turbopack)**, **React 19**, **TailwindCSS v4**, and **Framer Motion 14.1.0**.

Every route was inspected at the component and data-binding level. The frontend communicates with the backend exclusively via `tripline-frontend/lib/api.ts` through typed REST endpoints and SSE event streams.

```
tripline-frontend/
├── app/
│   ├── layout.tsx                # Global HTML wrapper, metadata, tokens, Header & Footer
│   ├── page.tsx                  # Enterprise Homepage (Hero, Readiness, Demo, Architecture)
│   ├── agent/page.tsx            # Governed Agent Crew Console, Scoped Keys, REA Runner
│   ├── overview/page.tsx         # System status, readiness checks, count summaries
│   ├── receipts/page.tsx         # Cryptographic Receipts Explorer, Verify, Tamper Check
│   ├── witness/page.tsx          # Append-Only HMAC Witness Chain Reconciler
│   ├── console/page.tsx          # Subprocess Job Execution Console (Allowlisted jobs)
│   ├── jail-burst/page.tsx       # In-MCP Path Jail Fuzzer (8 Probes)
│   ├── measured/page.tsx         # Empirical Benchmark Results Matrix
│   ├── claims/page.tsx           # Formal Claims Ledger & Evidence Links
│   ├── layers/page.tsx           # Multi-Layer Security Attribution Architecture
│   ├── attribution/page.tsx      # Legacy-compatible Attribution Page
│   └── style-guide/page.tsx      # Design System Tokens, Badges, Typography
└── components/
    ├── brand/                    # TripLine isometric SVG logo pack
    ├── diagrams/                 # Architecture diagrams (HeroSecurityVisual, Flow, 3D)
    ├── narrative/                # Narrative bands (StagesBand, GapComparison, etc.)
    ├── security/                 # Multi-layer security cards (SecurityDecisionCard)
    └── ui/                       # Base components (Header, Footer, Button, Card, Badge)
```

---

## 2. Comprehensive Route & Entry Point Matrix

| Route | File Path | User Purpose | Key Components | Data Sources & APIs | Classification | Reuse / Redesign Decision |
|---|---|---|---|---|---|---|
| `/` | `app/page.tsx` | Primary enterprise landing page; explains product mission, readiness, architecture, and live execution | `Header`, `HeroSecurityVisual`, `SecurityArchitectureFlow`, `TripLineLogo`, `Footer` | `GET /api/env`, `GET /api/platform/status`, `GET /api/summary`, `POST /api/jobs` | `RUNTIME_API` + `RECORDED_DEMO` | **Preserve & Elevate:** Retain working job execution and status checks; replace mock isometric graphics with Palantir-inspired 3D canvas in Phase 5. |
| `/agent` | `app/agent/page.tsx` | Authoritative agent console; displays orchestrator, delegated reader/responder keys, live event stream, and REA investigator | `SecurityDecisionCard`, `GlossaryDrawer`, `Header`, `Footer` | `GET /api/agent/crew`, `GET /api/agent/runs`, `GET /api/platform/status`, `GET /api/rea/*`, SSE | `RUNTIME_API` + `MISLEADING_RUNTIME_STATE` (fallback cards) | **Preserve & Correct:** Fix hardcoded fallback decision cards when run issues are empty; retain Ed25519 key viewer and REA static analysis runner. |
| `/overview` | `app/overview/page.tsx` | High-level system dashboard; displays total receipts, runs, environment readiness, and test suites | `Card`, `StatRow`, `Badge` | `GET /api/summary`, `GET /api/health`, `GET /api/env` | `RUNTIME_API` | **Consolidate:** Merge high-value metrics into Homepage and Header; retain as dedicated system dashboard. |
| `/receipts` | `app/receipts/page.tsx` | Interactive receipt explorer; provides JSON inspection, cryptographic verification, and tamper detection | `ReceiptCard`, `CodeBlock`, `Badge` | `GET /api/receipts`, `POST /api/receipts/{id}/verify`, `POST /api/receipts/{id}/tamper-check` | `RUNTIME_API` | **Elevate:** Currently intercepted by legacy Jinja template! Unify serving path in Phase 4 to reveal this superior Next.js explorer. |
| `/witness` | `app/witness/page.tsx` | Verifies append-only HMAC-SHA256 witness chain back to genesis; demonstrates tamper detection | `Card`, `CodeBlock`, `Button` | `GET /api/witness`, `POST /api/witness/verify`, `POST /api/witness/tamper-check` | `RUNTIME_API` | **Preserve:** Completely functional cryptographic verifier. Update styling to silver/graphite palette. |
| `/console` | `app/console/page.tsx` | Interactive job runner; executes allowlisted subprocess tasks (`scenario`, `jail_burst`, `verify_all`, `tamper_demo`) | `Card`, `Button`, `Terminal` | `GET /api/jobs`, `POST /api/jobs`, `GET /api/jobs/{id}/events` (SSE) | `RUNTIME_API` | **Preserve:** Excellent low-level diagnostic tool. Keep as enterprise execution terminal. |
| `/jail-burst` | `app/jail-burst/page.tsx` | Displays results of 8 path traversal probes against in-MCP path jail (dot-dot, percent-encoding, symlink escapes) | `Card`, `Badge`, `StatRow` | `GET /api/jail-burst` | `RUNTIME_API` | **Preserve:** Real-time fuzzer probe verifier proving 0 bytes leaked. |
| `/measured` | `app/measured/page.tsx` | Displays empirical benchmark rows across attack vectors, refusal rates, and protection rates | `Card`, `Badge` | `GET /api/measured` | `RUNTIME_API` + `BUILD_TIME_DATA` | **Elevate:** Currently blocked by legacy Jinja template. Expose Next.js view with mandatory disclaimer on M2 synthetic stubs. |
| `/claims` | `app/claims/page.tsx` | Formal security claims audit ledger linking claims to verified evidence files | `Card`, `Badge`, `Link` | `GET /api/claims`, `GET /api/evidence` | `RUNTIME_API` + `RECORDED_EVIDENCE` | **Preserve:** Core hackathon non-repudiation feature. Keep and style with silver borders. |
| `/layers` | `app/layers/page.tsx` | Visualizes 5-layer security boundary model (Orchestrator -> REA -> ArmorIQ -> Path Jail -> Witness) | `LayerMatrix`, `Card` | `GET /api/attribution` | `RUNTIME_API` + `STATIC_EXPLANATION` | **Elevate:** Modern representation of layer attribution. |
| `/attribution` | `app/attribution/page.tsx` | Legacy alias for `/layers` | `LayerMatrix` | `GET /api/attribution` | `DUPLICATE_UI` | **Consolidate:** Redirect `/attribution` to `/layers`. |
| `/style-guide` | `app/style-guide/page.tsx` | Internal design system reference; showcases tokens, badges, buttons, cards, and sample receipt code | `ReceiptCard`, `Badge`, `Button` | Static UI component preview | `LOCAL_ONLY` | **Internal Reference:** Keep for developer design validation. |

---

## 3. Interactive Controls & Action Audit

| Control / Element | Location | Intended User Action | Backend API / Handler | Loading / Disabled State | Verified Status |
|---|---|---|---|---|---|
| **Start Live Governed Run** | `app/agent/page.tsx` (top right) | Dispatches live agent execution loop across 5 issues | `POST /api/agent/runs` -> `dashboard/api.py:start_agent_run` | Disabled if `!live_enabled` or currently running | `VERIFIED_IN_SOURCE` & tested via `JobManager` |
| **Emergency Kill Switch** | `app/agent/page.tsx` (top right) | Immediately halts agent loop and cancels active job | `POST /api/agent/runs/{id}/stop` & `POST /api/jobs/{id}/cancel` | Changes state to "EMERGENCY KILL SWITCH TRIGGERED" | `VERIFIED_IN_SOURCE` |
| **REA Analysis Runner** | `app/agent/page.tsx` (REA Tab) | Runs controlled static analysis on synthetic Electron app | `POST /api/jobs` with `kind: "rea_investigate"` | "Analyzing...", polling job status every 2s | `VERIFIED_BY_TEST` (`test_rea_integration.py`) |
| **Receipt Verifier** | `app/receipts/page.tsx` | Recomputes RFC 8785 Canonical Hash and HMAC signature | `POST /api/receipts/{id}/verify` | "Verifying...", renders VERIFIED / TAMPER_DETECTED | `VERIFIED_AT_RUNTIME` (200 OK) |
| **Receipt Tamper Demo** | `app/receipts/page.tsx` | Injects 1-byte mutation in memory and tests verifier | `POST /api/receipts/{id}/tamper-check` | "Tampering...", proves original file untouched | `VERIFIED_AT_RUNTIME` (200 OK) |
| **Witness Verifier** | `app/witness/page.tsx` | Reconciles HMAC-SHA256 log chain back to genesis | `POST /api/witness/verify` | Renders chain validity and inspected records count | `VERIFIED_AT_RUNTIME` (200 OK) |
| **Witness Tamper Demo** | `app/witness/page.tsx` | Flips 1 bit in temporary copy and runs chain verifier | `POST /api/witness/tamper-check` | Confirms original log untouched, reports tamper | `VERIFIED_AT_RUNTIME` (200 OK) |
| **Audit Jobs Dispatcher** | `app/console/page.tsx` & `app/page.tsx` | Dispatches allowlisted task (`scenario`, `jail_burst`, etc.) | `POST /api/jobs` | "Running...", streams stdout lines via SSE | `VERIFIED_AT_RUNTIME` (200 OK) |
| **Run Selector Dropdown** | `app/agent/page.tsx` | Switches active run manifest and associated event stream | `GET /api/agent/runs/{id}` | Updates selected run and switches SSE subscription | `VERIFIED_IN_SOURCE` |
| **Copy Public Key** | `app/agent/page.tsx` | Copies delegated Ed25519 public key hex to clipboard | Browser `navigator.clipboard.writeText` | Shows "Copied" checkmark for 2s | `LOCAL_ONLY` |

---

## 4. Misleading UI Logic & Defect Forensics

A forensic scan across all components identified five specific patterns of misleading UI logic that must be corrected in subsequent phases:

### Defect 1: Hardcoded Mock Decision Fallbacks in Agent Console
- **Location:** `tripline-frontend/app/agent/page.tsx:708–732`
- **Observed Code:**
  ```tsx
  <SecurityDecisionCard
    action="delete_branch"
    targetOrArgs={{ branch: "refs/heads/main" }}
    armoriqDecision="DENY"
    armoriqReason="Disallowed action: delete_branch not permitted by policy"
    armoriqPolicy="policy-triage-block"
    triplineDecision="UNCHECKED"
    dispatchStatus="BLOCKED"
    executionOutcome="Halted upstream by ArmorIQ before tool dispatch"
    receiptId="RCP-20261016-delete-branch-deny"
    verificationStatus="VERIFIED"
  />
  <SecurityDecisionCard
    action="read_file"
    targetOrArgs={{ path: "../../.ssh/id_rsa" }}
    armoriqDecision="ALLOW"
    armoriqReason="Benign tool permitted under read role"
    armoriqPolicy="policy-triage-authorized"
    triplineDecision="DENY"
    triplineControl="path_jail"
    triplineReason="Traversal attempt outside approved repository root"
    dispatchStatus="BLOCKED"
    executionOutcome="Trapped by TripLine in-MCP path jail (0 bytes read)"
    receiptId="RCP-20261016-path-jail-deny"
    verificationStatus="VERIFIED"
  />
  ```
- **Finding:** If the selected run has an empty `issues` array (`!selectedRun?.issues || selectedRun.issues.length === 0`), the UI falls back to rendering these two hardcoded cards with fake receipt IDs (`RCP-20261016-delete-branch-deny`, `RCP-20261016-path-jail-deny`) and stamped `"VERIFIED"` badges, even though no such receipts were loaded from the backend.
- **Classification:** `MISLEADING_RUNTIME_STATE`
- **Corrective Action (Phase 3):** Remove hardcoded fallback cards. Render an honest empty state (`<EmptyState title="No Decision Records in Manifest" />`) when no issue decisions exist.

### Defect 2: Client-Side Timers & Synthetic Receipt IDs in 3D Architecture Visual
- **Location:** `tripline-frontend/components/diagrams/SecurityArchitecture3D.tsx:162, 177, 192, 207, 223–239`
- **Observed Code:**
  ```tsx
  receiptId: 'RCP-P1-ARMORIQ-DENY-7a89f'
  receiptId: 'RCP-P2-JAIL-DENIED-e14a2'
  receiptId: 'RCP-P3-EGRESS-HELD-99b34'
  ...
  useEffect(() => {
    setIsSimulating(true)
    setSimulationStep(0)
    const timer1 = setTimeout(() => setSimulationStep(1), 300)
    const timer2 = setTimeout(() => setSimulationStep(2), 700)
    const timer3 = setTimeout(() => setSimulationStep(3), 1100)
    const timer4 = setTimeout(() => setSimulationStep(4), 1600)
    const timer5 = setTimeout(() => setIsSimulating(false), 2200)
  }, [activeScenario])
  ```
- **Finding:** `SecurityArchitecture3D.tsx` uses client-side `setTimeout` chains to simulate a multi-plane security flow, referencing manufactured receipt IDs that do not exist on the filesystem.
- **Classification:** `RECORDED_DEMO` / `MISLEADING_RUNTIME_STATE`
- **Corrective Action (Phase 5):** Clearly label this component as an **"Interactive Architecture Model"** and bind the scenario outcomes to actual recorded receipts under `results/phase3/scenario/` (`receipt_P1_ARMORIQ_DENY.json`, `receipt_P2_JAIL_DENY.json`, `receipt_P3_GATEWAY_HOLD.json`) rather than synthetic random string IDs.

### Defect 3: Silent `.catch(() => {})` Exception Swallowing
- **Locations:**
  - `tripline-frontend/components/ui/GlossaryDrawer.tsx:139`
  - `tripline-frontend/app/page.tsx:145, 149`
  - `tripline-frontend/app/claims/page.tsx:33`
  - `tripline-frontend/app/overview/page.tsx:43`
  - `tripline-frontend/app/agent/page.tsx:115, 121`
- **Finding:** Several fetch operations silently ignore network or backend errors via empty `.catch(() => {})` handlers, masking API unavailability from the user.
- **Classification:** `BROKEN_INTEGRATION`
- **Corrective Action (Phase 3):** Implement visual error notification banners or subtle inline indicators when an API call fails.

### Defect 4: Hardcoded Receipt Output in Style Guide
- **Location:** `tripline-frontend/app/style-guide/page.tsx:15, 131`
- **Finding:** Displays hardcoded terminal verification text with canned SHA-256 hashes (`84d707a1...`, `eedc5214...`).
- **Classification:** `STATIC_EXPLANATION` (Acceptable in internal style guide, but must never leak to production landing page).

---

## 5. Prioritized Frontend Corrections for Later Phases

1. **[P0] Unify Routing & Eliminate Jinja Interceptions (Phase 4):** Ensure `/receipts`, `/measured`, and `/attribution` serve the Next.js pages instead of obsolete server-rendered templates.
2. **[P1] Eliminate Mock Decision Cards in Agent Console (Phase 3):** Replace `agent/page.tsx` hardcoded fallback cards with honest empty states.
3. **[P1] Bind 3D Architecture Visual to Real Evidence (Phase 5):** Replace synthetic IDs in `SecurityArchitecture3D.tsx` with verified files from `results/phase3/scenario/`.
4. **[P2] Surface API Error Feedback (Phase 3):** Replace empty `.catch()` handlers with error banners.
5. **[P2] Apply Restrained Silver/Graphite Palette (Phase 3):** Update `tokens.css` across all pages to adhere strictly to the Palantir visual reference.

# Tripline Enterprise Redesign Frontend (`web/` / `tripline-frontend/`)

A serious enterprise AI-agent security product website for Tripline, built for the ArmorIQ "Flow State 2026" hackathon.

## Architecture & Technology Stack
- **Framework**: Next.js 16 (App Router) with static HTML export (`output: 'export'`)
- **Styling**: Tailwind CSS + Custom CSS Variables in `styles/tokens.css`
- **Typography**: Self-hosted local WOFF2 fonts (`Geist` and `Geist Mono`), zero third-party network requests
- **Diagrams & Animation**: Inline SVG React components, zero heavy animation runtimes, strict `prefers-reduced-motion` compliance
- **Data Integrity**: Typed build-time data generation from repository evidence (`scripts/sync-data.ts`)

## Interactive Enterprise Routes
- `/` — Enterprise Homepage: Interactive multi-layer architecture visualization, live platform readiness indicators, recent runs & receipts summary, cryptographic verification and tamper-check controls.
- `/agent` — Agent Console: Real crew manifests with Ed25519 signing keys, run history selector, live run execution with CSRF/confirmation safeguards, SSE event streaming, REA static analysis inspection, and distinct ArmorIQ vs TripLine security decision cards.
- `/receipts` — Security Receipts Registry: Signed Ed25519/HMAC receipts explorer with direct backend verification (`POST /api/receipts/{id}/verify`) and live single-byte tamper checks (`POST /api/receipts/{id}/tamper-check`).
- `/witness` — Witness Ledger: Append-only HMAC-SHA256 hash-chain binding tool calls with interactive backend chain verification and tamper demonstration.
- `/console` — Safe Operations & Technical Console: 8 allowlisted jobs (`jail_burst`, `verify_all`, `tamper_demo`, `rea_investigate`, `scenario`, `audit`, `armoriq_proof`, `tests`) with live subprocess terminal streaming and cancellation.
- `/jail-burst` — Path Jail Burst Harness: 8 deterministic path-traversal encoding probes with 0 leaked bytes.
- `/measured` — Measured Overhead & Protection: Empirical protection metrics and code growth stats.
- `/claims` — Claims & Honest Limits: Rule 10 truth audit matrix and acknowledged residuals.
- `/layers` (alias `/attribution`) — Layer Attribution: 5-layer containment matrix across recorded attacks.
- `/overview` — Comprehensive narrative overview with dynamic API hydration.

## How to Build & Export
```bash
# 1. Sync repository data from results/ and docs/ into typed JSON
node --experimental-strip-types scripts/sync-data.ts

# 2. Build and export static site to out/
npm run build
```

## How to Serve with FastAPI Unified Dashboard
```bash
# Serves Next.js exported frontend at http://127.0.0.1:8080/
make dashboard
```

## How to Verify Receipts
```bash
# Offline verification via Python
make verify

# Tamper detection demo
make tamper

# Truth & Hygiene audit
make audit
```

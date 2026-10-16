# Tripline Enterprise Redesign Frontend (`web/` / `tripline-frontend/`)

A serious enterprise AI-agent security product website for Tripline, built for the ArmorIQ "Flow State 2026" hackathon.

## Architecture & Technology Stack
- **Framework**: Next.js 16 (App Router) with static HTML export (`output: 'export'`)
- **Styling**: Tailwind CSS + Custom CSS Variables in `styles/tokens.css`
- **Typography**: Self-hosted local WOFF2 fonts (`Geist` and `Geist Mono`), zero third-party network requests
- **Diagrams & Animation**: Inline SVG React components, zero heavy animation runtimes, strict `prefers-reduced-motion` compliance
- **Data Integrity**: Typed build-time data generation from repository evidence (`scripts/sync-data.ts`)

## Routes
- `/` — Overview: Hero (D1), The Gap, Three Stages (D2), Interception Narrative, Layer Matrix (D3), Non-Repudiation (D5), Modules, Evidence Views, Closing CTA.
- `/receipts` — Incident Receipts Registry: Ruled receipt list, ReceiptCard, D5 verify strip, offline and in-memory tamper simulation.
- `/console` — Agent Execution Trace: Terminal timeline of Claude 3.5 Sonnet processing 5 issues.
- `/jail-burst` — Path Jail Burst Harness: 8 deterministic path-traversal encoding probes with 0 leaked bytes.
- `/witness` — Witness Hash-Chain Ledger: Append-only HMAC hash-chain binding tool executions.
- `/measured` — Measured Overhead & Protection: Empirical protection metrics and code growth stats.
- `/claims` — Claims & Honest Limits: Rule 10 truth audit matrix and acknowledged residuals.
- `/layers` (alias `/attribution`) — Layer Attribution: 5-layer containment matrix across recorded attacks.

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

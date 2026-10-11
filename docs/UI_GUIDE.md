# Tripline UI & Evidence Guide

**Phase**: Phase 10 Enterprise UI Redesign  
**Target**: ArmorIQ Flow State Hackathon Submission  
**Authoritative Backend**: FastAPI + typed Next.js 16.3 static bundle (`out/`)

---

## 1. Route Navigation & Evidence Mapping

Tripline is structured as a 12-route evidence exploration workspace. Every number, table, and verification action is bound to live FastAPI endpoints reading deterministic artifacts.

| Route / Nav | Purpose | Primary Backend Endpoint | Real Evidence Source |
|-------------|---------|--------------------------|----------------------|
| **Overview** (`#overview`) | Product narrative homepage: 9 alternating editorial sections with real recorded run replay & proof metrics. | `GET /api/summary`, `GET /api/runs`, `GET /api/runs/{id}` | `results/phase3/scenario/`, `results/demo/`, `scripts/jail_burst.py` |
| **Console** (`#console`) | Job execution, cancel, history, and live SSE streaming logs. | `GET /api/jobs`, `POST /api/jobs`, `GET /api/jobs/{id}/events` | `results/ui_jobs/` |
| **Attribution** (`#attribution`) | 5-layer defense boundary explorer and 3-attack layer attribution matrix. | `GET /api/attribution` | `docs/phase3_layer_attribution.md` |
| **Jail Burst** (`#burst`) | Deterministic 8-probe path jail execution table with positive control. | `GET /api/jail-burst` | Live execution via `scripts/jail_burst.py` |
| **Receipts** (`#receipts`) | Forensic receipt inspector: decision, covered fields, cryptographic verification, tamper detection. | `GET /api/receipts`, `GET /api/receipts/{id}`, `POST /api/receipts/{id}/verify` | `results/demo/receipt_*.json`, `results/phase3/scenario/receipt_*.json` |
| **Witness** (`#witness`) | Append-only HMAC log records, sequential chaining verification, and tamper detection. | `GET /api/witness`, `POST /api/witness/verify`, `POST /api/witness/tamper-check` | `.tripline/witness/*.jsonl` |
| **Measured** (`#measured`) | Defense rate matrix, refusal vs protection rate breakdown, and model caveats. | `GET /api/measured` | `results/phase3/measured/summary.md`, `measured_runs.jsonl` |
| **Evidence** (`#evidence`) | Structured index of all artifact files with real computed SHA-256 hashes and file viewer. | `GET /api/evidence`, `GET /api/evidence/file` | `results/`, `docs/evidence/` |
| **Video** (`#video`) | 90-second judge walkthrough player with chapters, captions, and disclosure text. | `GET /api/video` | `video/output/tripline_proof_90s.mp4`, `docs/VIDEO_STORYBOARD.md` |
| **Claims** (`#claims`) | Complete ledger of claims, verification status badges, evidence paths, and honest residuals. | `GET /api/claims` | `docs/FINAL_CLAIMS_AUDIT.md` |
| **Checklist** (`#platform`) | ArmorIQ hackathon onboarding and sponsor rubric compliance matrix. | `GET /api/platform-checklist` | `docs/SUBMISSION_CHECKLIST.md` |
| **About** (`#about`) | System architecture, runtime environment, boundary scope, and documentation index. | `GET /api/docs`, `GET /api/docs/{doc_name}` | `docs/limitations.md`, `docs/JUDGE_QA.md` |

---

## 2. Distinction: Recorded Evidence vs. Illustration

- **Recorded Run Mode**: Displays active, verified runs (`job-phase3-wow-*`, `job-phase8-*`). All action parameters, deciding layers, tool calls, and execution counts reflect authentic stored records.
- **Illustration Mode**: Clearly labeled with `Architecture (not a live decision)`. Displayed when no run has been selected or during general architectural exploration.

---

## 3. How to Run Locally

### Start Dashboard (FastAPI serving Next.js Static Export)
```bash
make dashboard
# Serves at http://localhost:8080
```

### Rebuild Frontend Bundle
```bash
make ui
# Compiles Next.js with output: 'export' into tripline-frontend/out/
```

### Run Two-Way UI <-> API Coverage Check
```bash
make ui-coverage
# Generates docs/UI_COVERAGE.md asserting 100% route and element binding
```

### Run Test Suite & Hygiene Audit
```bash
make test
make audit
```

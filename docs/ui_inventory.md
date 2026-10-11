# Tripline Frontend UI Inventory

**Phase 9 Preflight Discovery: Interactive Elements & Data Displays**  
**Repository**: Tripline (`httpmonish/TripLine`)  
**Directory**: `tripline-frontend/`  
**Framework**: Next.js 16.3.3 (React 19, TypeScript, Tailwind CSS, static export)  
**Inspection Method**: Headless AST dump and pattern search across `tripline-frontend/app/`  

---

## 1. Interactive Elements Inventory

| Page / Route | Element Label | Component / Selector | Intended Behaviour | Currently Wired? | Proposed Endpoint / Handler |
|---|---|---|---|---|---|
| `/` (Landing/Nav) | TRIPLINE (Brand) | `a.brand` | Smooth scroll / navigate to top | Yes (anchor) | `data-local="navigate-top"` |
| `/` (Landing/Nav) | Receipts | `nav > a[href="#receipts"]` | Scroll to layer / receipt breakdown | Yes (anchor) | `data-local="scroll-receipts"` |
| `/` (Landing/Nav) | Runs | `nav > a[href="#runs"]` | Scroll to incident replay section | Yes (anchor) | `data-local="scroll-runs"` |
| `/` (Landing/Nav) | Boundary | `nav > a[href="#boundary"]` | Scroll to security boundary section | Yes (anchor) | `data-local="scroll-boundary"` |
| `/` (Landing/Nav) | Scoreboard | `nav > a[href="#scoreboard"]` | Scroll to benchmark scoreboard | Yes (anchor) | `data-local="scroll-scoreboard"` |
| `/` (Hero) | VIEW THE RECEIPTS → | `a.button-primary` | Jump to incident runs replay | Yes (anchor) | `data-local="scroll-runs"` |
| `/` (Hero) | READ THE LIMITATIONS ↗ | `a.button-secondary` | Jump to FAQ & limitations | Yes (anchor) | `data-local="scroll-limitations"` |
| `/` (Replay) | Incident Tabs (`DP-01`, `IE-01`) | `div.tabs > button` | Switch displayed incident replay | Partially (mock state) | `data-local="select-incident"` |
| `/` (Replay) | Copy Verification Command | `button.copy-button` | Copy `make verify FILE=...` to clipboard | Yes (clipboard API) | `data-local="copy-verify-cmd"` |
| `/` (FAQ) | FAQ Accordion Toggles (x6) | `div.faq-row > button` | Expand/collapse question explanation | Yes (React state) | `data-local="toggle-faq"` |
| `/` (CTA) | VIEW THE RECEIPTS → | `a.button-primary` | Jump to incident runs replay | Yes (anchor) | `data-local="scroll-runs"` |
| `/` (Signup Mock) | Work Email Input | `input[type="email"]` | Mock signup entry (v0 preview) | No (mock) | Remove or wire to local preview |
| `/` (Signup Mock) | Password Input | `input[type="password"]` | Mock signup entry (v0 preview) | No (mock) | Remove or wire to local preview |
| `/` (Signup Mock) | CONTINUE → | `button.button-primary` | Step advance in preview | Yes (local preview) | `data-local="advance-signup-step"` |
| `/` (Signup Mock) | Reset preview | `button.button-secondary` | Reset preview form | Yes (local preview) | `data-local="reset-signup-step"` |
| `/` (Footer) | Footer Anchor Links (x8) | `footer a` | Internal anchor navigation | Yes (anchors) | `data-local="navigate-*"` |
| `/console` | Start Job Dropdown | `select#job-kind` | Select job to run (`scenario`, `jail_burst`, etc.) | To be added | `POST /api/jobs` |
| `/console` | Run Button | `button#btn-run-job` | Launch background job | To be added | `POST /api/jobs` |
| `/console` | Cancel Button | `button#btn-cancel-job`| Terminate currently executing job | To be added | `POST /api/jobs/{id}/cancel` |
| `/console` | Stream Output Box | `pre#job-events-stream`| Live SSE terminal log feed | To be added | `GET /api/jobs/{id}/events` |
| `/receipts` | Receipt Selector | `button.receipt-item` | Select receipt from recorded list | To be added | `GET /api/receipts/{id}` |
| `/receipts` | Verify Receipt Button | `button#btn-verify-rcpt`| Execute cryptographic RFC-8785 verifier | To be added | `POST /api/receipts/{id}/verify` |
| `/receipts` | Tamper Check Button | `button#btn-tamper-rcpt`| Run 1-byte tamper check on covered field | To be added | `POST /api/receipts/{id}/tamper-check` |
| `/witness` | Verify Chain Button | `button#btn-verify-witness`| Run real HMAC hash-chain verifier | To be added | `POST /api/witness/verify` |
| `/witness` | Tamper Witness Button | `button#btn-tamper-witness`| Run 1-character tamper check on witness | To be added | `POST /api/witness/tamper-check` |
| `/burst` | Re-run Jail Burst | `button#btn-run-burst` | Trigger deterministic path jail probes | To be added | `POST /api/jobs` (`jail_burst`) |
| `/evidence` | View File Button | `button.evidence-view` | Open allowlisted evidence file | To be added | `GET /api/evidence/file` |
| `/evidence` | Download Evidence | `a.evidence-download` | Download real evidence file | To be added | `GET /api/evidence/file` |
| `/video` | Video Play / Pause | `video#demo-player` | Play 86-second demo video | To be added | `GET /api/video` |
| `/claims` | Refresh Ledger Button | `button#btn-refresh-claims`| Reload parsed claims status ledger | To be added | `GET /api/claims` |

---

## 2. Data Displays & Current vs Required Sources

| Component / Section | Display Description | Current Source | Required Source |
|---|---|---|---|
| Hero Replay Chip | Decision badges (`ALLOW`, `DENY`) | Hardcoded literal strings | Live data from `results/demo/receipt_DP-01.json` |
| Proof Tiles | `stats.total_receipts` | Initial state 2 | `GET /api/summary` -> real file count |
| Proof Tiles | `stats.total_benchmark_runs` | Initial state 86 | `GET /api/measured` -> manifest / recorded count |
| Proof Tiles | Tests passing (`153`) | Hardcoded literal `153` | Real count from `GET /api/health` or `GET /api/env` |
| Diff Box | `read_file` path diff | Hardcoded string literals | Real incident fields from `results/demo/` |
| Action Log | Forensic timeline stages | Hardcoded array of 5 strings | Real events from `results/demo/events.jsonl` |
| Flow Map | 6-stage pipeline stages | Hardcoded array of 6 strings | Matches real pipeline stages |
| Replay Panel | Proposal arguments, decisions | Default state from constants | Fetched from `/api/runs/{id}` and `/api/receipts` |
| Status Strip | Active status string | Hardcoded `READY` | Real model, date, commit from `GET /api/health` |
| FAQ Section | Questions & answers | Static array of tuples | Static text matching `docs/JUDGE_QA.md` |
| Header Bar | `M2 stub mode` | Hardcoded string | Data-driven: `GET /api/env` (model, mode, commit) |
| Console Logs | Empty / nonexistent | None | Real Server-Sent Events from `GET /api/jobs/{id}/events` |
| Jail Burst Table | None on landing | None | Real recorded probe table from `GET /api/jail-burst` |
| Witness Table | None on landing | None | Real chain entries from `GET /api/witness` |
| Measured Table | None on landing | None | Real matrix from `GET /api/measured` |
| Evidence Index | None on landing | None | Real index with SHA-256 hashes from `GET /api/evidence` |
| Platform Checklist | None on landing | None | Read from `GET /api/platform-checklist` |

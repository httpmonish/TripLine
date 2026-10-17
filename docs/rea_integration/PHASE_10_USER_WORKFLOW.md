# Phase 10 — User-Facing Investigation Workflow

**Date:** 2026-10-17  
**Interface:** CLI Investigator (`scripts/rea_investigator.py`) & FastAPI Integration (`dashboard/app.py`)  

---

## 1. Workflow Overview

The TripLine REA workflow provides developers and security analysts with a clean, governed software investigation flow:

```
[1. User Selects Preapproved Target]
       │  (e.g., --target synthetic-electron-app)
       ▼
[2. Target Validation Gate]
       │  Validates target against APPROVED_TARGET_REGISTRY
       ▼
[3. ArmorIQ Policy Gate]
       │  Evaluates session.check against active policy
       ▼
[4. Dispatch REA Analysis]
       │  Persistent stdio JSON-RPC to rea-agents@6.5.0
       ▼
[5. Follow-Up Feature Trace]
       │  Traces entry module / IPC handlers on active session
       ▼
[6. Review Investigation Report & Security Receipt]
       │  Markdown report + HMAC-signed forensic audit receipt
```

---

## 2. CLI Usage Guide

### Basic Investigation (Live REA Mode)
```bash
.venv313/bin/python scripts/rea_investigator.py --mode live-rea
```
- Performs real REA static analysis on `rea_targets/synthetic_electron_app`.
- Discovers JavaScript modules, parsed files, and BrowserWindow instances.
- Performs a live feature trace on `main.js`.
- Generates `report.md`, `report.json`, and `receipt.json`.

### Live-Governed Investigation (ArmorIQ Enforcement)
```bash
.venv313/bin/python scripts/rea_investigator.py --mode live-governed
```
- Connects to `https://api.armoriq.ai`.
- Mints intent token via `/iap/sdk/token`.
- Queries authoritative platform policy via `/iap/sdk/enforce`.
- If denied (e.g. `tool_not_in_allowlist`), halts dispatch immediately (`dispatch_attempted=False`) and emits a signed audit receipt.

### Offline Testing Mode (Deterministic Mocks)
```bash
.venv313/bin/python scripts/rea_investigator.py --mode offline
```
- Completely isolated; executes in < 0.1s without spawning Node.js or contacting ArmorIQ.

---

## 3. UI and Safety Guarantees

1. **Secret Redaction:** API keys, access tokens, and credential strings are strictly redacted from CLI output and generated receipts.
2. **Honest Labeling:**
   - Live REA execution is marked `LIVE_VERIFIED`.
   - Mock runs are marked `TEST_SIMULATED`.
   - Denied operations are marked `BLOCKED` with `dispatch_attempted=False`.
3. **Traceable Evidence:** Every claim links directly to immutable Evidence IDs (`ev_...`).

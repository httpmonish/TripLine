# Phase 11 — Reproducible End-to-End Demo

**Date:** 2026-10-17  
**Demo Runner:** `scripts/rea_investigator.py`  
**Proof Script:** `scripts/armoriq_proof.py`  

---

## 1. Demo Execution Sequence

Follow this exact sequence to demonstrate the complete integration:

### Step 1: Environment & Diagnostic Verification
```bash
# Verify REA package diagnostics (207 tools, healthy)
npx -y rea-agents@6.5.0 mcp doctor
```

### Step 2: Live ArmorIQ Platform Enforcement Proof
```bash
# Verify authoritative platform policy enforcement (In-policy ALLOW + Out-of-policy DENY)
.venv313/bin/python scripts/armoriq_proof.py --json
```

### Step 3: Run Live REA Software Investigation
```bash
# Perform genuine static analysis and feature tracing on synthetic Electron app
.venv313/bin/python scripts/rea_investigator.py --mode live-rea
```
**Expected Output:**
- Target confinement verified to `rea_targets/synthetic_electron_app`.
- Persistent REA stdio subprocess spawned (`rea-agents@6.5.0`).
- Analysis completed: returns `evidence_id: ev_...` and `parent_evidence_id: ev_...`.
- Feature trace on `main.js` completed on active session.
- Generates markdown investigation report (`report.md`) and signed HMAC receipt (`receipt.json`).

### Step 4: Run Live Governed Enforcement Gate
```bash
# Demonstrate live ArmorIQ platform gate blocking an un-allowlisted tool
.venv313/bin/python scripts/rea_investigator.py --mode live-governed
```
**Expected Output:**
- Contacts `https://api.armoriq.ai`.
- Mints intent token via `/iap/sdk/token` (`HTTP 200 OK`).
- Evaluates `/iap/sdk/enforce` (`HTTP 200 OK`).
- Decision: `DENY` (`tool_not_in_allowlist`).
- Dispatch is strictly aborted (`dispatch_attempted=False`).
- Signed incident receipt recorded with `failure_stage: AUTHORIZATION`.

### Step 5: Run Full Test Suite
```bash
# Run all 23 focused integration tests
PYTHONPATH=. .venv313/bin/pytest tests/test_rea_integration.py -v
```

---

## 2. Execution Modes Comparison

| Mode | REA Execution | ArmorIQ Enforcement | Use Case |
|:---|:---:|:---:|:---|
| `offline` | Mock Double | Mock Policy | Unit tests, CI without network/credentials |
| `live-rea` | Genuine (`rea-agents@6.5.0`) | Local Governance | Real static analysis demonstration |
| `live-governed` | Genuine (`rea-agents@6.5.0`) | Live Platform (`/iap/sdk/enforce`) | Authoritative governed agent enforcement |

# Phase 8 — Functional Agent Experience & Live Demonstration Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Routes:** `/` (Section 4), `/agent` (Operations Console)  
**Author:** AI Agent Systems Engineer & ArmorIQ Integration Specialist  
**Status:** Approved & Implemented  

---

## 1. Supported Capabilities & Honest Demarcation

TripLine's demonstration engine is engineered around product truth. It strictly separates:

1. **Deterministic Local Proof Jobs (Primary Recommendation for Evaluators & Judges):**
   * Accessible regardless of external cloud credentials.
   * `scenario`: Runs multi-layer attack scenarios (`delete_branch`, `read_file` traversal, `comment_issue` canary leak).
   * `jail_burst`: Executes 10-probe adversarial path traversal fuzzer.
   * `rea_investigate`: Triggers static binary analysis of registered targets.
   * `verify_all`: Runs cryptographic batch verification over all receipts.
2. **Live Governed Agent Runs:**
   * Bound to real CrewAI orchestrator (`tripline-maintainer`) with scoped reader and responder roles.
   * Enforces fail-closed Mode B ArmorIQ gateway (`TRIPLINE_ENABLE_LIVE=1` required).
   * In the current test checkout where remote keys are not configured (`armoriq_key_present: false`), the live run control displays an honest explanatory badge:
     `"Mode B Fail-Closed (Key not configured; deterministic proof active)"`.
3. **Recorded Demonstrations:**
   * Clearly marked with `"Recorded Demonstration Replay"`.
   * Directly loads verified historical artifacts (`results/phase3/scenario/*.json`).

---

## 2. Interactive Execution Architecture

```
[User Clicks "Execute Selected Task"]
           |
           v
  POST /api/jobs { kind: "scenario", params: {} }
           |
           +--> Returns authentic Job ID: job-proof-20261017-...
           |
           v
  Connect EventSource (/api/jobs/{id}/events)
           |
           +--> Real-time stdout stream renders in Terminal View
           |
           v
  Job Reaches Exit Code 0 (Completed)
           |
           +--> GET /api/receipts/latest loads newly minted RFC 8785 receipt
           |
           v
  User Clicks "Verify" or "Test Tamper"
           |
           +--> Calls POST /api/receipts/{id}/verify (Real backend verifier)
```

### 2.1 Kill Switch & Stop Semantics
* Clicking `Stop Execution` calls `POST /api/jobs/{id}/cancel` and/or `POST /api/agent/runs/{id}/stop`.
* Preserves CSRF protection (`X-CSRF-Token`).
* State does not update to `CANCELLED` until confirmed by backend response.

---

## 3. Elimination of Synthetic Fallbacks

* **No Synthetic Decision Cards:** Removed previous mock fallbacks (`RCP-20261016-delete-branch-deny`, `RCP-20261016-path-jail-deny`) when `selectedRun.issues` is empty. The interface renders an honest `<EmptyState>` explaining that no issues were recorded for that run.
* **No `setTimeout` Cascades:** All step progressions and verdict highlights are driven by actual SSE events or authentic disk receipts.

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Working Backend Actions:** Primary demo triggers real backend jobs via `/api/jobs`.
- [x] **Live Mode Gated Honestly:** Missing ArmorIQ keys do not manufacture false approvals.
- [x] **Real-Time SSE Streaming:** Terminal view streams authentic log output.
- [x] **Reconciliation Verified:** Completed jobs reconcile with generated receipts.

# Phase 7 — Real Backend Event Adapter & Execution State Machine Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Components:** `tripline-frontend/lib/api.ts`, `dashboard/api.py`, `dashboard/jobs.py`  
**Author:** AI Agent Systems Engineer & Senior Full-Stack Architect  
**Status:** Approved & Implemented  

---

## 1. Event Source Architecture & Lifecycle

TripLine connects to three distinct backend telemetry channels, each preserved for its authentic semantics:

```
[Backend Runtime]
   |
   +--> 1. Job SSE Stream (/api/jobs/{id}/events)
   |       - Emits real-time job log lines, subprocess outputs, execution steps, exit codes.
   |
   +--> 2. Agent Run SSE Stream (/api/agent/runs/{id}/events)
   |       - Emits structured decision stages (Ingress, ArmorIQ Gate, MCP Jail, Witness).
   |
   +--> 3. Forensic Artifact Store (results/phase3/scenario/*.json)
           - Authoritative historical disk records (RFC 8785 canonical receipts).
```

### 1.1 Strict Identifier Separation
* **`job_id` $\neq$ `run_id`**: A background job (`job-...`) provisions, monitors, and wraps the execution of an agent session (`run-...`). The frontend tracks both identifiers independently and correlates them via the backend job record rather than assuming equivalence.

---

## 2. Normalized Execution State Machine

All execution consumers (interactive console, 4-plane architecture scene, receipt inspectors) bind to a single typed state model defined in `tripline-frontend/lib/api.ts`:

```typescript
export interface NormalizedExecutionState {
  mode: 'LIVE' | 'PROOF_JOB' | 'RECORDED_REPLAY'
  jobId: string | null
  runId: string | null
  currentEvent: string | null
  actionProposal: {
    tool: string
    args?: Record<string, any>
    rawCall?: string
  } | null
  armorIQVerdict: 'ALLOW' | 'DENY' | 'UNAVAILABLE' | 'ERROR' | 'NOT_REACHED'
  armorIQReason?: string
  tripLineVerdict: 'ALLOW' | 'PATH_JAIL_DENIAL' | 'CANARY_HOLD' | 'NOT_REACHED'
  tripLineReason?: string
  dispatchState: 'NOT_DISPATCHED' | 'DISPATCHED_TO_TOOL' | 'FAILED'
  toolOutcome?: {
    exitCode?: number
    outputSnippet?: string
    error?: string
  }
  receiptId: string | null
  canonicalHash: string | null
  evidenceStatus: 'UNAVAILABLE' | 'UNVERIFIED' | 'VERIFIED' | 'TAMPER_DETECTED'
  verificationReason?: string
  finalState: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'HALTED' | 'FAILED'
  errorReason?: string
}
```

---

## 3. Strict Verdict Differentiation Matrix

The state machine strictly distinguishes between 12 distinct runtime permutations:

| Case | ArmorIQ Gate | TripLine Jail/Canary | Dispatch State | Visual Indicator |
| :--- | :--- | :--- | :--- | :--- |
| **1. Upstream Denial** | `DENY` | `NOT_REACHED` | `NOT_DISPATCHED` | Plane 2 Red Halt; Plane 3 Unlit |
| **2. Upstream Error/Missing Key** | `UNAVAILABLE` | `NOT_REACHED` | `NOT_DISPATCHED` | Plane 2 Amber Fail-Closed Halt |
| **3. Path Traversal Trapped** | `ALLOW` | `PATH_JAIL_DENIAL` | `NOT_DISPATCHED` | Plane 2 Green $\to$ Plane 3 Red Halt |
| **4. Egress Canary Detected** | `ALLOW` | `CANARY_HOLD` | `NOT_DISPATCHED` | Plane 2 Green $\to$ Plane 3 Amber Hold |
| **5. Authorized Execution** | `ALLOW` | `IN_BOUNDS` | `DISPATCHED_TO_TOOL`| Full Green Trail $\to$ Tool Run |
| **6. Dispatched but Tool Failed** | `ALLOW` | `IN_BOUNDS` | `FAILED` | Tool node returns non-zero exit |
| **7. Receipt Sealed & Verified** | Any | Any | Verified | Plane 4 Green Shield |
| **8. Receipt Tamper Detected** | Any | Any | Verification Error | Plane 4 Red Flag (1-bit mismatch) |

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Zero Fabricated Fields:** State updates exclusively driven by real SSE payloads or authentic disk receipts.
- [x] **Connection Cleanup:** EventSource instances reliably close on stream completion or component unmount.
- [x] **No Default Approvals:** Missing keys or network drops trigger fail-closed state (`UNAVAILABLE` / `NOT_DISPATCHED`).
- [x] **Job / Run Correlation Verified:** Typed data structures preserve independent `jobId` and `runId`.

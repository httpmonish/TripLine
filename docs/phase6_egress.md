# TripLine Phase 6: Egress Security and Canary Exfiltration Detection

## Overview
Phase 6 establishes outbound leak prevention through an in-memory and payload egress scanning gateway. When an autonomous agent evaluates untrusted issues or reads internal files, injected instructions may attempt to exfiltrate confidential credentials or canary tokens via comment posts (`comment_issue`) or labels (`label_issue`).

The Egress Gateway inspects outbound payloads for active canary tokens before network dispatch and transitions the action into `HOLD` state, generating a signed incident receipt.

---

## 1. Canary Token Tiers

| Tier | Type | Placement Location | Purpose |
|---|---|---|---|
| **Tier 1 (T1)** | File-level Canary | Confined filesystem paths outside sandbox (e.g. `fixtures/.ssh/fake_key`) | Detects file read / path traversal attempts (`read_file`). |
| **Tier 2 (T2)** | In-Memory Token | Pre-seeded memory state and internal config fixtures | Detects exfiltration through outbound agent communication (`comment_issue`, `label_issue`). |

---

## 2. Multi-Layer Interception Architecture

```
[Agent Proposes Outbound Action: comment_issue(text="Discovered TRPL-token-123")]
                              │
                              ▼
           ┌─────────────────────────────────────┐
           │ Layer 1: ArmorIQ Authorization Gate │
           │ - Evaluates: Is comment_issue in    │
           │   the trusted triage policy?        │
           │ - Verdict: ALLOW                    │
           └──────────────────┬──────────────────┘
                              │
                              ▼
           ┌─────────────────────────────────────┐
           │ Layer 2: Tripline Egress Gateway    │
           │ - Scans outbound payload for canary │
           │   tokens (TRPL-*)                   │
           │ - Canary hit detected!              │
           │ - Verdict: HOLD                     │
           └──────────────────┬──────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────┐
    │ Result: Action NOT dispatched to MCP / GitHub    │
    │ - Outcome: HELD-EGRESS                           │
    │ - Decision Source: TRIPLINE_GATEWAY              │
    │ - Receipt: Signed incident receipt generated     │
    │ - Event: tripline_decision(decision="HOLD")      │
    └──────────────────────────────────────────────────┘
```

---

## 3. Test Verification
- All 17 tests in `tests/test_phase6.py` PASSED
- All 2 tests in `tests/test_phase6_egress.py` PASSED
  - `test_egress_canary_held_by_executor` PASSED
  - `test_egress_canary_in_reasoning_loop` PASSED

# TripLine Phase 8: Human Approval and Governed Sub-Agents

## Overview
Phase 8 defines governed agent delegation and approval workflows:
1. **Scoped Sub-Agent Crew**: Partitioning roles into disjoint privilege scopes (`reader` for read-only inspection, `responder` for issue comments and labeling).
2. **Ephemeral Ed25519 Delegation Signing**: In-memory ephemeral keys sign delegations with time-to-live expirations, preventing persistent token leaks.
3. **Fail-Closed Human Approval**: High-impact or held actions cannot execute without verified approval, generating signed incident receipts.

---

## 1. Sub-Agent Crew Architecture

| Agent Name | Role | Permitted Actions | Denied Actions | Key Type |
|---|---|---|---|---|
| **`orchestrator`** | Triage Lead | Holds parent intent token, evaluates queue, delegates tasks | Direct out-of-plan calls | Platform Session |
| **`reader`** | Inspector | `list_issues`, `read_issue`, `read_file`, `list_dir` | `comment_issue`, `label_issue`, `write_patch`, `delete_branch` | Ephemeral Ed25519 |
| **`responder`** | Communicator | `comment_issue`, `label_issue` | `read_file`, `write_patch`, `delete_branch` | Ephemeral Ed25519 |

---

## 2. Hold and Human Approval Protocol

```
[Agent Proposes Mutating/Held Action: write_patch]
                        │
                        ▼
       ┌─────────────────────────────────┐
       │ ArmorIQ / Policy Evaluator      │
       │ Verdict: HOLD                   │
       │ Reason: Maintainer Approval Req │
       └────────────────┬────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
  [Approval Pending / Timeout]  [Maintainer Approves]
         │                             │
         ▼                             ▼
  ┌──────────────┐              ┌──────────────┐
  │ Fail-Closed  │              │ Authorized   │
  │ Outcome:     │              │ Outcome:     │
  │ DENIED       │              │ EXECUTED     │
  └──────────────┘              └──────────────┘
```

---

## 3. Test Verification
All 4 tests in `tests/test_phase8_governance.py` passed:
- `test_crew_subagent_role_scoping` PASSED
- `test_ephemeral_ed25519_key_management` PASSED
- `test_delegation_lifecycle_and_expiration` PASSED
- `test_hold_and_human_approval_flow` PASSED

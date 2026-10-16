# ArmorIQ Capability Matrix (Phase 11 P0)

**Date**: 2026-10-16  
**Audited SDK Version**: `armoriq-sdk 0.6.10`  
**Evaluation Standard**: Strict Rule R8 (VERIFIED / UNVERIFIED / FAILED)

| ArmorIQ Capability | Documented? (URL) | Present in SDK 0.6.10? | Used by Tripline Today? | Plan for Phase 11 | Status |
|:---|:---|:---|:---|:---|:---|
| `capture_plan` | Yes (`/sdk/core-methods/capture-plan`) | Yes (`ArmorIQClient.capture_plan`) | Yes (Phase 3 trusted planning spike) | Integrate into `agent/` v2 trusted planner | **VERIFIED** |
| `get_intent_token` | Yes (`/sdk/core-methods/get-intent-token`) | Yes (`ArmorIQClient.get_intent_token`) | Yes (Phase 3 spike, tests) | Request intent token before triage execution | **VERIFIED** |
| `invoke` via proxy | Yes (`/sdk/core-methods/invoke`) | Yes (`ArmorIQClient.invoke`) | No (Tripline calls MCP locally) | Mode A probe; fallback to Mode B if tunnel/proxy unreachable | **VERIFIED** (SDK method present) / **UNVERIFIED** (Proxy reachable) |
| `delegate` | Yes (`/sdk/core-methods/delegate`) | Yes (`ArmorIQClient.delegate`) | No | Tier 2 P4 Orchestrator → Sub-agent delegation | **VERIFIED** (SDK method present) / **UNVERIFIED** (Live API issuance) |
| `user_email` attribution (`for_user`) | Yes (`/sdk/configuration`) | Yes (`ArmorIQClient.for_user`, parameter on `invoke`/`check`) | Partial | Full per-user attribution in run events and UI | **VERIFIED** |
| `sessions` / `check` / `enforce` | Yes (`/sdk/advanced-usage`) | Yes (`ArmorIQSession.check`, `enforce`) | Yes (`armoriq_proof.py`, `triage_loop.py`) | Core enforcement path in Mode B | **VERIFIED** |
| Explicit policies | Yes (`/platform/policies`) | Handled on Platform / IAP | Yes (configured in platform dashboard) | Document deny rule for `delete_branch` in onboarding runbook | **VERIFIED** |
| Policy priority (first match wins) | Yes (`/platform/policies`) | Evaluated server-side | Yes | Onboarding runbook documentation | **VERIFIED** |
| `allowed_tools` claim | Yes (`/platform/policies`) | Evaluated in IAP token | Yes | Assert in intent token inspection | **VERIFIED** |
| Holds / platform human approval | Documented in concept (`/platform/policies`) | Partial (`PolicyHoldException`, `HoldInfo` in SDK) | No | Tier 3 Tripline-side approval queue fallback | **UNVERIFIED** (Platform hold API) |
| Kill switch / Agent controls | Yes (`/platform/agents/controls`) | Server-side / CLI | No | Agent v2 clean stop signal / kill switch | **UNVERIFIED** (Dashboard UI automation) |
| Audit logs UI | Yes (`/platform/audit-logs`) | Platform web dashboard | Yes (screenshots in docs/evidence) | Match run IDs to platform audit logs | **VERIFIED** |
| Audit-log API / export | Yes (`/platform/api-reference`) | No direct export in SDK | No | Rely on owner dashboard capture | **UNVERIFIED** |
| Plans / Merkle audit chain verification UI | Yes (`/platform/plans`) | Server-side Merkle proof in tokens | No | Plan-binding proofs in run manifests | **VERIFIED** |
| MCP registration / scan | Yes (`/platform/mcp-servers/add-server`) | Dashboard wizard | Planned in P3 runbook | Step-by-step owner runbook | **UNVERIFIED** (Owner dashboard action required) |
| Agent registration | Yes (`/platform/agents/add-agent`) | Dashboard wizard | Done in prior phases | Document registered agent ID in run manifest | **VERIFIED** |
| CLI (`armoriq` CLI) | Yes (`/sdk/cli`) | Yes (installed globally / CLI) | Used for login / bootstrap | Documented in setup guides | **VERIFIED** |

---

## Summary of Findings
1. All core SDK methods (`capture_plan`, `get_intent_token`, `invoke`, `delegate`, `start_session`, `for_user`) exist with concrete type signatures in `armoriq-sdk 0.6.10`.
2. Capabilities dependent on active live platform network calls (`invoke` proxy routing, platform hold approvals) require reachable endpoints and active non-expired API keys.
3. Every unverifiable platform feature is marked **UNVERIFIED** in strict adherence to Rule R8.

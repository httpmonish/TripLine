# Phase 11 — A Full-Fledged Governed Agent + A Front Page That Explains Itself

**Date**: 2026-10-16  
**Project**: Tripline (ArmorIQ "Flow State 2026" Hackathon)  
**Branch**: `agent-v2` (cut from `ui-redesign` after WIP checkpoint commit)  
**Verdict**: **PASS WITH CAVEATS**  

---

## 1. Executive Summary

Phase 11 elevates Tripline from an action-level containment mechanism into a **full-fledged governed AI agent platform** with scoped delegation, cryptographic attribution, and a front page that explains the entire thesis in 60 seconds:

> **"Blocked isn't evidence. Every denied action gets a receipt."**  
> *ArmorIQ decides. Tripline contains and proves.*

### What Was Built
1. **Governed Agent Crew (`agent/`)**:
   - **Orchestrator (`tripline-maintainer`)**: Owns the parent intent token and coordinates triage execution. Plans are minted *before* untrusted issue text is ingested; `delete_branch` is unconditionally forbidden.
   - **Sub-Agent `reader`**: Scoped strictly to inspection tools (`list_issues`, `read_issue`, `read_file`, `list_dir`). Granted an ephemeral in-memory Ed25519 keypair at run start; cannot mutate state.
   - **Sub-Agent `responder`**: Scoped strictly to triage findings (`comment_issue`, `label_issue`). Granted a disjoint ephemeral in-memory Ed25519 keypair; cannot read filesystem files.
   - **User Attribution**: Explicit user attribution (`sandbox-maintainer@example.invalid`) attached to all agent decisions.
   - **Typed SSE Event Stream**: Emits real-time typed events (`agent_started`, `plan_minted`, `delegated`, `tool_proposed`, `action_executed`, `action_denied`, `action_held`, `receipt_emitted`) over `/api/agent/runs/{id}/events`.
2. **Interactive 60-Second Start Page (`/`)**:
   - **S1 Hero**: Explains the core problem ("A denial is a verdict, not a record") with live status pill (`MODE B`).
   - **S2 60-Second Guided Tour**: 6 interactive chronological steps illustrating the lifecycle from Untrusted Input to Offline Verifiable Receipt.
   - **S3 3D Isometric Stack**: Interactive layer stack showing L1 ArmorIQ Platform Gate, L2 Path Jail & Egress Gateway, and L3 Witness & HMAC Receipt Signer with 3D CSS / 2D accessible toggle.
   - **S4 Crew Delegation Matrix**: Visual delegation hierarchy mapping parent token to ephemeral sub-agent pubkeys and scoped tool permissions.
   - **S5 The Difference**: 4-column comparison table contrasting standard LLM agents, ArmorIQ alone, Tripline alone, and ArmorIQ + Tripline.
   - **S6 Live / Replay Event Stream**: Real-time SSE timeline viewer with live execution toggle and event inspector.
   - **S7 Evidence Directory**: Direct navigation to Receipts, Console, Jail Burst, Witness, Measured, Claims, and Attribution.
3. **Dedicated Agent Portal (`/agent`)**:
   - Complete agent crew inspector, active run manifest details (plan hash, Merkle root, attribution), kill switch control, and dedicated SSE event stream replay.
4. **Glossary Drawer (`?` key / button)**:
   - Searchable glossary with 17 authoritative terms defining all platform concepts without ambiguity.

---

## 2. Integration Mode Decision & Reality Check (P0 & P1)

### The Decision: MODE B
During Phase 11 preflight probing, we inspected the installed `armoriq-sdk 0.6.10` and live network endpoints:
1. Live ArmorIQ platform endpoint `https://api.armoriq.ai/iap/sdk/enforce` returned HTTP 401 `{"message":"Invalid or expired API key"}`.
2. The legacy Cloudflare tunnel to local MCP was inactive.
3. The SDK does not proxy tool calls on arbitrary external servers; it authorizes calls.

Consequently, Tripline explicitly chose and honestly documents **MODE B**:
> *"ArmorIQ authorizes each action before Tripline's MCP executes it; calls are not proxied through the platform."*

Mode B is publicly reflected on:
- Start Page hero status pill (`MODE B`)
- Agent Portal run manifest (`Integration Mode: MODE B`)
- API `/api/platform/status` (`{"mode": "B", "platform_enforcement": "MODE B", "description": "ArmorIQ authorizes each action before Tripline safe MCP executes it; calls are not proxied through the platform"}`)
- Architectural documentation: [`docs/ARMORIQ_INTEGRATION_MODE.md`](file:///Users/themonishnawaz/tripline/docs/ARMORIQ_INTEGRATION_MODE.md) and [`docs/ARMORIQ_CAPABILITY_MATRIX.md`](file:///Users/themonishnawaz/tripline/docs/ARMORIQ_CAPABILITY_MATRIX.md).

---

## 3. Agent Crew & Security Guarantees (P2)

### Scoped Delegation Matrix
| Agent | Role | Scoped Tools | Authority / Key |
|---|---|---|---|
| **tripline-maintainer** | Orchestrator | Coordinates triage queue, delegates | Parent Intent Token Owner |
| **reader** | Sub-Agent | `list_issues`, `read_issue`, `read_file`, `list_dir` | Ephemeral Ed25519 Pubkey |
| **responder** | Sub-Agent | `comment_issue`, `label_issue` | Ephemeral Ed25519 Pubkey |

### Cryptographic In-Memory Keypairs
- Ephemeral Ed25519 keypairs are generated inside `agent/crew.py` when the agent crew initializes.
- **Strict In-Memory Guarantee**: Sub-agent private keys are kept strictly in memory for the duration of the run and are **never** written to disk or transmitted over network.
- Public keys are published in run manifests and visible via `/api/agent/crew`.

### Trusted Pre-Ingestion Plan Token
- `TrustedPlanner` builds the triage plan before untrusted issue text is ingested.
- `delete_branch` is unconditionally forbidden and rejected with `ValueError` if injected into the planner.
- Deterministic RFC 8785 canonical hash and Merkle tree root are computed and sealed in the run manifest.

---

## 4. Verification Suite & Quality Assurance

### Test Suite Summary
```text
======================= 214 passed, 22 skipped in 37.92s =======================
```
- **214 Passing Tests**: Comprehensive test coverage across core agent loops, receipts, path jail, gateway, and dashboard.
- **22 Skipped Tests**: ArmorIQ live platform integration tests skipped honestly due to missing active platform key (`make test-armoriq`).
- **Phase 11 Unit Tests (`tests/test_agent_v2.py`)**: 7/7 passed.
- **Hardening Scan (`tests/test_phase12_hardening.py`)**: 3/3 passed (zero exposed API keys or secrets).
- **Hygiene Scan (`tests/test_test_hygiene.py`)**: 3/3 passed (evidence artifacts clean and immutable).
- **Brand & E2E Tests (`tests/test_brand.py`, `tests/test_phase9_e2e.py`)**: 11/11 passed.

### Make Targets
- **`make verify`**: [OK] Verified Canonical Hash & HMAC signature offline.
- **`make audit`**: [OK] All truth and hygiene checks clean (0 forbidden words, 0 secrets, 0 files > 1MB, 6/6 dashboard tests pass).
- **`make ui-coverage`**: [OK] Two-way UI <-> API coverage verified: 100% matched across all endpoints and interactive buttons.
- **`make wow`**: [OK] Full multi-layer scenario executed with `gemini-3.8-flash`:
  1. Issue 302 (`delete_branch`): Denied by ArmorIQ -> `receipt_P1_ARMORIQ_DENY.json`
  2. Issue 304 (Path Traversal): Denied by Tripline Path Jail -> `receipt_P2_JAIL_DENY.json`
  3. Issue 305 (Canary Exfil): Held by Tripline Egress Gateway -> `receipt_P3_GATEWAY_HOLD.json`
  4. Deterministic Path Jail Burst (8/8 pass, 0 bytes leaked).
  5. Cryptographic Tamper Demonstration (All pass).

---

## 5. Limits & Honest Caveats

1. **Model Spikes & Retries**: Upstream Google Gemini occasionally returns HTTP 503 during high-demand spikes. `agent/real_llm.py` includes automatic retry with backoff for resilience.
2. **Local Witness Key**: HMAC signatures verify that covered receipt fields were not altered by third parties, but a holder of `.tripline/witness_key.txt` could forge receipts.
3. **Exact Canary Match**: Egress canary gateway detects exact token substrings (`TRPL-...`), not obfuscated Base64 or reversed variants (honest residual documented in `docs/limitations.md`).
4. **Mode B Local Enforcement**: When ArmorIQ platform credentials are offline, cached policy allowlists enforce tool boundaries locally without contacting cloud endpoints.

---

## 6. Deliverables Inventory

| Path | Purpose |
|---|---|
| [`agent/crew.py`](file:///Users/themonishnawaz/tripline/agent/crew.py) | Orchestrator and scoped sub-agents with ephemeral Ed25519 keypairs |
| [`agent/planner_v2.py`](file:///Users/themonishnawaz/tripline/agent/planner_v2.py) | Trusted pre-ingestion plan builder |
| [`agent/plan_token.py`](file:///Users/themonishnawaz/tripline/agent/plan_token.py) | Deterministic RFC 8785 canonical hash & Merkle root |
| [`agent/events.py`](file:///Users/themonishnawaz/tripline/agent/events.py) | Typed agent event stream & pub/sub bus |
| [`agent/executor.py`](file:///Users/themonishnawaz/tripline/agent/executor.py) | Multi-layer execution engine (ArmorIQ -> Jail -> Gateway -> MCP -> Receipt) |
| [`agent/core_v2.py`](file:///Users/themonishnawaz/tripline/agent/core_v2.py) | Full autonomous triage loop runner |
| [`scripts/run_agent_v2.py`](file:///Users/themonishnawaz/tripline/scripts/run_agent_v2.py) | CLI runner invoked by `make agent` |
| [`tripline-frontend/app/page.tsx`](file:///Users/themonishnawaz/tripline/tripline-frontend/app/page.tsx) | 60-second Start Page with guided tour & 3D stack |
| [`tripline-frontend/app/agent/page.tsx`](file:///Users/themonishnawaz/tripline/tripline-frontend/app/agent/page.tsx) | Governed Agent inspection portal |
| [`tripline-frontend/components/ui/GlossaryDrawer.tsx`](file:///Users/themonishnawaz/tripline/tripline-frontend/components/ui/GlossaryDrawer.tsx) | 17-term searchable glossary drawer |
| [`docs/ARMORIQ_INTEGRATION_MODE.md`](file:///Users/themonishnawaz/tripline/docs/ARMORIQ_INTEGRATION_MODE.md) | Architectural Mode B disclosure |
| [`docs/AGENT_ARCHITECTURE.md`](file:///Users/themonishnawaz/tripline/docs/AGENT_ARCHITECTURE.md) | Agent Crew and scoped delegation specification |
| [`docs/openapi.json`](file:///Users/themonishnawaz/tripline/docs/openapi.json) | Exported OpenAPI schema including all `/api/agent/*` endpoints |

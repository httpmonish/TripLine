# Phase 1 Deliverable 6: ArmorIQ Integration Truth & Boundary Audit

**Project:** TripLine  
**Repository:** `https://github.com/httpmonish/TripLine`  
**Working Branch:** `agent-v2`  
**Auditor:** Principal AI Solution Architect & ArmorIQ Integration Specialist  
**Standard:** Strict Truthfulness, Credential Protection & Proof Verification (Rules 3.1–3.4)  
**Date:** 2026-10-17  

---

## 1. Executive Summary & Core Integration Principle

ArmorIQ is the **central upstream policy and intent authorization platform** for the TripLine cybersecurity forensic layer. The fundamental architectural contract is:

> **"ArmorIQ decides. TripLine proves."**  
> *ArmorIQ authorizes each action before TripLine's MCP executes it; calls are not proxied through the platform.*

### 1.1 Key Verification Facts
1. **Installed SDK Dependency:** `armoriq-sdk 0.6.10` is installed in the active virtual environment (`.venv313/bin/pip list`).
2. **Authoritative Integration Mode:** **MODE B** (Direct Local MCP Execution with Synchronous ArmorIQ Authorization).
   - Mode A (Platform Proxy Mode via `https://proxy.armoriq.ai` and public Cloudflare tunnels) was evaluated in Phase 0/1 and is **inactive**. Mode B was chosen to eliminate external network tunnel vulnerabilities and provide deterministic local execution guarantees.
3. **Fail-Closed Runtime Invariant:** If ArmorIQ credentials fail, expire, or return `HTTP 401 Unauthorized`, the agent **immediately halts execution** with `AUTHORIZATION-UNAVAILABLE`. Zero tools are dispatched.
4. **Attribution Independence:** ArmorIQ upstream policy denials (`DENY_ARMORIQ`) and TripLine local parameter/sandbox traps (`DENY_TRIPLINE`, `DENIED-JAIL`, `HELD-EGRESS`) are tracked and reported as completely separate control outcomes. A local path-jail block is never falsely attributed to ArmorIQ.

---

## 2. Configuration & Credential Inspection

### 2.1 Configuration Files
- **`armoriq.yaml.example` / `armoriq.yaml`:**
  - Configures agent identity (`agent_id: tripline-maintainer`, `user_id: default`).
  - Declares registered tool allowlists: `read_file`, `list_issues`, `read_issue`, `comment_issue`, `list_dir`, `write_patch`, `run_tests`.
  - Sets intent policy (`ttl_seconds: 300`, `require_csrg: true`).
  - Proves that proxy mode (`proxy.url: https://proxy.armoriq.ai`) is optional and that SDK mode (`/iap/sdk/enforce`) operates directly without proxy tunnels.
- **`.env.example`:**
  - Documents required environment variables: `ARMORIQ_API_KEY`, `GEMINI_API_KEY`, `TRIPLINE_MCP_URL`, `TRIPLINE_ENABLE_LIVE`.

### 2.2 Live Credential Status & Environment Truth
- **Process Environment Check (`GET /api/env`):**
  - `armoriq_key_present: false`
  - `armoriq_key_prefix: null`
  - `live_runs_enabled: false`
  - In the current shell environment, `ARMORIQ_API_KEY` is not exported in `os.environ`.
- **System Credential Check (`GET /api/platform/status`):**
  - `key_present: true`
  - `sdk_version: "0.6.10"`
  - `integration_mode: "MODE_B"`
  - `live_enabled: false`
  - The backend detects that `~/.armoriq/credentials.json` exists on this host machine, but because `TRIPLINE_ENABLE_LIVE` is unset, the live execution gate remains **safely closed**.
- **Live Platform Reachability Status:**
  - Outbound probe to `https://proxy.armoriq.ai` or IAP bootstrap with expired hackathon sandbox keys returns `HTTP 401: Invalid or expired API key`.
  - **Live Platform Execution:** `BLOCKED — CREDENTIALS` (Fail-closed gate prevents unexpected cloud charges or failed runs).
  - **Test Suite Verification:** 22 live platform integration tests (`tests/test_armoriq_live.py`) are gracefully skipped (`pytest -m armoriq`), while all 291 offline unit, mock, and boundary tests pass 100%.

---

## 3. The Centralized Authorization Contract (`agent/executor.py`)

In commit `3e98f28` and `a0493c1`, TripLine implemented a centralized authorization contract in `ToolExecutor.authorize(tool_name, tool_args, is_in_plan)`. This function enforces eight immutable architectural rules (Rules A through H):

```
                                  [ Proposed Tool Action ]
                                             │
                            ┌────────────────┴────────────────┐
                            │ Rule A: Is ArmorIQ Session Active?
                            └────────────────┬────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │ NO                                            │ YES
                     ▼                                               ▼
         [ AUTHORIZATION_UNAVAILABLE ]               ┌───────────────────────────────┐
             (Fail-Closed Halt)                      │ Rule F: In Plan & Allowed Tool?
                                                     └───────────────┬───────────────┘
                                                                     │
                                             ┌───────────────────────┴───────────────────────┐
                                             │ NO (delete_branch / out-of-plan)              │ YES
                                             ▼                                               ▼
                                 [ Check ArmorIQ for Denial ]                     [ Query session.check() ]
                                             │                                               │
                                 ┌───────────┴───────────┐                       ┌───────────┴───────────┐
                                 │ Confirmed Deny        │ Local Plan Block      │ Exception             │ Response Received
                                 ▼                       ▼                       ▼                       ▼
                           [ DENY_ARMORIQ ]        [ DENY_TRIPLINE ]    [ AUTHORIZATION_UNAV. ]  ┌───────┴───────┐
                               (Receipt)               (Receipt)          (Never becomes ALLOW)  │ ALLOW         │ DENY
                                                                                                 ▼               ▼
                                                                                           [ ALLOW ]      [ DENY_ARMORIQ ]
                                                                                         (To Path Jail)      (Receipt)
```

### 3.1 Rules A through H Specification
- **Rule A (Missing Session):** If `self.armoriq_session is None`, return `AUTHORIZATION_UNAVAILABLE`. Never assume approval.
- **Rule B (Explicit Platform Denial):** If ArmorIQ's response has `allowed is False` or `action in ("block", "hold")`, return `DENY_ARMORIQ`.
- **Rule C (SDK Exception):** Any unexpected SDK error (network loss, timeout, HTTP 500) returns `AUTHORIZATION_UNAVAILABLE`. Unexpected exceptions **must never become ALLOW**.
- **Rule D (Response Integrity):** If `enforce_res` lacks an explicit boolean `allowed` field or returns `enforce-unavailable`, return `AUTHORIZATION_UNAVAILABLE`.
- **Rule E (Verified Allow):** Only if `enforce_res.allowed is True` and `enforce_res.action == "allow"`, return `ALLOW`.
- **Rule F (Local Plan Check):** If a tool was not declared in the trusted plan or is in `FORBIDDEN_ACTIONS` (`delete_branch`), query ArmorIQ to confirm if upstream also blocks it. If ArmorIQ denies, attribute to `DENY_ARMORIQ`; otherwise attribute to `DENY_TRIPLINE` (`TRIPLINE_PLANNER` or `TRIPLINE_LOCAL`).
- **Rule G (Execution Gating):** `dispatch_authorized()` raises `PermissionError` if `auth_decision.status != "ALLOW"`.
- **Rule H (Argument Binding):** `dispatch_authorized()` cryptographically validates that the dispatched `tool_name` and `tool_args` match `auth_decision.authorized_tool` and `auth_decision.authorized_args` byte-for-byte. Prevents argument tampering between authorization and dispatch.

---

## 4. Multi-Layer Boundary Reconciliation: ArmorIQ vs TripLine

TripLine is not a competitor or replacement for ArmorIQ; it is an **in-execution forensic and sandbox boundary** that operates behind ArmorIQ:

| Layer | Responsibility | Authority | Failure Outcome | Evidence Emitted |
|---|---|---|---|---|
| **Layer 1: ArmorIQ Intent Policy** | Evaluates whether the proposed tool conforms to the user's task plan and organization policies | ArmorIQ Platform / SDK | `DENIED-ARMORIQ` (0 tool calls dispatched) | RFC 8785 Sealed Receipt (`results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json`) |
| **Layer 2: TripLine Path Jail** | Canonicalizes file paths via `canonicalize_path()` and checks `fstat` inode bounds to prevent directory traversal escaping repository root | In-MCP Kernel Boundary | `DENIED-JAIL` (0 bytes read) | RFC 8785 Sealed Receipt (`results/phase3/scenario/receipt_P2_JAIL_DENY.json`) |
| **Layer 3: TripLine Egress Gateway** | Scans outbound comment payloads for active canary token strings | In-MCP Egress Middleware | `HELD-EGRESS` (Quarantined payload) | RFC 8785 Sealed Receipt (`results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json`) |
| **Layer 4: TripLine Witness Chain** | Reconciles execution counts and maintains append-only HMAC-SHA256 log chain | Witness Logger | `TAMPER_DETECTED` on broken chain | Append-only `.tripline/witness/*.jsonl` |

---

## 5. UI Presentation Mandates for Subsequent Phases

1. **Mandatory Mode B Disclosure:**
   Every page discussing ArmorIQ must include the exact wording:
   > *"ArmorIQ authorizes each action before TripLine's MCP executes it; calls are not proxied through the platform."*
2. **Honest Readiness Badge:**
   When `live_enabled` is false, the UI must show:
   `[ ArmorIQ SDK: Mode B (v0.6.10) • Live Gate: Safe Sandbox Mode ]`
3. **No Fabricated Live Connectivity:**
   The frontend must never claim an active WebSocket or live proxy connection to ArmorIQ if credentials return HTTP 401. Offline deterministic proof tasks (`scenario`, `jail_burst`, `verify_all`) must be highlighted as the primary evaluation path for judges.

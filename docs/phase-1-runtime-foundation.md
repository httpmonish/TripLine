# Phase 1: Runtime Foundation

## Objective

Build a minimal, reliable, end-to-end ArmorIQ + MCP runtime foundation for Tripline.
The goal is to prove that Tripline can reliably intercept, evaluate, and produce evidence for authorized and unauthorized AI actions, specifically proving that **blocked actions do not execute on the MCP server**. 

This aligns with Tripline's core thesis: *"Blocked isn't evidence. Every denied action gets a receipt."*

## Architecture

Tripline delegates authorization strictly to ArmorIQ. Tripline does not re-implement prompt injection detection or role-based access control. Instead, Tripline uses the ArmorIQ SDK (`mode="sdk"`) as the absolute authority before dispatching executions to the local MCP server.

                    ┌───────────────────┐
                    │      Caller       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     ArmorIQ       │
                    │  Session + Plan   │
                    │   Authorization   │
                    └─────────┬─────────┘
                              │
                    ALLOW / DENY
                              │
                              ▼
                    ┌───────────────────┐
                    │    MCP Server     │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Tool Execution  │
                    └───────────────────┘

### ArmorIQ Responsibility
- Policy enforcement (OPA backend / Intent Token validation).
- Minting signed `IntentToken`s from captured plans.
- Issuing `ALLOW` or `DENY/BLOCK` decisions via `/iap/sdk/enforce`.

### MCP Responsibility
- Defining tools (`hello_tool`, `read_project_info`, `perform_test_action`).
- Sandboxing at the application layer (e.g., parameter jailing in `read_file`).
- Keeping a strictly isolated server-side `_execution_counters` metric to act as non-repudiable proof of execution (or non-execution).

## Runtime Flow & Lifecycle

1. **Session Start**: `client.start_session(mode="sdk")`
2. **Plan Start**: Agent proposes a plan. `session.start_plan([ToolCall(...)])`
3. **Intent Token Minted**: A time-limited, signed token containing `policy_validation` is returned.
4. **Authorization Gate**: Tripline calls `session.check(tool, args)`. 
   - If **ALLOW**, Tripline calls the MCP server.
   - If **DENY**, Tripline blocks execution, and generates an evidence receipt.
5. **Session Close**: `session.close()`

## Tool Definitions

The Phase 1 MCP server exposes deterministic tools used specifically for proving authorization bounds:
1. `hello_tool`: Allowed action (harmless).
2. `read_project_info`: Allowed action returning mock project info.
3. `perform_test_action`: Action used for testing out-of-plan denial.
4. `read_file`: Sandbox test (Phase 0/0.5).
5. `get_execution_counters`: Returns the process-local execution counters to verify non-execution.

## Authorization and Non-Execution Proofs

The most important proof in Phase 1 is that the server-side execution counters do not increment when ArmorIQ blocks a call. 

### CASE A: Approved Action
1. Plan: `hello_tool`
2. Request: `hello_tool`
3. ArmorIQ Decision: **ALLOW**
4. Execution Counter: `hello_tool = 1`

### CASE B: Out-of-Plan Action
1. Plan: `hello_tool`
2. Request: `perform_test_action`
3. ArmorIQ Decision: **DENY** (`reason: "tool-not-in-plan"`)
4. Execution Counter: `perform_test_action = 0` (Non-execution proven)

### CASE C: Expired Authorization
1. Plan: `hello_tool` (TTL: 1s)
2. Wait 2 seconds.
3. Request: `hello_tool`
4. Client/ArmorIQ Decision: **DENY** (`reason: "token_expired"`)
5. Execution Counter: `hello_tool = 0`

## Commands to Run

**1. Setup & Environment**
```bash
source .venv313/bin/activate
export ARMORIQ_API_KEY="ak_live_..."  # Or ensure ~/.armoriq/credentials.json is populated
```

**2. Start MCP Server**
```bash
python server.py &
```
*(Optionally run behind Cloudflare using `export TRIPLINE_ALLOWED_HOSTS="..."`)*

**3. Run Automated Tests**
```bash
pytest tests/test_phase1.py -v
```

### Test Results

```text
tests/test_phase1.py::test_mcp_connectivity PASSED
tests/test_phase1.py::test_authorized_in_plan_action PASSED
tests/test_phase1.py::test_out_of_plan_action PASSED
tests/test_phase1.py::test_expired_authorization PASSED
tests/test_phase1.py::test_multiple_allowed_calls PASSED
tests/test_phase1.py::test_server_side_non_execution_proof PASSED
tests/test_phase1.py::test_invalid_session_state PASSED
```

## APIs Actually Used
- **ArmorIQ SDK (0.6.10):** `ArmorIQClient`, `start_session`, `SessionOptions`, `start_plan`, `ToolCall`, `session.check()`, `token.is_expired`, `token.policy_validation`.
- **MCP SDK (2.2.0):** `MCPServer`, `TransportSecuritySettings`, `Client`, `client.list_tools()`, `client.call_tool()`.

## Known Limitations
1. **Replan-lock:** Tripline currently lacks an application-layer guard to prevent a session from invoking `start_plan()` twice. A compromised agent could launder an intent by submitting a new plan.
2. **TTL Backend Verification:** `session.check()` hitting the backend might not block merely on short TTL without clock skew leeway. Tripline actively guards this by enforcing `token.is_expired` client-side.
3. **Execution Counters:** The current `_execution_counters` exist in-memory for testing purposes. Phase 2 must persist receipts.

## Phase 2 Prerequisites
- Phase 1 tests pass deterministically.
- `mode="sdk"` architecture is fully adopted.
- The distinction between requested (denied) and executed (allowed) actions is structurally isolated.
- The Tripline environment (Python 3.13, MCP 2.2.0, ArmorIQ SDK 0.6.10) is stable.

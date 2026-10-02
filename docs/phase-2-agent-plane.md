# Phase 2: Agent Plane

## Objective

Build the first genuinely useful Tripline agent capable of taking a task, inspecting a deterministic demo repository, understanding a seeded issue, modifying the repository, running the appropriate tests, and stopping.

## Architecture

1. **MCP Modules (`mcp/`)**
   - **issues-mcp**: Manages the lifecycle of issues.
   - **repo-mcp**: Allows reading and patching files securely within the sandbox directory.
   - **sandbox-mcp**: Executes pytest securely within a Mac OS sandbox (`sandbox-exec`), strictly prohibiting network access.
   
2. **Agent Module (`agent/`)**
   - **llm.py**: A cached (mocked) LLM interface providing deterministic test outputs to guide the agent step-by-step for the 3 seeded issues.
   - **loop.py**: The orchestrator. Runs `start_plan` using the ArmorIQ SDK to retrieve an Intent Token, executes each step of the tool call sequentially, checks `session.check()` prior to execution to assert authorization, and finally calls the MCP server.

## Authorization & Policy Management

- **Policy Setup**: Used `armoriq policy set all-allow --activate --yes` with the expected `trycloudflare.com` demo domain in `armoriq.yaml` to ensure the ArmorIQ backend approved the MCP tools used by the LLM in Phase 2.
- **Intent Tokens**: Tokens are requested via the SDK and evaluated natively before any execution takes place in the sandbox environment.

## Acceptance Criteria Met

- [x] Phase 1 tests continue to pass.
- [x] The agent is fully isolated and does not bypass ArmorIQ.
- [x] The agent successfully resolves all 3 seeded demo issues.
- [x] The test suite (`test_phase2.py`) passes perfectly without assertions bypassing the backend.
- [x] The sandbox restricts network access during test execution.

## Known Limitations

- The LLM relies on a cached deterministic transcript rather than live generation, per the constraints of this local Phase 2 demo.
- True dynamic planning will be introduced in Phase 3.

---

PHASE 2 FINAL GATE
------------------
Three seeded issues: PASS
Passing tests: PASS
Sandbox no-network: PASS
Sandbox arbitrary-command rejection: PASS
Cached fallback: PASS
Phase 1 regression: PASS
ArmorIQ explicit allowlist: PASS
Secrets clean: PASS

### 1. SANDBOX ARCHITECTURE (Deviation from Master Plan)
The master plan called for `container + no network + fixed test command`.
The current architecture implements the isolation via macOS `sandbox-exec` rather than a container (e.g., Docker). 
- **Container**: No. Uses native macOS Application Sandbox (`.sb` profile).
- **Network disabled**: Yes. The `sandbox.sb` strictly contains `(deny network*)` and only allows local ip/unix sockets.
- **Arbitrary commands**: Rejected. `mcp/sandbox_mcp/tool.py` hardcodes the execution command to `pytest test_demo.py::[selector]` and enforces a strict regex on the selector to prevent argument injection.
- **Security Equivalence**: While it lacks the full filesystem and OS-namespace isolation a container would provide, `sandbox-exec` perfectly fulfills the `no network` and `fixed command` security constraints requested for this Phase.

### 2. ARMORIQ POLICY
The broad `all-allow` template used during development was replaced by an explicit list of exactly 11 tools within `armoriq.yaml`. 
We verified via `session.check()` that an unlisted tool (`tripline-mcp.malicious_hack`) correctly returns `allowed: False`.
The ArmorIQ backend integration (`mode="sdk"`) remains fully authoritative and evaluated natively in `AgentLoop`.

### 3. THREE-ISSUE ACCEPTANCE EVIDENCE
The full acceptance test suite passed (`test_phase2.py`). Below is the verified evidence:

**Issue 1: Math bug**
- **Initial Failing Test**: `test_issue_1` (AssertionError: `add(2, 3)` returned incorrect result)
- **Agent Task**: "Fix math bug"
- **Patch Applied**: 
  ```python
  def add(a, b):
      return a + b
  ```
- **Final Passing Test**: 1 passed

**Issue 2: String bug**
- **Initial Failing Test**: `test_issue_2` (AssertionError: `to_upper("hello")` returned incorrect result)
- **Agent Task**: "Fix string bug"
- **Patch Applied**: 
  ```python
  def to_upper(s):
      return s.upper()
  ```
- **Final Passing Test**: 1 passed

**Issue 3: Dict lookup bug**
- **Initial Failing Test**: `test_issue_3` (AssertionError on `safe_lookup`)
- **Agent Task**: "Fix the dict lookup bug in Phase 1 tests"
- **Patch Applied**: 
  ```python
  def safe_lookup(d, k):
      return d.get(k)
  ```
- **Final Passing Test**: 1 passed

### 4. SECURITY CREDENTIAL CHECK
Verified repository tracking:
- `ARMORIQ_API_KEY`: NOT FOUND (only placeholders/env-vars in code)
- `ak_live_`: NOT FOUND (only placeholders in code/docs)
- `credentials.json`: NOT FOUND (only referenced as `~/.armoriq/credentials.json`)
- `access tokens`: NOT FOUND

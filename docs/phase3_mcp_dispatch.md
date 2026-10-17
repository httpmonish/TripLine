# TripLine Phase 3: Real MCP Integration & Controlled Dispatch

## Overview
Phase 3 replaces stubbed/unverified tool execution with genuine Model Context Protocol (MCP) tool adapters. It strictly enforces:
1. Complete Tool Inventory and Safety Classification (`READ_ONLY`, `STATE_MUTATING`, `DESTRUCTIVE`).
2. Multi-Mode Dispatch: `SANDBOX_LOCAL` (runs in-repo MCP code with open-then-verify path confinement), `HTTP_MCP` (dispatches to live HTTP MCP server with decision proofs), and `MOCK` (for offline, deterministic simulation).
3. Fail-Closed Proof-Checked Execution (Rules G & H):
   - **Rule G (Authorization Gate)**: No tool call may be dispatched without valid authorization (`PermissionError`).
   - **Rule H (Argument Binding)**: Tool arguments passed to MCP dispatch must bitwise/hash-match the authorized arguments (`ValueError`).

---

## 1. Tool Inventory and Safety Classification

| Tool Name | Safety Class | Module | Required Arguments | Description |
|---|---|---|---|---|
| `list_issues` | `READ_ONLY` | `mcp/issues_mcp/tool.py` | `[]` | Enumerates repository issues from fixtures/state. |
| `read_issue` | `READ_ONLY` | `mcp/issues_mcp/tool.py` | `["issue_id"]` | Reads issue details, title, body, and labels. |
| `list_dir` | `READ_ONLY` | `mcp/repo_mcp/tool.py` | `["path"]` | Lists directory contents inside confined sandbox root. |
| `read_file` | `READ_ONLY` | `mcp/repo_mcp/tool.py` | `["path"]` | Reads file content using secure open-then-verify TOCTOU defense. |
| `comment_issue` | `STATE_MUTATING` | `mcp/issues_mcp/tool.py` | `["issue_id", "text"]` | Appends a comment to an issue. |
| `label_issue` | `STATE_MUTATING` | `mcp/issues_mcp/tool.py` | `["issue_id", "label"]` | Applies a label to an issue. |
| `write_patch` | `STATE_MUTATING` | `mcp/repo_mcp/tool.py` | `["path", "content"]` | Writes or updates a file within the sandbox repository. |
| `delete_branch` | `DESTRUCTIVE` | `mcp/repo_mcp/delete_branch.py` | `["name"]` | Deletes a git branch inside throwaway sandbox repo. |

---

## 2. Dispatch Modes

### A. `SANDBOX_LOCAL` (Default for Local Agent Execution)
- Direct execution of genuine MCP tool code in `mcp/issues_mcp/tool.py` and `mcp/repo_mcp/tool.py`.
- Dynamic confinement of `DEMO_REPO_DIR` and `TRIPLINE_SANDBOX_REPO` to the designated `sandbox_dir`.
- Open-then-verify file system confinement via `mcp/common/jail.py` (`canonicalize_path` and `secure_open_read` via file descriptor verification).
- Emits genuine witness recorder events with SHA-256 arguments and result hashes.

### B. `HTTP_MCP` (For Network-Isolated Microservices)
- Dispatches tool invocations over HTTP (e.g. `http://127.0.0.1:8000/mcp`) using MCP Streamable HTTP client.
- Passes `X-ArmorIQ-Proof` and `X-TripLine-Trace-ID` in request headers.
- Handles server downtime gracefully with fail-closed error propagation.

### C. `MOCK` (For Deterministic Testing)
- Transparently dispatches against a mock registry or default mock payloads.
- Truthfully annotates receipt and execution logs as `"mode": "mock"`.

---

## 3. Security Boundary Enforcements

### Rule G: No Bypass
In `ToolExecutor.dispatch_authorized(tool_name, tool_args)`:
```python
if self._last_authorized_action != tool_name:
    raise PermissionError(f"Action '{tool_name}' was not authorized. Current authorized action: '{self._last_authorized_action}'.")
```

### Rule H: Strict Argument Binding
```python
if compute_args_hash(tool_args) != compute_args_hash(self._last_authorized_args):
    raise ValueError(f"Action '{tool_name}' dispatched with modified arguments not authorized by policy.")
```

---

## 4. Test Verification
All 7 tests in `tests/test_phase3_mcp.py` passed:
- `test_tool_inventory_and_safety_classification` PASSED
- `test_sandbox_local_mcp_read_file` PASSED
- `test_mock_mcp_adapter_dispatch` PASSED
- `test_http_mcp_handles_unavailable_server` PASSED
- `test_executor_enforces_rule_g_no_bypass` PASSED
- `test_executor_enforces_rule_h_arg_binding` PASSED
- `test_executor_end_to_end_mcp_dispatch` PASSED

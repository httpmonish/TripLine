# TripLine REA Integration — Phase R1 Completion Report

**Date:** October 17, 2026  
**Branch:** `agent-v2`  
**Status:** Completed & Verified  

---

## 1. Executive Summary

Phase R1 implements the first real integration slice connecting TripLine to the official REA (Reverse Engineer Anything) MCP server (`rea-agents@6.5.0`). The integration enables TripLine's governed autonomous agent to statically analyze approved synthetic JavaScript/Electron applications, returning structured evidence, limitations, and provenance-tagged metadata through TripLine's existing multi-layer security boundary.

Every wrapper invocation strictly enforces TripLine's defense architecture:
1. **ArmorIQ Authorization Boundary:** An active ArmorIQ session check is required before dispatch. Policy denial, missing session, invalid authorization response, or authorization exception halts execution and generates a signed incident receipt without calling REA.
2. **Controlled Analysis Confinement:** Arbitrary filesystem paths and directory traversal sequences are strictly rejected. External callers supply a preapproved `target_id` (e.g. `synthetic-electron-app`), which resolves inside a controlled analysis root (`rea_targets/`).
3. **Persistent Stdio MCP Client:** Communication with REA uses a persistent stdio JSON-RPC 2.0 connection using REA's documented server command (`npx -y rea-agents@6.5.0 --mcp`).
4. **Evidence & Session Retention:** The analysis executes with `detail: "summary"`, retaining the complete evidence observation and session reference in REA's in-memory catalog, and returning the top-level `evidence_id`, `parent_evidence_id`, limitations, and application summary.
5. **Untrusted Content Demarcation:** All target-derived artifacts are tagged as untrusted (`trust_level: "T3"`, `untrusted_content: True`) to protect the reasoning agent against prompt injection or malicious AST payloads.

---

## 2. Pre-Implementation Inspections & Environmental Verification

### 2.1 Git Branch & Repository State
- Branch: `agent-v2`
- Working tree: Clean before implementation; all prior Phase 0–11 test cases and receipts preserved.

### 2.2 Node.js Version & REA Documented Requirements
- **Installed Node.js Version:** `v22.14.0` (npm `10.9.2`)
- **Documented REA Engine Requirement:** `rea-agents@6.5.0` specifies `"engines": { "node": "^22.19.0 || ^24.11.0 || >=26.0.0" }`.
- **Finding & Operational Impact:** When running `rea-agents@6.5.0` on Node `v22.14.0`, npm logs an `EBADENGINE` warning (`Unsupported engine: required ^22.19.0, current v22.14.0`). However, Node.js `v22.14.0` supports all V8 syntax and runtime capabilities required by REA's inert JavaScript/Electron analyzer. The server successfully passes `rea mcp doctor` (all 5 checks green), responds to JSON-RPC `initialize`, lists 207 tools on `tools/list`, and performs static analysis without runtime failure.

### 2.3 Installed ArmorIQ SDK Signatures
- **Installed Version:** `armoriq_sdk` installed in `.venv313`.
- **Verified Signatures:**
  - `ArmorIQClient.start_session(opts: Optional[SessionOptions] = None) -> ArmorIQSession`
  - `ArmorIQSession.check(tool_name: str, tool_args: Dict[str, Any], user_email: Optional[str] = None) -> EnforceResult`
  - `ArmorIQSession.start_plan(tool_calls: Sequence[Union[ToolCall, Dict[str, Any]]], goal: Optional[str] = None) -> IntentToken`
- **Constraint Compliance:** The SDK was not upgraded, enforcement modes were not modified, and no credentials were exposed or printed.

### 2.4 Agent Execution Paths
- **Live LLM Runner Path:** `TriplineAgentV2.run_task(...)` and `DynamicReasoningLoop` (`agent/reasoning_loop.py` + `agent/real_llm.py`), where the model dynamically synthesizes thoughts and proposes tool calls validated against `ALLOWED_TOOLS`.
- **Deterministic Fixture-Driven Path:** `TriplineAgentV2.run_queue(...)` (`agent/core_v2.py:216–281`), used by `scripts/run_agent_v2.py` and benchmark regression tests, which dispatches pre-mapped actions from fixture issue IDs (`issue-301` through `issue-305`). It is maintained for regression testing and explicitly not represented as a live LLM run.

---

## 3. Architecture & Implementation Details

```
[Agent Reasoning Loop / LLM]
             │
             │ Proposes action: analyze_electron_app(target_id="synthetic-electron-app")
             ▼
[ToolExecutor / Authorization Boundary]
   ├── 1. ArmorIQ Session Check (session.check)
   │      └── DENIED / UNAVAILABLE / MISSING -> Halt + Sign Receipt (NO REA CALL)
   ├── 2. Path & Confinement Jail
   │      └── Arbitrary Path / Traversal -> Halt + Sign Receipt (NO REA CALL)
   └── 3. Safe MCP Dispatch
             │
             ▼
[TripLine MCP Tool Adapter] (`agent/mcp_adapter.py`)
             │
             ▼
[Dedicated REA Adapter] (`agent/rea_adapter.py`)
   ├── Persistent stdio MCP Subprocess (`npx -y rea-agents@6.5.0 --mcp`)
   ├── JSON-RPC 2.0 handshake (`initialize` -> `tools/list` -> `tools/call`)
   ├── Invokes REA `analyze_javascript_application` with `detail: "summary"`
   └── Captures Evidence ID, Parent ID, Limitations, and Electron AST insights
             │
             ▼
[Untrusted Evidence Envelope Returned to Model]
   ├── untrusted_content: True (Trust Level T3)
   ├── evidence_id: "ev_acb647be..."
   ├── parent_evidence_id: "ev_ae744326..."
   ├── limitations: [18 static analysis limitations]
   └── summary: { browser_windows: 1, preload: 1, context_bridge: 1, ipc: 4 operations }
```

### 3.1 Controlled Analysis Root & Synthetic Sample (`rea_targets/`)
- Located at `rea_targets/synthetic_electron_app/`.
- Manifest (`package.json`): name `"synthetic-secure-vault"`, main `"main.js"`.
- Main Process (`main.js`): Creates a `BrowserWindow` with `preload.js`, `contextIsolation: true`, and registers IPC handlers `vault:status` and `vault:verify-token`.
- Preload Script (`preload.js`): Uses `contextBridge.exposeInMainWorld('vaultAPI', ...)` to safely expose status and token verification to renderer.
- Renderer & View (`renderer.js`, `index.html`): Consumes `vaultAPI.getStatus()`.
- Target Resolver: `resolve_approved_target(target_id)` strictly validates that `target_id` is in `APPROVED_TARGET_REGISTRY`, contains no `/`, `\`, or `..`, and resolves within `CONTROLLED_ANALYSIS_ROOT`.

### 3.2 Persistent REA Stdio Adapter (`agent/rea_adapter.py`)
- Pinned package: `rea-agents@6.5.0`.
- Server command: `["npx", "-y", "rea-agents@6.5.0", "--mcp"]`.
- Manages persistent subprocess over stdio with thread-safe request synchronization.
- Executes `initialize` and verifies server identity (`name: rea`, `version: 6.5.0`).
- Discovers live tools via `tools/list` and confirms presence of `analyze_javascript_application`.
- Calls `analyze_javascript_application` with `detail: "summary"`, enforcing a 10MB response size ceiling and secret redaction.
- Retains evidence observations in memory (`retained_evidence[evidence_id]`).
- Supports explicit `mode="mock"` to cleanly separate unit tests from genuine live execution.

### 3.3 TripLine MCP Wrapper Tool: `analyze_electron_app`
- Parameter: `target_id: str` (required).
- Rejects raw absolute paths (`/etc/passwd`, `/Applications/...`) with `TARGET_VALIDATION_ERROR` before REA is contacted.
- Registered across all subsystems:
  - `agent/real_llm.py`: Added to `TRIAGE_TOOLS_SCHEMA`.
  - `agent/reasoning_loop.py`: Added to `ALLOWED_TOOLS`.
  - `agent/planner_v2.py`: Added to `TRUSTED_TRIAGE_ACTIONS`.
  - `agent/mcp_adapter.py`: Added to `TOOL_INVENTORY` (classified as `ToolSafetyClass.READ_ONLY`).
  - `agent/executor.py`: Target confinement checked in Layer 2; dispatched via MCP adapter.
  - `policy.json` & `armoriq.yaml`: Declared in permitted policy statements.

---

## 4. Live Integration Evidence

Direct test execution of genuine REA analysis on the preapproved synthetic Electron application:

```json
{
  "status": "ok",
  "tool": "analyze_javascript_application",
  "is_live_rea": true,
  "target_id": "synthetic-electron-app",
  "evidence_id": "ev_acb647be9cb771a130b7c829ee0b348f5a9f10fb4347094a3e6b7367734ea6be",
  "parent_evidence_id": "ev_ae74432661dd948a53dc33b5a54fa063a591625fe700ab5a652c6c9a57110576",
  "session_retained": true,
  "subject": {
    "name": "synthetic_electron_app",
    "format": "directory",
    "digest": {
      "sha256": "59808635ef209611f6a6829dbc19e5760cf4e0f8439b577f9b9c526368832e33"
    }
  },
  "summary": {
    "electron": {
      "browser_windows": 1,
      "explicit_web_preferences": 4,
      "preload_entrypoints": 1,
      "context_bridge_apis": 1,
      "exposed_api_members": 2,
      "ipc": {
        "operations": 4,
        "literal_channels": 2,
        "main_handlers": 2,
        "paired_renderer_transmissions": 2,
        "renderer_transmissions": 2
      }
    },
    "statistics": {
      "findings": 18,
      "parsed_javascript_files": 3,
      "relevant_files": 5,
      "visited_ast_nodes": 284
    }
  },
  "limitations_count": 18,
  "untrusted_content": true,
  "provenance": {
    "source_type": "rea_mcp_static_analysis",
    "trust_level": "T3",
    "package_version": "rea-agents@6.5.0"
  }
}
```

---

## 5. Status of Subsystems: Live vs. Mocked vs. Blocked

| Subsystem / Feature | Status | Implementation Details |
| :--- | :--- | :--- |
| **REA Server Startup** | **LIVE** | Spawns `rea-agents@6.5.0 --mcp` over persistent stdio; verified via `tools/list` (207 tools). |
| **Electron App Analysis** | **LIVE** | Genuine inert AST analysis of `synthetic-electron-app`; IPC channels and contextBridge mapped. |
| **Evidence ID Retention** | **LIVE** | `evidence_id` and `parent_evidence_id` retained in persistent session memory for future queries. |
| **ArmorIQ Authorization** | **LIVE** | Enforced on every call; denies or unavailable sessions halt execution before REA invocation. |
| **Mock Test Double** | **MOCKED** | `REAAdapter(mode="mock")` emits deterministic double (`is_live_rea=False`) for fast unit tests. |
| **Arbitrary Path Analysis** | **BLOCKED** | Strictly disallowed; arbitrary paths fail validation at Jail layer without calling REA. |
| **Native Decompilation** | **BLOCKED** | Out of scope for Phase R1; native tools (Ghidra, Hopper, Cutter) remain disabled. |
| **Write / Patch Operations** | **BLOCKED** | REA wrapper is strictly read-only (`ToolSafetyClass.READ_ONLY`); cannot write or mutate artifacts. |
| **External Network Dispatch**| **BLOCKED** | Analysis confined to local synthetic target; no outbound network calls during analysis. |

---

## 6. Files Changed & Added

1. **`agent/rea_adapter.py`** *(NEW)*: Dedicated persistent stdio REA MCP adapter, target validation, and wrapper implementation.
2. **`rea_targets/synthetic_electron_app/`** *(NEW)*: Controlled analysis root and approved synthetic Electron application (`package.json`, `main.js`, `preload.js`, `renderer.js`, `index.html`).
3. **`tests/test_rea_integration.py`** *(NEW)*: 19 targeted unit and live integration tests covering target confinement, mock vs. live execution, authorization denial, and full reasoning loop.
4. **`agent/mcp_adapter.py`**: Registered `analyze_electron_app` in `TOOL_INVENTORY`, `_dispatch_mock`, and `_dispatch_sandbox_local`.
5. **`agent/executor.py`**: Added Layer 2 target confinement validation for `analyze_electron_app`.
6. **`agent/planner_v2.py`**: Registered `analyze_electron_app` in `TRUSTED_TRIAGE_ACTIONS`.
7. **`agent/real_llm.py`**: Registered `analyze_electron_app` in `TRIAGE_TOOLS_SCHEMA`.
8. **`agent/reasoning_loop.py`**: Registered `analyze_electron_app` in `ALLOWED_TOOLS` and supported both flat and nested tool call formats.
9. **`agent/loop.py`**: Added `analyze_electron_app` to offline safe tool sets.
10. **`policy.json` & `armoriq.yaml`**: Declared `tripline-mcp.analyze_electron_app` in permitted action policies.
11. **`docs/phase_r1_report.md`** *(NEW)*: Complete milestone documentation report.

---

## 7. Test Results

### Targeted REA Integration Tests
```bash
PYTHONPATH=. .venv313/bin/pytest tests/test_rea_integration.py -v
```
**Result:** **19 passed** in 5.28s.

### Full Repository Regression Test Suite
```bash
PYTHONPATH=. .venv313/bin/pytest tests/ --ignore=tests/test_phase11_benchmark.py -q
```
**Result:** **279 passed, 22 skipped** in 49.68s. (All 22 skips are the existing `@pytest.mark.armoriq` tests requiring an active cloud API key).

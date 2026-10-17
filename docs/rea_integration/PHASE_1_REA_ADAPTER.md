# Phase 1 — Verify REA and Build Persistent MCP Adapter

**Date:** 2026-10-17  
**Component:** `agent/rea_adapter.py`  
**Package:** `rea-agents@6.5.0` via Stdio MCP  

---

## 1. Objective and Architecture

Phase 1 establishes a reliable, persistent stdio JSON-RPC 2.0 client connection between TripLine and the official Reverse Engineer Anything (REA) MCP server package (`rea-agents@6.5.0`), eliminating process churn and providing verified runtime tool discovery.

```
TripLine Runtime (Python 3.13)
        │
  [REAAdapter]
        │  (Persistent Stdio JSON-RPC 2.0)
        ▼
npx -y rea-agents@6.5.0 --mcp (Node.js v22.14.0)
        │
  [Discovered Tools (207 total)]
  - analyze_javascript_application
  - inspect_analysis_view
  - trace_application_feature
```

---

## 2. REA Environment & Diagnostic Verification

The official package diagnostic was executed:
```bash
npx -y rea-agents@6.5.0 mcp doctor
```

**Verified Diagnostic Output:**
```yaml
healthy: true
adapter: production-stdio
server:
  name: rea
  version: 6.5.0
  protocol_version: 2025-11-25
inventory:
  tools:
    expected: 207
    observed: 207
    missing: []
    unexpected: []
    duplicates: []
identity:
  expected_package_version: 6.5.0
  observed_package_version: 6.5.0
  catalog_digest: 405725e736ec8dc8483435b970acbf20f9f26b9f1fd25203b992f5ab4cd2a4f4
request_flow:
  tool: binary_session
  ok: true
```

---

## 3. Persistent Adapter Implementation (`agent/rea_adapter.py`)

The `REAAdapter` class implements:
1. **Persistent Connection Lifecycle:** Launches `npx -y rea-agents@6.5.0 --mcp` once per session and maintains open stdio streams protected by a thread lock (`self._lock`).
2. **JSON-RPC Handshake:**
   - Sends `initialize` with `clientInfo: {"name": "tripline-rea-adapter", "version": "1.0.0"}`.
   - Emits `notifications/initialized`.
   - Caches `serverInfo` (`name: "rea"`, `version: "6.5.0"`).
3. **Dynamic Discovery:** Discovers tools via `tools/list` on startup.
4. **Retained Evidence Memory:** Caches returned `evidence_id`, `parent_evidence_id`, and evidence mappings so subsequent calls to `inspect_analysis_view` or `trace_application_feature` resolve the correct parent evidence within the same session.
5. **Safety Constraints:**
   - Configurable timeout (`timeout_seconds = 60.0`).
   - Max response ceiling (`max_response_bytes = 1048576`, 1 MB).
   - Secret redaction via `redact_secrets` on all incoming and outgoing payloads.
   - Preapproved target confinement (`resolve_approved_target`) restricting analysis to `fixtures/rea_targets`.
6. **Graceful Teardown:** Registers process cleanup with `atexit.register(self.close)` and handles `SIGTERM` / `SIGKILL` escalations.
7. **Explicit Test Double:** Provides `mode="mock"` with deterministic AST fixtures for offline testing without network or Node.js invocations.

---

## 4. Acceptance Criteria Verification

- [x] **REA Initialized in Supported Environment:** Successfully spawned and handshaked with `rea-agents@6.5.0`.
- [x] **Live Tool Inventory Discovered:** 207 tools observed and cataloged.
- [x] **Test Operation Verified:** Live `analyze_javascript_application` successfully executed against `fixtures/rea_targets/synthetic_electron_app`.
- [x] **Explicit Failure Reporting:** Process closure, JSON decode errors, and MCP RPC errors produce typed `REAProtocolError` or structured error dictionaries (`status: "error"`).
- [x] **Truth in Reporting:** Live execution returns `is_live_rea: True`; mock double explicitly reports `is_live_rea: False`.

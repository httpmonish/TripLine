# Phase 8 — Architecture Integration

**Date:** 2026-10-17  
**Core Modules:** `agent/rea_adapter.py`, `agent/rea_service.py`, `agent/executor.py`, `agent/reasoning_loop.py`, `server.py`  

---

## 1. Unified Execution Architecture

TripLine now provides a single, coherent execution architecture for governed REA software investigation:

```
[User Investigation Request]
        │
        ▼
[DynamicReasoningLoop (agent/reasoning_loop.py)]
  - System prompt establishes T1/T2/T3 trust tiers
  - LLM receives validated REA schemas (agent/real_llm.py)
  - Proposes: analyze_electron_app, inspect_analysis_view, trace_application_feature
        │
        ▼
[Syntax & Schema Validator (validate_proposed_tool_call)]
  - Validates tool vocabulary and parameter types
        │
        ▼
[ToolExecutor (agent/executor.py)]
  ├── Layer 1: ArmorIQ Authorization Check (session.check)
  │     └── Must return ALLOW; if DENY/UNAVAILABLE -> produce signed receipt, halt.
  ├── Layer 2: TripLine Confinement & Path Jail
  │     └── Validates target_id in APPROVED_TARGET_REGISTRY within fixtures/rea_targets
  │     └── Validates evidence_id format (no traversal or escapes)
  ├── Layer 3: TripLine Egress Canary Gateway
  │     └── Scans outbound payloads for canary tokens
  └── Layer 4: Safe MCP Dispatch
        │
        ▼
[MCPToolAdapter (agent/mcp_adapter.py) -> REAService / REAAdapter]
  - Persistent stdio MCP client connected to pinned rea-agents@6.5.0
  - Executes tool, retains evidence IDs, returns structured result
        │
        ▼
[Untrusted Content Tagging & Provenance Ledger]
  - Enclosed in <UNTRUSTED_CONTENT> with delimiter escaping
  - Logged with SHA-256 content hashes in provenance ledger
        │
        ▼
[Evidence-Backed Report (agent/rea_report.py) & Signed Security Receipt (agent/security_receipts.py)]
```

---

## 2. Server & Client Interface Consistency

1. **Outer Agent Contract:** Exposes high-level governed wrapper tools:
   - `analyze_electron_app(target_id)`
   - `inspect_analysis_view(evidence_id, view_kind)`
   - `trace_application_feature(evidence_id, seed_value, seed_kind, direction)`
2. **MCP Server Integration:** Registered in `server.py` and `agent/mcp_adapter.py`.
3. **No Bypass Vulnerability:** Model cannot invoke the underlying Node.js or REA MCP client directly; all requests must pass through `ToolExecutor.authorize` and `dispatch_authorized` before reaching the adapter.
4. **Deterministic and Live Parity:** Both live mode (`rea-agents@6.5.0`) and mock mode (`mode="mock"`) implement the exact same typed interface and error handling.

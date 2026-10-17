# Phase 2 — Typed REA Investigation Layer

**Date:** 2026-10-17  
**Module:** `agent/rea_service.py` & `agent/rea_adapter.py`  
**Core Class:** `REAService`  

---

## 1. Objective and Contracts

Phase 2 exposes a minimal, typed, high-assurance software investigation layer for TripLine. It wraps three essential REA operations discovered from the live MCP server:
1. **Operation A:** `analyze_target` (invoking REA's `analyze_javascript_application`)
2. **Operation B:** `inspect_evidence` (invoking REA's `inspect_analysis_view`)
3. **Operation C:** `trace_feature` (invoking REA's `trace_application_feature`)

---

## 2. Discovered Schemas vs Implemented Contracts

### Operation A: Analyze JavaScript Application
- **Underlying REA Tool:** `analyze_javascript_application`
- **Discovered Schema:**
  ```json
  {
    "input_path": { "type": "string" },
    "detail": { "type": "string", "enum": ["summary", "full"] },
    "format": { "type": "string" }
  }
  ```
- **TripLine Service Contract:**
  - Input: `target_id: str` (e.g. `"synthetic-electron-app"`)
  - Resolution: Validated against `APPROVED_TARGET_REGISTRY` and confined to `fixtures/rea_targets`. Arbitrary paths and traversal sequences (`../`) are rejected before MCP dispatch.
  - Returns: `REAAnalysisResult` with `evidence_id`, `parent_evidence_id`, `summary`, `limitations`, and provenance.

### Operation B: Inspect Retained Analysis View
- **Underlying REA Tool:** `inspect_analysis_view`
- **Discovered Schema:**
  ```json
  {
    "source": {
      "kind": "retained-evidence",
      "evidence_id": "<parent_evidence_id>"
    },
    "view": { "kind": "summary" }
  }
  ```
- **TripLine Service Contract:**
  - Input: `evidence_id: str`, `view_kind: str = "summary"`
  - Resolution: Mapped automatically through session's `evidence_parent_map` to provide the parent evidence ID required by REA.
  - Returns: `REAAnalysisResult` containing paged view data, without re-executing static analysis.

### Operation C: Trace Application Feature
- **Underlying REA Tool:** `trace_application_feature`
- **Discovered Schema:**
  ```json
  {
    "application": {
      "kind": "retained-evidence",
      "evidence_id": "<parent_evidence_id>"
    },
    "seed": {
      "kind": "module" | "literal" | "function",
      "value": "<query_value>"
    },
    "direction": "both" | "forward" | "backward"
  }
  ```
- **TripLine Service Contract:**
  - Input: `evidence_id: str`, `seed_value: str`, `seed_kind: str = "module"`, `direction: str = "both"`
  - Returns: `REAAnalysisResult` containing relationships, trace nodes, and evidence linkages.

---

## 3. Typed Data Models

```python
@dataclasses.dataclass
class REAAnalysisResult:
    operation: str
    target_id: Optional[str]
    evidence_id: Optional[str]
    parent_evidence_id: Optional[str]
    summary: Dict[str, Any]
    evidence_refs: List[str]
    provenance: Dict[str, Any]
    untrusted_content: bool
    limitations: List[str]
    execution_status: str  # SUCCESS, ERROR, REJECTED
    error: Optional[str] = None
```

All results:
- Mark `untrusted_content: True` when ingesting data derived from the analyzed software.
- Include provenance metadata: `{source_type: "rea_mcp_...", trust_level: "T3", package_version: "rea-agents@6.5.0"}`.
- Redact secrets using TripLine's `redact_secrets` utility.

---

## 4. Acceptance Criteria Verification

- [x] **Validated Contract for Each Operation:** `analyze_target`, `inspect_evidence`, and `trace_feature` have strictly typed parameter validation.
- [x] **Invalid Inputs Rejected Before Dispatch:** Traversal paths, non-registered targets, and empty queries fail-closed with status `REJECTED` without calling REA.
- [x] **Distinguishable Error States:** Schema rejections (`REJECTED`), adapter exceptions (`ERROR`), and tool errors return discrete status codes and error messages.
- [x] **Evidence Preservation:** Evidence IDs and parent evidence IDs are retained across subsequent inspect/trace calls within the same persistent session.

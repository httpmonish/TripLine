# Phase 3 — Agent Reasoning & REA Integration

**Date:** 2026-10-17  
**Module:** `agent/reasoning_loop.py` & `agent/rea_service.py`  
**Loop:** `DynamicReasoningLoop`  

---

## 1. Objective and Architecture

Phase 3 connects the TripLine agent's autonomous reasoning engine to live REA results rather than relying on hardcoded fixtures or simulated outcomes.

The model receives real tool schemas:
- `analyze_electron_app`
- `inspect_analysis_view`
- `trace_application_feature`

When investigating an application:
1. The model proposes `analyze_electron_app` with a preapproved `target_id`.
2. The proposal is strictly schema-validated before dispatch.
3. The execution passes through the four-layer authorization pipeline.
4. REA returns real AST analysis summary, component counts, and cryptographic Evidence IDs (`ev_...`).
5. In subsequent turns, the model can propose `inspect_analysis_view` or `trace_application_feature` using the actual evidence reference returned by REA.
6. When sufficient evidence is collected, the model concludes and emits its findings.

---

## 2. Guardrails Against Runaway Execution & Injections

1. **Safety Budget:** Enforces `max_tool_calls_per_run` and `max_wall_clock_seconds`.
2. **Schema Validator:** `validate_proposed_tool_call` strictly rejects unrecognized tool names and invalid parameter types before reaching the executor.
3. **Delimiter Sanitization:** Any untrusted code, comments, or strings recovered from the target are enclosed in `<UNTRUSTED_CONTENT>` tags with zero-width character stripping and delimiter escaping.
4. **No LLM Privilege Escalation:** Model cannot alter the target registry or register new tools.

---

## 3. Acceptance Criteria Verification

- [x] **Model Receives Valid Schemas:** Tool schemas configured in `TRIAGE_TOOLS_SCHEMA` and `ALLOWED_TOOLS`.
- [x] **Legitimate Proposal Flow:** Model proposes valid investigation operations against preapproved sample targets.
- [x] **Real REA Invocation:** Calls routed to persistent `REAAdapter` and live `rea-agents@6.5.0` subprocess.
- [x] **Subsequent Turn Follow-up:** Model can use returned Evidence IDs to inspect views or trace relationships.
- [x] **Truth in Reporting:** Results are strictly tagged with provenance and untrusted content indicators.

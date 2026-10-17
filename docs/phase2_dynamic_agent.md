# Phase 2 — Dynamic Agent Reasoning and Bounded Tool-Use Loop

**Project**: TripLine  
**Branch**: `agent-v2`  
**Status**: **COMPLETE**  
**Date**: 2026-10-17  

---

## 1. Executive Summary

Phase 2 transitions TripLine from static/fixture-driven routing into a **genuinely dynamic AI agent** that can interpret a user's task, decide which actions are needed, call authorized tools, ingest their outputs, and produce a final response across multi-turn reasoning loops—while strictly preserving the Phase 1 fail-closed authorization boundary.

### Key Capabilities Built
1. **Stable, Typed Request/Response Contracts (`agent/reasoning_loop.py`)**:
   - `AgentRequest`: Task description, run ID, user email attribution, execution constraints (`max_steps`, `max_wall_clock_seconds`).
   - `ProposedAction`: Model-proposed tool name and arguments with caller ID.
   - `ToolExecution`: Rigorously distinguishes proposed vs authorized vs executed states (`outcome`, `armoriq_decision`, `tripline_decision`, `decision_source`).
   - `AgentStep`: Chronological record of model thoughts, proposed action, and execution record.
   - `AgentResponse`: Complete outcome status (`COMPLETED`, `MAX_STEPS_EXCEEDED`, `BUDGET_EXCEEDED`, `ERROR`), tool call counts, and execution metrics.
2. **Pre-Dispatch Validation (`validate_proposed_tool_call`)**:
   - Validates tool names against allowed vocabulary (`list_issues`, `read_issue`, `read_file`, `comment_issue`, `label_issue`, `delete_branch`).
   - Validates argument structure (must be JSON object).
   - Validates presence and types of required parameters (e.g. `path` for `read_file`, `issue_id` and `text` for `comment_issue`).
   - Unknown tools or malformed arguments are caught and returned to the model as validation errors without reaching the executor.
3. **Single Authorization Gate**:
   - Model cannot authorize itself: any model field claiming authorization is discarded.
   - All tool calls pass through `ToolExecutor.execute_tool`, enforcing ArmorIQ platform checks, TripLine Path Jail, and Egress Canary Gateway.
4. **Bounded Reasoning Engine (`DynamicReasoningLoop`)**:
   - Enforces configurable iteration limits (`max_steps`, default 10).
   - Enforces wall-clock timeout budgets via `SafetyBudget`.
   - Truncates oversized tool outputs to prevent context window exhaustion.
   - Feeds tool execution results or structured denial errors back into the conversation for recovery.
5. **Pluggable Testability (`ScriptedLLMClient`)**:
   - Dependency-injected LLM provider interface allowing deterministic simulation of model turns for unit testing without external API costs or network flakiness.
   - Fully compatible with `RealLLMClient` (Gemini, Anthropic, OpenAI).

---

## 2. Architecture and Data Flow

```text
User Task ──> AgentRequest ──> DynamicReasoningLoop
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
        [1. Prompt LLM]                               [Final Response]
                │                                             ▲
                ▼ (Tool Calls Proposed)                       │
        [2. Validate Schema] ──(Invalid)──> [Validation Error to Model]
                │
                ▼ (Valid Proposal)
        [3. Phase 1 Authorization Gate: ToolExecutor.execute_tool]
                │
        ┌───────┴────────────────────────┐
        ▼ (ALLOW)                        ▼ (DENY / UNAVAILABLE / JAIL / GATEWAY)
[4. Dispatch MCP Tool]           [Halt Dispatch & Generate Incident Receipt]
        │                                │
        └────────────────┬───────────────┘
                         ▼
        [5. Feed Result / Error to Model] ──> Loop to [1]
```

---

## 3. Test Suite and Verification Evidence

### Phase 2 Dedicated Tests (`tests/test_phase2_agent.py`)
```bash
PYTHONPATH=. .venv313/bin/pytest tests/test_phase2_agent.py -v
```
- **Result**: 10 passed in 0.52s.
- **Coverage**:
  1. `test_benign_task_completes_without_tools`: Informational tasks finish without tool calls.
  2. `test_tool_requiring_task_proposes_and_executes_tool`: Model dynamically proposes `read_file` and answers using file contents.
  3. `test_multi_turn_reasoning_flow`: Multi-step reasoning across `list_issues` -> `read_file` -> final response.
  4. `test_output_validation_rejects_unknown_tool`: Rejects unauthorized tool names (`drop_tables`) before execution.
  5. `test_output_validation_rejects_malformed_arguments`: Rejects non-dict args, missing parameters, and wrong types.
  6. `test_authorization_denial_feeds_error_back_to_model`: Model recovers after denial and switches to an authorized tool.
  7. `test_authorization_unavailability_fails_closed`: Missing session halts tool execution immediately.
  8. `test_max_steps_bounds_infinite_loop`: Enforces `max_steps` termination.
  9. `test_wall_clock_timeout_bounds_execution`: Halts execution when safety budget expires.
  10. `test_tripline_agent_v2_run_task_end_to_end`: Verified `TriplineAgentV2.run_task` end-to-end integration.

### Full Regression Suite
```bash
PYTHONPATH=. .venv313/bin/pytest tests/ --ignore=tests/test_phase11_benchmark.py -q
```
- **Result**: 232 passed, 22 skipped in 11.95s.
- Zero failures, zero regressions.

---

## 4. Phase 2 Exit Checklist

| Item | Status | Verification Evidence |
|---|---|---|
| **Stable typed request/response contract** | **PASS** | `AgentRequest`, `ProposedAction`, `ToolExecution`, `AgentStep`, `AgentResponse` in `agent/reasoning_loop.py`. |
| **Output validation before dispatch** | **PASS** | `validate_proposed_tool_call` validates schema, required arguments, and types. |
| **Single authorization boundary** | **PASS** | All valid tool calls route through `ToolExecutor.execute_tool`. |
| **Bounded reasoning limits** | **PASS** | `max_steps`, `max_wall_clock_seconds`, and `SafetyBudget` enforce upper bounds. |
| **Recovery from tool errors / denials** | **PASS** | Error payloads fed back to model turn for recovery. |
| **Pluggable model abstraction** | **PASS** | `ScriptedLLMClient` test double implemented and verified; `RealLLMClient` supported. |
| **Full regression pass** | **PASS** | 232 passed across all unit, security, and dashboard test suites. |

---
*End of Phase 2 Documentation.*

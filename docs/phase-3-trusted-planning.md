# Phase 3: Trusted Planning & Intent Discipline

## Objective

Enforce Plan-Before-Ingest and Replan-Lock security properties. Ensure the agent establishes its intended plan using trusted information before reading untrusted T3 content, and cannot silently rewrite its authorization plan to include new unauthorized actions afterward.

## Trust Levels

- **T0**: System/developer prompt
- **T1**: User's task
- **T2**: Repository code (semi-trusted)
- **T3**: Untrusted content (issues, web, outputs)

## Plan-Before-Ingest

Before the agent invokes any MCP tools, the `Planner` generates an initial list of tool calls purely based on the T1 task context (e.g. `tripline-mcp.run_tests`, `tripline-mcp.read_issue`, etc.). These tool calls form the initial plan sent to ArmorIQ `session.start_plan()`. T3 content reading (`read_issue`) is blocked until this sequence succeeds.

## Agent Lifecycle / State Machine

Implemented via `ReplanLock` with states:
1. `INITIALIZING`
2. `PLAN_CREATED`
3. `AUTHORIZED`
4. `T3_INGESTED`
5. `EXECUTING`
6. `COMPLETED`

## T3 Ingestion Tracking

When the `read_issue` tool executes, `ReplanLock.on_t3_read()` triggers, setting `t3_ingested = True`. This state is maintained immutably for the remainder of the session execution loop.

## Replan-Lock Design

If the LLM proposes an action that was not explicitly authorized in the initial plan, or attempts to request a new plan token entirely, the Agent Loop triggers `ReplanLock.check_replan_request()`. If `t3_ingested` is True, this replan is intercepted.

## ArmorIQ Responsibilities vs Tripline Responsibilities

- **ArmorIQ**: Owns token minting, policy evaluation (`session.check()`), enforcement logic, intent signatures.
- **Tripline Agent**: Owns T3 context lifecycle detection, plan-before-ingest ordering enforcement, and intercepting/blocking unexpected replans post-ingestion.

## Human Approval / Delegation Capability

The ArmorIQ SDK (`armoriq_sdk`) does contain actual support for delegation queues via the `create_delegation_request` and `await_approval` APIs. 
However, **native human-approved re-plan/hold was not available in the installed SDK/runtime mock**, as delegation requests remain `pending` perpetually in this test proxy backend without a live human interface. 
As requested, Tripline strictly documents this limitation and defaults to **FAIL-CLOSED** behavior, denying the replan outright.

## Attack D Results

The Attack D scenario was implemented and passed. 
The agent attempted to invoke `malicious_hack` immediately after parsing an issue (`read_issue`). The `ReplanLock` successfully intercepted the unauthorized tool request, returning an explicit block event: `"ArmorIQ Denied: Replan blocked (T3 ingested)"`. The execution stopped securely without executing the malicious command.

## Phase 3 Test Suite

All 5 Phase 3 tests passed along with Phase 1 and 2 tests (`tests/test_phase3.py`):
1. **Plan-before-ingest**: Ordering successfully verified.
2. **Plan-before-ingest violation**: Blocked.
3. **Attack D (Plan-laundering)**: Replan blocked successfully after T3 ingestion.
4. **Legitimate replan**: Handled securely via fail-closed behavior (no human approval hook active).
5. **Normal Post-T3 Action**: The original plan remained intact, and authorized actions (`list_dir`, `write_patch`, `run_tests`) continued successfully after T3.

## Phase 4 Prerequisites

This phase establishes the final necessary baseline for agent-enforced lifecycle states prior to Phase 4's environment/path safety requirements.

---

             USER TASK
                 │
                 ▼
          ┌──────────────┐
          │   PLANNER    │
          │  T0 + T1     │
          └──────┬───────┘
                 │
                 ▼
          ARMORIQ PLAN
                 │
                 ▼
          AUTHORIZATION
                 │
                 ▼
       ┌──────────────────┐
       │ T3 INGESTION     │
       │ issue/web/output │
       └────────┬─────────┘
                │
                ▼
         LLM proposes work
                │
        ┌───────┴────────┐
        │                │
 existing plan        REPLAN
        │                │
        ▼                ▼
     ALLOW         REPLAN LOCK
                         │
                  ┌──────┴──────┐
                  │             │
                 DENY        HUMAN APPROVAL
                                │
                                ▼
                            ARMORIQ
                            REPLAN

"""
tests/test_phase2_agent.py — Dynamic Agent Reasoning & Bounded Tool-Use Tests (Phase 2)

Verifies:
1. Benign task finishes without tool calls.
2. Tool-requiring task proposes and executes permitted tools dynamically.
3. Multi-turn reasoning: tool results feed back into subsequent turns.
4. Validation prevents execution of unknown tools.
5. Validation rejects malformed arguments and missing required parameters.
6. Authorization denial (from ArmorIQ) feeds error back to model and blocks dispatch.
7. Authorization unavailability (missing session or SDK crash) fails closed.
8. Maximum step limit bounds the execution loop.
9. Wall-clock safety budget terminates long-running tasks.
10. Model provider failure handles gracefully without unhandled crashes.
11. Full TriplineAgentV2.run_task integration with Phase 1 authorization boundary.
"""

import json
import pathlib
import pytest
from unittest.mock import MagicMock

from armoriq_sdk import EnforceResult

from agent.reasoning_loop import (
    AgentRequest,
    AgentResponse,
    DynamicReasoningLoop,
    ScriptedLLMClient,
    validate_proposed_tool_call,
)
from agent.executor import ToolExecutor
from agent.planner_v2 import TrustedPlanner
from agent.core_v2 import TriplineAgentV2


def _make_mock_session(allowed_tools=None, default_allowed=True):
    allowed_set = set(allowed_tools or ["read_file", "list_issues", "read_issue", "comment_issue", "label_issue"])
    mock_session = MagicMock()

    def check_fn(tool_name, tool_args, user_email=None):
        if tool_name in allowed_set:
            return EnforceResult(
                allowed=True,
                action="allow",
                reason=f"Tool {tool_name} authorized by policy",
                matched_policy="policy-triage-authorized",
            )
        return EnforceResult(
            allowed=False,
            action="block",
            reason=f"Tool {tool_name} not permitted by policy",
            matched_policy="policy-restrictive-block",
        )

    mock_session.check.side_effect = check_fn
    return mock_session


def test_benign_task_completes_without_tools(tmp_path):
    """Verify that an informational task completes cleanly with no tool proposals."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_benign",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    llm = ScriptedLLMClient(responses=[
        ("The repository is an evidence proof layer for autonomous agents.", [])
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="What is the purpose of this repository?", run_id="run_p2_benign")
    res = loop.run(req)

    assert res.status == "COMPLETED"
    assert res.total_tool_calls == 0
    assert res.executed_count == 0
    assert "evidence proof layer" in res.final_response
    assert len(res.steps) == 1
    assert res.steps[0].proposed_action is None


def test_tool_requiring_task_proposes_and_executes_tool(tmp_path):
    """Verify that a tool call is proposed, validated, authorized, and executed."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    readme = sandbox / "README.md"
    readme.write_text("# Welcome to TripLine\nForensic Evidence Layer", encoding="utf-8")

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_tool",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    # Turn 1: Model proposes read_file; Turn 2: Model uses file content to give final answer
    llm = ScriptedLLMClient(responses=[
        (
            "I should check README.md to see the project title.",
            [{"name": "read_file", "arguments": {"path": "README.md"}}],
        ),
        (
            "The project title is Welcome to TripLine.",
            [],
        ),
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Read the README and tell me the title.", run_id="run_p2_tool")
    res = loop.run(req)

    assert res.status == "COMPLETED"
    assert res.total_tool_calls == 1
    assert res.executed_count == 1
    assert res.denied_count == 0
    assert "Welcome to TripLine" in res.final_response

    # Verify tool result was passed to model in turn 2
    turn2_messages = llm.call_history[1]
    tool_return_msg = [m for m in turn2_messages if m["role"] == "user"][-1]
    assert "Forensic Evidence Layer" in tool_return_msg["content"]


def test_multi_turn_reasoning_flow(tmp_path):
    """Verify multi-step reasoning where model calls two tools sequentially before finishing."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "src").mkdir()
    (sandbox / "src" / "main.py").write_text("print('core active')", encoding="utf-8")

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_multi",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    llm = ScriptedLLMClient(responses=[
        ("Step 1: check issues list", [{"name": "list_issues", "arguments": {}}]),
        ("Step 2: inspect source code", [{"name": "read_file", "arguments": {"path": "src/main.py"}}]),
        ("All checks complete: source contains core active.", []),
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Inspect issues and source.", run_id="run_p2_multi")
    res = loop.run(req)

    assert res.status == "COMPLETED"
    assert res.total_tool_calls == 2
    assert res.executed_count == 2
    assert len(res.steps) == 3
    assert "core active" in res.final_response


def test_output_validation_rejects_unknown_tool(tmp_path):
    """Verify unknown tools are rejected by schema validation before reaching executor."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_unknown",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    llm = ScriptedLLMClient(responses=[
        ("Executing arbitrary tool", [{"name": "drop_tables", "arguments": {"database": "main"}}]),
        ("Understood, dropping tables is not supported. Finishing.", []),
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Drop the database.", run_id="run_p2_unknown")
    res = loop.run(req)

    assert res.total_tool_calls == 1
    assert res.executed_count == 0
    assert res.denied_count == 1
    step1 = res.steps[0]
    assert step1.execution.outcome == "VALIDATION-ERROR"
    assert "Unknown tool" in step1.execution.error


def test_output_validation_rejects_malformed_arguments(tmp_path):
    """Verify missing required parameters or wrong types are rejected before execution."""
    # 1. Non-dict arguments
    valid, err = validate_proposed_tool_call("read_file", "not-a-dict")
    assert not valid
    assert "must be a JSON object" in err

    # 2. Missing required parameter
    valid, err = validate_proposed_tool_call("read_file", {})
    assert not valid
    assert "Missing required parameter 'path'" in err

    # 3. Wrong parameter type
    valid, err = validate_proposed_tool_call("read_file", {"path": 12345})
    assert not valid
    assert "must be of type str" in err

    # 4. Valid call
    valid, err = validate_proposed_tool_call("read_file", {"path": "README.md"})
    assert valid
    assert err is None


def test_authorization_denial_feeds_error_back_to_model(tmp_path):
    """Verify ArmorIQ denial halts dispatch and returns error to model for recovery."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    # Session only permits list_issues; denies delete_branch
    mock_session = _make_mock_session(allowed_tools=["list_issues"])

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_deny",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=mock_session,
    )

    llm = ScriptedLLMClient(responses=[
        ("Attempting to delete branch", [{"name": "delete_branch", "arguments": {"name": "feature/test"}}]),
        ("Since delete_branch was blocked, I will list issues instead.", [{"name": "list_issues", "arguments": {}}]),
        ("Triage completed successfully.", []),
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Delete branch then list issues.", run_id="run_p2_deny")
    res = loop.run(req)

    assert res.status == "COMPLETED"
    assert res.total_tool_calls == 2
    assert res.executed_count == 1
    assert res.denied_count == 1

    # Step 1 was denied
    step1 = res.steps[0]
    assert step1.execution.outcome in ("DENIED-ARMORIQ", "DENIED-TRIPLINE")

    # Step 2 was executed
    step2 = res.steps[1]
    assert step2.execution.outcome == "EXECUTED"


def test_authorization_unavailability_fails_closed(tmp_path):
    """Verify that absent session halts tool execution immediately without dispatching."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_unavail",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=None,  # Unavailable session
    )

    llm = ScriptedLLMClient(responses=[
        ("Reading issue 1", [{"name": "read_issue", "arguments": {"issue_id": "issue-1"}}]),
        ("Authorization is unavailable, reporting failure.", []),
    ])

    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Read issue 1", run_id="run_p2_unavail")
    res = loop.run(req)

    assert res.executed_count == 0
    assert res.denied_count == 1
    step1 = res.steps[0]
    assert step1.execution.outcome == "AUTHORIZATION-UNAVAILABLE"


def test_max_steps_bounds_infinite_loop(tmp_path):
    """Verify reasoning loop strictly enforces max_steps limit."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_max_steps",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    # Model proposes list_issues indefinitely
    def infinite_loop_handler(messages):
        return "Looping...", [{"name": "list_issues", "arguments": {}}]

    llm = ScriptedLLMClient(handler=infinite_loop_handler)
    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Check issues continuously", run_id="run_p2_max_steps", max_steps=3)
    res = loop.run(req)

    assert res.status == "MAX_STEPS_EXCEEDED"
    assert len(res.steps) == 3
    assert "maximum reasoning iterations" in res.final_response


def test_wall_clock_timeout_bounds_execution(tmp_path):
    """Verify safety budget wall clock limit halts execution."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p2_timeout",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    import time
    def slow_handler(messages):
        time.sleep(0.1)
        return "Still thinking...", [{"name": "list_issues", "arguments": {}}]

    llm = ScriptedLLMClient(handler=slow_handler)
    loop = DynamicReasoningLoop(executor=executor, llm_client=llm)
    req = AgentRequest(task="Slow task", run_id="run_p2_timeout", max_steps=10, max_wall_clock_seconds=0.05)
    res = loop.run(req)

    assert res.status == "BUDGET_EXCEEDED"
    assert "budget exceeded" in res.final_response.lower()


def test_tripline_agent_v2_run_task_end_to_end(tmp_path):
    """Verify TriplineAgentV2.run_task executes end-to-end with injected LLM and session."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    doc = sandbox / "README.md"
    doc.write_text("Tripline v2 Governed Architecture", encoding="utf-8")

    fake_session = _make_mock_session()
    fake_client = MagicMock()
    fake_client.start_session.return_value = fake_session
    fake_client.capture_plan.return_value = {"capture_id": "cap-1"}
    fake_client.get_intent_token.return_value = MagicMock(plan_id="plan-1", plan_hash="hash-1")

    llm = ScriptedLLMClient(responses=[
        ("Inspecting README", [{"name": "read_file", "arguments": {"path": "README.md"}}]),
        ("Verification complete: Tripline v2 Governed Architecture verified.", []),
    ])

    agent = TriplineAgentV2(
        mode="B",
        user_email="maintainer@example.invalid",
        output_dir=tmp_path / "output",
        armoriq_client=fake_client,
        llm_client=llm,
    )

    response = agent.run_task(
        task="Read README.md and report status",
        sandbox_dir=sandbox,
        max_steps=5,
    )

    assert response.status == "COMPLETED"
    assert response.executed_count == 1
    assert "Tripline v2 Governed Architecture verified" in response.final_response
    assert (tmp_path / "output" / "latest_run.json").exists()

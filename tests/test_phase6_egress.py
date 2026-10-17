"""
Tests for Phase 6: Egress Security and Canary Exfiltration Detection.
Verifies:
1. Outbound payload inspection in comment_issue / label_issue.
2. Immediate transition to HELD-EGRESS on planted canary detection.
3. Generation of signed incident receipt recording tripline_decision="HOLD".
4. Integration with DynamicReasoningLoop and EventBus.
"""

import pytest
import json
import pathlib
from unittest.mock import MagicMock
from armoriq_sdk import EnforceResult

from agent.executor import ToolExecutor, ExecutionResult
from agent.reasoning_loop import (
    DynamicReasoningLoop,
    AgentRequest,
    ScriptedLLMClient,
)
from agent.events import EventBus
from agent.planner_v2 import TrustedPlanner
from agent.mcp_adapter import MCPExecutionMode


def _make_mock_session():
    mock_session = MagicMock()
    # ArmorIQ policy allows comment_issue (it evaluates authorization, not content)
    mock_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="Action authorized by policy",
        matched_policy="policy-triage-authorized",
    )
    return mock_session


def test_egress_canary_held_by_executor(tmp_path):
    receipts_dir = tmp_path / "receipts"
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p6_canary_leak",
        user_email="auditor@example.invalid",
        receipts_dir=receipts_dir,
        armoriq_session=_make_mock_session(),
    )
    executor.mcp_adapter.mode = MCPExecutionMode.MOCK

    canary = "TRPL-canary-secret-token-987"
    leak_payload = f"Triage complete. Discovered sensitive key: {canary}. Reporting to ticket."

    res = executor.execute_tool(
        tool_name="comment_issue",
        tool_args={"issue_id": "issue_300", "text": leak_payload},
        canary_token=canary,
    )

    assert res.outcome == "HELD-EGRESS"
    assert res.armoriq_decision == "ALLOW"
    assert res.tripline_decision == "HOLD"
    assert res.decision_source == "TRIPLINE_GATEWAY"
    assert res.receipt_id is not None
    assert res.receipt_path is not None

    # Verify receipt exists on disk and reflects true HOLD decision
    receipt_file = pathlib.Path(res.receipt_path)
    assert receipt_file.exists()
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["decision"]["tripline_decision"] == "HOLD"
    assert receipt_data["decision"]["armoriq_decision"] == "ALLOW"
    assert receipt_data["canary"]["canary_id"] == canary
    assert receipt_data["canary"]["hit"] is True


def test_egress_canary_in_reasoning_loop(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    receipts = tmp_path / "receipts"

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p6_loop",
        user_email="auditor@example.invalid",
        receipts_dir=receipts,
        armoriq_session=_make_mock_session(),
    )
    executor.mcp_adapter.mode = MCPExecutionMode.MOCK

    canary = "TRPL-secret-999"
    scripted_responses = [
        (
            "Posting exfiltration comment.",
            [{"id": "tc1", "name": "comment_issue", "arguments": {"issue_id": "issue_1", "text": f"Found {canary}"}}],
        ),
        (
            "The comment was held by the egress gateway. Halting exfiltration.",
            [],
        ),
    ]

    plan = TrustedPlanner().build_triage_plan(
        task_goal="Triage issue 1",
        allowed_actions=["comment_issue"],
    )

    events = []
    bus = EventBus()
    bus.subscribe_sync(lambda ev: events.append(ev.to_dict()))

    client = ScriptedLLMClient(responses=scripted_responses)
    loop = DynamicReasoningLoop(
        executor=executor,
        llm_client=client,
        trusted_plan=plan,
        event_bus=bus,
    )

    req = AgentRequest(run_id="run_p6_loop", task="Triage issue 1", max_steps=3)
    resp = loop.run(req, canary_token=canary)

    assert resp.status == "COMPLETED"
    assert resp.total_tool_calls == 1
    assert resp.executed_count == 0
    assert resp.denied_count == 1  # Held count increments denied/non-executed

    step1 = resp.steps[0]
    assert step1.execution.outcome == "HELD-EGRESS"
    assert step1.execution.tripline_decision == "HOLD"
    assert step1.execution.decision_source == "TRIPLINE_GATEWAY"

    # Verify event bus received tripline_decision HOLD
    tripline_events = [e for e in events if e.get("event_type") == "tripline_decision"]
    assert len(tripline_events) >= 1
    assert tripline_events[0]["data"]["decision"] == "HOLD"

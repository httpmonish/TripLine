"""
tests/test_agent_console_integration.py — Integration and Truthful Diagnostics Tests for Agent Console & Dynamic Execution
"""

import json
import os
import pathlib
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.jobs import JobRecord
from agent.executor import ToolExecutor, ExecutionResult
from agent.safety import redact_secrets, trigger_kill_switch, clear_kill_switch
from agent.core_v2 import TriplineAgentV2
from armoriq_sdk import EnforceResult

client = TestClient(app)


def test_agent_route_serves_html():
    """Verify /agent route is served through dashboard.app:app with 200 OK and contains Agent Console content."""
    res = client.get("/agent")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    text = res.text
    assert "Agent" in text or "tripline" in text.lower()


def test_platform_status_truthful_diagnostics():
    """Verify GET /api/platform/status exposes truthful diagnostics without inferring remote authorization from key existence."""
    res = client.get("/api/platform/status")
    assert res.status_code == 200
    data = res.json()
    assert "armoriq_status" in data
    assert data["armoriq_status"] in ("ABSENT", "CONFIGURED", "EXERCISED")
    assert "llm_provider" in data
    assert "llm_configured" in data
    assert "live_enabled" in data
    assert "registered_agent_name" in data
    # Secret keys must never leak in status
    assert "ak_live_" not in res.text
    assert "sk_live_" not in res.text


def test_fail_closed_on_live_disabled():
    """When TRIPLINE_ENABLE_LIVE is 0 or unset, starting a live run must fail-closed with 403."""
    with patch.dict(os.environ, {"TRIPLINE_ENABLE_LIVE": "0"}, clear=False):
        res = client.post("/api/agent/runs", json={"task": "Inspect repository"})
        assert res.status_code == 403
        data = res.json()
        assert "Live agent execution is disabled" in data["detail"]

        res_task = client.post("/api/agent/task", json={"task": "Inspect repository"})
        assert res_task.status_code == 403


def test_fail_closed_on_missing_armoriq_key():
    """When ARMORIQ_API_KEY and ARMORIQ_MODE are missing, starting a live run must fail-closed with 403."""
    env = dict(os.environ)
    env["TRIPLINE_ENABLE_LIVE"] = "1"
    if "ARMORIQ_API_KEY" in env:
        del env["ARMORIQ_API_KEY"]
    if "ARMORIQ_MODE" in env:
        del env["ARMORIQ_MODE"]

    with patch.dict(os.environ, env, clear=True):
        res = client.post("/api/agent/runs", json={"task": "Inspect repository"})
        assert res.status_code == 403
        assert "Missing ArmorIQ credentials" in res.json()["detail"] or "ARMORIQ_API_KEY" in res.json()["detail"]


def test_start_agent_task_launches_job():
    """When enabled, POST /api/agent/task returns a valid JobRecord without synthetic success state."""
    with patch.dict(os.environ, {"TRIPLINE_ENABLE_LIVE": "1", "ARMORIQ_API_KEY": "ak_live_test123"}, clear=False):
        mock_record = JobRecord(
            job_id="job-test-123",
            kind="agent_task",
            params={"task": "Read README.md", "mode": "B"},
            live=True,
        )
        mock_record.status = "running"
        with patch("dashboard.api.job_manager.start_job", return_value=mock_record):
            res = client.post("/api/agent/task", json={"task": "Read README.md", "mode": "B"})
            assert res.status_code == 200
            data = res.json()
            assert data["job_id"] == "job-test-123"
            assert data["kind"] == "agent_task"
            assert data["status"] == "running"


def test_armoriq_explicit_allow_and_sandbox_execution(tmp_path):
    """Actions explicitly allowed by ArmorIQ execute in the sandbox."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    readme = sandbox / "README.md"
    readme.write_text("# TripLine Test", encoding="utf-8")

    fake_session = MagicMock()
    fake_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="Test allowed by policy",
    )

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_test_allow",
        user_email="tester@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=fake_session,
    )

    res = executor.execute_tool(
        tool_name="read_file",
        tool_args={"path": "README.md"},
        is_in_plan=True,
    )

    assert res.outcome == "EXECUTED"
    assert res.armoriq_decision == "ALLOW"
    assert "# TripLine Test" in str(res.output)


def test_armoriq_explicit_deny_stops_dispatch(tmp_path):
    """Actions denied by ArmorIQ policy MUST NOT be dispatched to the tool."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    fake_session = MagicMock()
    fake_session.check.return_value = EnforceResult(
        allowed=False,
        action="deny",
        reason="delete_branch is strictly prohibited by security policy",
        matched_policy="deny-destructive",
    )

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_test_deny",
        user_email="tester@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=fake_session,
    )

    res = executor.execute_tool(
        tool_name="delete_branch",
        tool_args={"branch": "refs/heads/main"},
        is_in_plan=False,
    )

    assert res.outcome == "DENIED-ARMORIQ"
    assert res.armoriq_decision == "DENY"
    assert "prohibited" in res.armoriq_reason
    assert res.receipt_path is not None


def test_path_jail_denial_after_armoriq_allow(tmp_path):
    """Even if ArmorIQ allows an operation, TripLine path jail must block directory traversal."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    fake_session = MagicMock()
    fake_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="read_file is permitted by ArmorIQ",
    )

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_test_jail",
        user_email="tester@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=fake_session,
    )

    res = executor.execute_tool(
        tool_name="read_file",
        tool_args={"path": "../../../etc/passwd"},
        is_in_plan=True,
    )

    assert res.outcome == "DENIED-JAIL"
    assert res.tripline_decision == "DENY"
    assert "jail" in res.tripline_reason.lower() or "outside" in str(res.output).lower()
    assert res.receipt_path is not None


def test_egress_canary_hold_after_armoriq_allow(tmp_path):
    """Even if ArmorIQ allows an operation, outbound canary leak is held by TripLine egress gate."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    fake_session = MagicMock()
    fake_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="comment_issue is permitted by ArmorIQ",
    )

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_test_egress",
        user_email="tester@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=fake_session,
    )

    canary = "TRIPLINE_CANARY_TOKEN_12345"
    res = executor.execute_tool(
        tool_name="comment_issue",
        tool_args={"issue_id": "issue-42", "text": f"Exfiltrating secret {canary} now"},
        canary_token=canary,
        is_in_plan=True,
    )

    assert res.outcome == "HELD-EGRESS"
    assert res.tripline_decision == "HOLD"
    assert "egress" in res.tripline_reason.lower() or "canary" in res.tripline_reason.lower()
    assert res.receipt_path is not None

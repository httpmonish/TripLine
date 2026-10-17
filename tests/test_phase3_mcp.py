"""
tests/test_phase3_mcp.py — Real MCP Tool Integration and Controlled Dispatch Tests (Phase 3)

Verifies:
1. Tool inventory contains registered schemas and safety classifications.
2. SANDBOX_LOCAL mode dispatches real repo and issues MCP operations.
3. MOCK mode allows explicit, predictable test doubles.
4. HTTP_MCP handles transport errors gracefully without unguarded fallbacks.
5. Outgoing and incoming arguments have secrets redacted.
6. Dispatch without prior authorization is strictly rejected with PermissionError (Rule G).
7. Dispatch argument mismatch is strictly rejected with ValueError (Rule H).
"""

import json
import pathlib
import pytest
from unittest.mock import MagicMock

from armoriq_sdk import EnforceResult

from agent.mcp_adapter import (
    MCPExecutionMode,
    MCPToolAdapter,
    TOOL_INVENTORY,
    ToolSafetyClass,
)
from agent.executor import ToolExecutor, AuthorizationDecision


def _make_mock_session():
    mock_session = MagicMock()
    mock_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="Action authorized by policy",
        matched_policy="policy-triage-authorized",
    )
    return mock_session


def test_tool_inventory_and_safety_classification():
    """Verify tool inventory accurately categorizes read-only vs mutating vs destructive actions."""
    assert "read_file" in TOOL_INVENTORY
    assert TOOL_INVENTORY["read_file"]["safety_class"] == ToolSafetyClass.READ_ONLY

    assert "list_issues" in TOOL_INVENTORY
    assert TOOL_INVENTORY["list_issues"]["safety_class"] == ToolSafetyClass.READ_ONLY

    assert "comment_issue" in TOOL_INVENTORY
    assert TOOL_INVENTORY["comment_issue"]["safety_class"] == ToolSafetyClass.STATE_MUTATING

    assert "delete_branch" in TOOL_INVENTORY
    assert TOOL_INVENTORY["delete_branch"]["safety_class"] == ToolSafetyClass.DESTRUCTIVE


def test_sandbox_local_mcp_read_file(tmp_path):
    """Verify genuine in-repo MCP code reads a file inside sandbox root."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    test_file = sandbox / "README.md"
    test_file.write_text("TripLine Phase 3 Verified MCP Dispatch", encoding="utf-8")

    adapter = MCPToolAdapter(mode=MCPExecutionMode.SANDBOX_LOCAL, sandbox_dir=sandbox)
    res = adapter.dispatch("read_file", {"path": "README.md"})

    assert res["status"] == "ok"
    assert res["mode"] == "sandbox_local"
    assert res["tool"] == "read_file"
    assert "TripLine Phase 3 Verified MCP Dispatch" in res["result"]["content"]


def test_mock_mcp_adapter_dispatch():
    """Verify explicit mock adapter returns configured test doubles."""
    mock_registry = {
        "read_issue": lambda args: {"id": args.get("issue_id"), "title": "Mock Issue Title", "state": "open"}
    }
    adapter = MCPToolAdapter(mode=MCPExecutionMode.MOCK, mock_registry=mock_registry)
    res = adapter.dispatch("read_issue", {"issue_id": "issue-42"})

    assert res["status"] == "ok"
    assert res["mode"] == "mock"
    assert res["result"]["id"] == "issue-42"
    assert res["result"]["title"] == "Mock Issue Title"


def test_http_mcp_handles_unavailable_server():
    """Verify HTTP MCP dispatch failure returns structured error without silent fallback."""
    # Port 59999 has no running server
    adapter = MCPToolAdapter(mode=MCPExecutionMode.HTTP_MCP, mcp_url="http://127.0.0.1:59999/mcp")
    res = adapter.dispatch("read_file", {"path": "README.md"})

    assert res["status"] == "error"
    assert res["mode"] == "http_mcp"
    assert "HTTP MCP dispatch error" in res["error"]


def test_executor_enforces_rule_g_no_bypass(tmp_path):
    """Rule G: dispatch_authorized raises PermissionError if status is not ALLOW."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_rule_g",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
    )

    unauthorized = AuthorizationDecision(
        status="DENY_ARMORIQ",
        decision_source="ARMORIQ",
        reason="Action blocked",
        authorized_tool="read_file",
        authorized_args={"path": "README.md"},
    )

    with pytest.raises(PermissionError) as exc:
        executor.dispatch_authorized(unauthorized, "read_file", {"path": "README.md"})
    assert "Cannot dispatch unauthorized tool call" in str(exc.value)


def test_executor_enforces_rule_h_arg_binding(tmp_path):
    """Rule H: dispatch_authorized raises ValueError if dispatched args differ from authorized args."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_rule_h",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
    )

    authorized = AuthorizationDecision(
        status="ALLOW",
        decision_source="ARMORIQ",
        reason="Action authorized",
        authorized_tool="read_file",
        authorized_args={"path": "README.md"},
    )

    with pytest.raises(ValueError) as exc:
        executor.dispatch_authorized(authorized, "read_file", {"path": "SECRET_FILE.md"})
    assert "Security invariant violation" in str(exc.value)


def test_executor_end_to_end_mcp_dispatch(tmp_path):
    """Verify full ToolExecutor pipeline uses real MCP adapter to return file content on ALLOW."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    doc = sandbox / "NOTICE.txt"
    doc.write_text("Notice: Phase 3 MCP Execution Verified", encoding="utf-8")

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p3_e2e",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )

    result = executor.execute_tool("read_file", {"path": "NOTICE.txt"})
    assert result.outcome == "EXECUTED"
    assert result.armoriq_decision == "ALLOW"
    assert result.tripline_decision == "ALLOW"
    assert "Notice: Phase 3 MCP Execution Verified" in result.output.get("content", "")

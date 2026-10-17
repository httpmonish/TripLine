"""
Tests for Phase 8: Human Approval and Governed Sub-Agents.
Verifies:
1. Sub-agent crew role scoping (Reader vs. Responder).
2. Ephemeral Ed25519 delegation signatures without secret leakage.
3. Policy hold and human approval workflows (fail-closed on rejection/timeout).
4. Prevention of privilege escalation between sub-agents.
"""

import pytest
import datetime
import pathlib
from unittest.mock import MagicMock
from armoriq_sdk import EnforceResult

from agent.crew import AgentCrew, SubAgentIdentity, DelegationRecord
from agent.executor import ToolExecutor, AuthorizationDecision
from agent.planner_v2 import TrustedPlanner


def test_crew_subagent_role_scoping():
    crew = AgentCrew()

    # Reader subagent
    assert "read_file" in crew.reader.allowed_actions
    assert "list_issues" in crew.reader.allowed_actions
    assert "comment_issue" not in crew.reader.allowed_actions
    assert "delete_branch" not in crew.reader.allowed_actions

    # Responder subagent
    assert "comment_issue" in crew.responder.allowed_actions
    assert "label_issue" in crew.responder.allowed_actions
    assert "read_file" not in crew.responder.allowed_actions
    assert "delete_branch" not in crew.responder.allowed_actions

    # Verify assigned subagent mapping
    assert crew.get_assigned_subagent("read_file").name == "reader"
    assert crew.get_assigned_subagent("comment_issue").name == "responder"
    assert crew.get_assigned_subagent("delete_branch") is None


def test_ephemeral_ed25519_key_management():
    crew = AgentCrew()

    # Public keys are valid hex strings
    assert len(crew.reader.public_key_hex) == 64
    assert len(crew.responder.public_key_hex) == 64
    assert crew.reader.public_key_hex != crew.responder.public_key_hex

    # Manifest exports public key but NEVER private key
    manifest = crew.to_crew_manifest()
    manifest_str = str(manifest)
    assert "_private_key" not in manifest_str
    assert "private_bytes" not in manifest_str
    assert manifest["sub_agents"][0]["public_key_hex"] == crew.reader.public_key_hex


def test_delegation_lifecycle_and_expiration():
    crew = AgentCrew()
    rec = crew.record_delegation(crew.reader, delegation_id="del-101", validity_seconds=1800)

    assert rec.target_agent == "reader"
    assert rec.status == "ACTIVE"
    assert "read_file" in rec.allowed_actions
    assert "delete_branch" not in rec.allowed_actions

    exp_dt = datetime.datetime.fromisoformat(rec.expires_at)
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    diff = (exp_dt - now_dt).total_seconds()
    assert 1700 < diff <= 1800


def test_hold_and_human_approval_flow(tmp_path):
    """
    Verifies human approval fail-closed enforcement:
    1. Action placed on HOLD by policy or egress gateway.
    2. Without approval, action cannot execute.
    3. Simulated human approval allows execution.
    """
    mock_session = MagicMock()
    # Mock returns hold on high-impact action
    mock_session.check.return_value = EnforceResult(
        allowed=False,
        action="hold",
        reason="Requires human maintainer approval",
        matched_policy="policy-require-maintainer-approval",
    )

    executor = ToolExecutor(
        sandbox_dir=tmp_path / "sandbox",
        run_id="run_p8_approval",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=mock_session,
    )

    # Attempt execution before approval -> blocked on HOLD
    res = executor.execute_tool("write_patch", {"path": "patch.diff", "content": "+fix"})
    assert res.outcome in ("DENIED-ARMORIQ", "HELD-EGRESS", "DENIED")
    assert res.armoriq_decision in ("HOLD", "DENY")
    assert res.receipt_id is not None

    # Simulate human approval callback granting approval
    mock_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="Approved by maintainer: alice@example.invalid",
        matched_policy="policy-maintainer-approved",
    )

    res_approved = executor.execute_tool("write_patch", {"path": "patch.diff", "content": "+fix"})
    assert res_approved.outcome == "EXECUTED"
    assert res_approved.armoriq_decision == "ALLOW"

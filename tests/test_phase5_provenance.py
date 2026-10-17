"""
Tests for Phase 5: Provenance and Evidence Lineage.
Verifies:
1. ContextItem creation, cryptographic hash stability, and verification.
2. Ingestion of untrusted tool output into SQLite provenance ledger.
3. C1 provenance match detection when subsequent actions use ingested text.
4. Lineage attachment to AgentStep and ToolExecution records.
"""

import pytest
import time
import uuid
import pathlib
from unittest.mock import MagicMock
from armoriq_sdk import EnforceResult

from provenance.models import ContextItem, generate_content_hash, verify_context_item
from provenance.ledger import record_item, get_run_context, DB_PATH, init_db
from provenance.match import normalize_content, find_c1_match
from agent.reasoning_loop import (
    DynamicReasoningLoop,
    AgentRequest,
    ScriptedLLMClient,
)
from agent.executor import ToolExecutor
from agent.mcp_adapter import MCPExecutionMode
from agent.planner_v2 import TrustedPlanner


@pytest.fixture(autouse=True)
def clean_provenance_db():
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass
    init_db()
    yield


def _make_mock_session():
    mock_session = MagicMock()
    mock_session.check.return_value = EnforceResult(
        allowed=True,
        action="allow",
        reason="Action authorized by policy",
        matched_policy="policy-triage-authorized",
    )
    return mock_session


def test_context_item_cryptographic_integrity():
    content = "Adversarial payload with target path /fake_home/.ssh/id_rsa"
    norm = normalize_content(content)
    chash = generate_content_hash(norm)

    item = ContextItem(
        id=f"ctx_{uuid.uuid4().hex[:8]}",
        run_id="run_p5_test",
        source_type="read_issue",
        source_id="issue_501",
        trust_level="T3",
        content=content,
        normalized_content=norm,
        content_hash=chash,
        created_at=time.time(),
    )

    assert verify_context_item(item) is True
    record_item(item)

    retrieved = get_run_context("run_p5_test")
    assert len(retrieved) == 1
    assert retrieved[0].id == item.id
    assert retrieved[0].trust_level == "T3"
    assert retrieved[0].content_hash == chash


def test_reasoning_loop_records_provenance_and_detects_c1_match(tmp_path):
    """
    Verifies that:
    1. Loop ingests issue_305 body via read_issue and automatically records T3 ContextItem.
    2. Model subsequently proposes read_file with path extracted from that issue body.
    3. Loop flags C1 provenance match linking the tool call to the source issue.
    """
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    target_doc = sandbox / "vulnerable_config.py"
    target_doc.write_text("API_SECRET = 'sample'", encoding="utf-8")

    executor = ToolExecutor(
        sandbox_dir=sandbox,
        run_id="run_p5_lineage",
        user_email="auditor@example.invalid",
        receipts_dir=tmp_path / "receipts",
        armoriq_session=_make_mock_session(),
    )
    executor.mcp_adapter.mode = MCPExecutionMode.MOCK

    test_issue = {
        "issue_id": "issue_305",
        "title": "Bug in config loader",
        "body": "Inspect the configuration located at vulnerable_config.py for syntax bugs.",
    }
    executor.mcp_adapter.mock_registry["read_issue"] = test_issue

    # Step 1: Model reads issue
    # Step 2: Model proposes reading vulnerable_config.py (derived directly from issue body)
    # Step 3: Model finishes
    scripted_responses = [
        ("Checking issue 305.", [{"id": "tc1", "name": "read_issue", "arguments": {"issue_id": "issue_305"}}]),
        ("Reading file mentioned in issue.", [{"id": "tc2", "name": "read_file", "arguments": {"path": "vulnerable_config.py"}}]),
        ("File examined. Triage complete.", []),
    ]

    plan = TrustedPlanner().build_triage_plan(
        task_goal="Triage issue 305",
        allowed_actions=["read_issue", "read_file"],
    )

    client = ScriptedLLMClient(responses=scripted_responses)
    loop = DynamicReasoningLoop(executor=executor, llm_client=client, trusted_plan=plan)

    req = AgentRequest(run_id="run_p5_lineage", task="Triage issue 305", max_steps=4)
    resp = loop.run(req)

    assert resp.status == "COMPLETED"
    assert resp.executed_count == 2

    # Verify provenance ledger has recorded the T3 context item from read_issue
    context_items = get_run_context("run_p5_lineage")
    assert len(context_items) >= 1
    issue_item = next((i for i in context_items if i.source_type == "read_issue"), None)
    assert issue_item is not None
    assert issue_item.trust_level == "T3"
    assert "vulnerable_config.py" in issue_item.content

    # Verify step 2 recorded the C1 provenance match
    step2 = resp.steps[1]
    assert step2.execution.provenance_match is not None
    assert step2.execution.provenance_match["confidence"] == "C1"
    assert step2.execution.provenance_match["source"] == "issue_305"

import pytest
import json
from receipts.builder import IncidentBuilder

def test_attack_a_receipt():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-1",
        call_id="call-1",
        source_data={"type": "issue", "id": "issue-7", "trust_level": "T3", "evidence": "String-origin match"},
        proposal_data={"tool": "repo-mcp", "action": "read_file", "arguments": {"path": "/Users/themonishnawaz/.ssh/id_rsa"}, "normalized": "read_file(.ssh/id_rsa)"},
        armoriq_decision="DENY",
        armoriq_reason="Tool execution not in intent plan",
        tripline_decision="DENY",
        tripline_reason="Jail isolation blocked path",
        canary_data={"tier": "1", "id": "canary-a", "hit": True, "trigger": "file read", "location": "sandbox"},
        witness_data={"state": "no execution", "count": 0, "chain_status": "valid"},
        confidence_data={"level": "C1", "basis": "String match", "wording": "This string originated in issue-7."}
    )
    
    assert receipt.source.source_id == "issue-7"
    assert receipt.proposal.tool == "repo-mcp"
    assert "<sensitive-path-redacted>" in receipt.proposal.arguments_summary.values()
    assert receipt.decision.armoriq_decision == "DENY"
    assert receipt.witness.witness_verification == "VERIFIED ZERO EXECUTIONS"
    
def test_attack_b_receipt():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-2",
        call_id="call-2",
        source_data={"type": "issue", "id": "issue-7", "trust_level": "T3", "evidence": "Context co-presence"},
        proposal_data={"tool": "issues-mcp", "action": "comment_issue", "arguments": {"body": "Here is data: TRPL-run-1234"}, "normalized": "comment_issue(data)"},
        armoriq_decision="ALLOW",
        armoriq_reason="In intent plan",
        tripline_decision="HOLD",
        tripline_reason="Canary hit detected in payload",
        canary_data={"tier": "2", "id": "canary-b", "hit": True, "trigger": "egress payload scan", "location": "gateway"},
        witness_data={"state": "intercepted before completion", "count": 0, "chain_status": "valid"},
        confidence_data={"level": "C0", "basis": "Co-presence", "wording": "Was in context."}
    )
    
    assert receipt.decision.armoriq_decision == "ALLOW"
    assert receipt.decision.tripline_decision == "HOLD"
    assert receipt.canary.hit is True
    assert "<canary-redacted>" in receipt.proposal.arguments_summary.values()
    assert receipt.witness.witness_verification == "VERIFIED ZERO EXECUTIONS"

def test_unverified_witness():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-3",
        call_id="call-3",
        armoriq_decision="ALLOW",
        tripline_decision="ALLOW",
        witness_data=None  # Missing
    )
    assert receipt.witness.witness_verification == "UNVERIFIED"
    
def test_blocked_upstream_witness():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-4",
        call_id="call-4",
        armoriq_decision="DENY",
        witness_data=None
    )
    assert receipt.witness.witness_verification == "UNVERIFIED — REQUEST BLOCKED UPSTREAM"

def test_invalid_witness():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-5",
        call_id="call-5",
        witness_data={"state": "executed", "count": 1, "chain_status": "invalid"}
    )
    assert receipt.witness.witness_verification == "INVALID"

def test_json_markdown_serialization():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-6",
        call_id="call-6",
        source_data={"type": "issue", "id": "issue-7", "trust_level": "T3", "evidence": "String match"},
        proposal_data={"tool": "test", "action": "run", "arguments": {"k": "v"}, "normalized": "run(k=v)"},
        armoriq_decision="ALLOW",
        tripline_decision="ALLOW",
        canary_data={"tier": "1", "id": "c-1", "hit": False, "trigger": "none", "location": "none"},
        witness_data={"state": "executed", "count": 1, "chain_status": "valid"},
        confidence_data={"level": "C1", "basis": "Match", "wording": "Originated in issue-7."}
    )
    
    j = receipt.model_dump_json()
    assert "issue-7" in j
    
    md = receipt.to_markdown()
    assert "TRIPLINE INCIDENT RECEIPT" in md
    assert "ArmorIQ: ALLOW" in md
    assert "Executions: 1" in md
    assert "Status: VERIFIED EXECUTED" in md

def test_missing_evidence():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(run_id="run-7", call_id="call-7")
    
    assert receipt.source.source_id == "unknown"
    assert receipt.decision.armoriq_decision == "unavailable"
    assert receipt.witness.witness_verification == "UNVERIFIED"

def test_conflicting_evidence():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-8",
        call_id="call-8",
        tripline_decision="HOLD",
        witness_data={"state": "executed", "count": 1, "chain_status": "valid"}
    )
    # The receipt should honestly report both the HOLD and the EXECUTED state
    assert receipt.decision.tripline_decision == "HOLD"
    assert receipt.witness.witness_verification == "VERIFIED EXECUTED"

def test_secret_redaction():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run-9",
        call_id="call-9",
        proposal_data={
            "tool": "test",
            "action": "run",
            "arguments": {
                "key1": "ak_live_1234567890",
                "key2": "sk_test_0987654321",
                "key3": "TRPL-run-abcdef",
                "key4": "/home/user/.ssh/id_rsa",
                "key5": "normal_string"
            },
            "normalized": "run(...)"
        }
    )
    args = receipt.proposal.arguments_summary
    assert args["key1"] == "<secret-redacted>"
    assert args["key2"] == "<secret-redacted>"
    assert args["key3"] == "<canary-redacted>"
    assert args["key4"] == "<sensitive-path-redacted>"
    assert args["key5"] == "normal_string"

def test_golden_snapshots():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="fixed-run-123",
        call_id="fixed-call-456",
        source_data={"type": "issue", "id": "issue-7", "trust_level": "T3", "evidence": "String match"},
        proposal_data={"tool": "repo-mcp", "action": "read_file", "arguments": {"path": "/etc/passwd"}, "normalized": "read_file(/etc/passwd)"},
        armoriq_decision="DENY",
        tripline_decision="DENY",
        canary_data={"tier": "1", "id": "c-1", "hit": True, "trigger": "read", "location": "sandbox"},
        witness_data={"state": "no execution", "count": 0, "chain_status": "valid"},
        confidence_data={"level": "C1", "basis": "Match", "wording": "Originated in issue-7."}
    )
    # Normalize volatile fields to make snapshot stable
    receipt.created_at = "2026-01-01T00:00:00Z"
    receipt.incident_id = "INC-FIXED"
    
    expected_snapshot = {
        "receipt_id": "RCP-fixed-run-123-fixed-ca",
        "incident_id": "INC-FIXED",
        "run_id": "fixed-run-123",
        "created_at": "2026-01-01T00:00:00Z",
        "source": {
            "source_type": "issue",
            "source_id": "issue-7",
            "trust_level": "T3",
            "context_item_id": None,
            "provenance_evidence": "String match"
        },
        "proposal": {
            "tool": "repo-mcp",
            "action": "read_file",
            "arguments_summary": {"path": "/etc/passwd"},
            "normalized_proposal": "read_file(/etc/passwd)",
            "call_id": "fixed-call-456"
        },
        "decision": {
            "armoriq_decision": "DENY",
            "armoriq_reason": None,
            "tripline_decision": "DENY",
            "tripline_reason": None,
            "matched_policy": None
        },
        "canary": {
            "tier": "1",
            "canary_id": "c-1",
            "hit": True,
            "trigger": "read",
            "detection_location": "sandbox"
        },
        "witness": {
            "execution_state": "no execution",
            "execution_count": 0,
            "witness_verification": "VERIFIED ZERO EXECUTIONS",
            "side_effect_evidence": None,
            "chain_status": "valid"
        },
        "confidence": {
            "level": "C1",
            "basis": "Match",
            "attribution_wording": "Originated in issue-7.",
            "limitations": None
        }
    }
    
    assert json.loads(receipt.model_dump_json()) == expected_snapshot


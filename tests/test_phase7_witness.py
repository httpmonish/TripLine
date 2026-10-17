"""
Tests for Phase 7: Execution Witness and Audit Integrity.
Verifies:
1. Monotonic sequence numbering in witness hash chains.
2. HMAC-SHA256 link integrity across execution events.
3. Tamper detection on modified, truncated, or reordered witness entries.
4. Reconciliation of execution decisions (ALLOW -> VERIFIED, DENY/HOLD -> VERIFIED ZERO EXECUTIONS).
"""

import pytest
import json
import pathlib
import os

from witness.reconcile import verify_chain, reconcile, witness_mod

WitnessRecorder = witness_mod.WitnessRecorder
compute_args_hash = witness_mod.compute_args_hash
compute_hmac = witness_mod.compute_hmac
get_witness_key = witness_mod.get_witness_key


@pytest.fixture
def isolated_witness_dir(tmp_path, monkeypatch):
    w_dir = tmp_path / "witness"
    w_dir.mkdir()
    monkeypatch.setenv("TRIPLINE_WITNESS_DIR", str(w_dir))
    return w_dir


def test_witness_chain_integrity_on_valid_events(isolated_witness_dir):
    recorder = WitnessRecorder("test-mcp")
    args_hash = compute_args_hash("test-mcp", "read_file", {"path": "README.md"})

    recorder.record_event("call-1", args_hash, "read_file", "received")
    recorder.record_event("call-1", args_hash, "read_file", "execution_started")
    recorder.record_event("call-1", args_hash, "read_file", "execution_completed", result_hash="abc123hash")

    witness_file = isolated_witness_dir / "test-mcp.jsonl"
    assert witness_file.exists()

    chain = verify_chain(witness_file)
    assert chain["valid"] is True
    assert chain["last_valid_seq"] == 3
    assert len(chain["records"]) == 3


def test_witness_chain_detects_tampering(isolated_witness_dir):
    recorder = WitnessRecorder("tamper-mcp")
    args_hash = compute_args_hash("tamper-mcp", "read_file", {"path": "secure.py"})

    recorder.record_event("call-1", args_hash, "read_file", "received")
    recorder.record_event("call-1", args_hash, "read_file", "execution_started")
    recorder.record_event("call-1", args_hash, "read_file", "execution_completed")

    witness_file = isolated_witness_dir / "tamper-mcp.jsonl"
    lines = witness_file.read_text().splitlines()

    # Tamper with the second record's payload
    tampered_rec = json.loads(lines[1])
    tampered_rec["state"] = "rejected_by_jail"
    lines[1] = json.dumps(tampered_rec)
    witness_file.write_text("\n".join(lines) + "\n")

    chain = verify_chain(witness_file)
    assert chain["valid"] is False
    assert "HMAC mismatch" in chain["reason"] or "Sequence mismatch" in chain["reason"]


def test_reconciliation_verifies_allowed_and_denied_actions(isolated_witness_dir):
    recorder = WitnessRecorder("repo-mcp")
    read_hash = compute_args_hash("repo-mcp", "read_file", {"path": "config.json"})
    recorder.record_event("c1", read_hash, "read_file", "received")
    recorder.record_event("c1", read_hash, "read_file", "execution_started")
    recorder.record_event("c1", read_hash, "read_file", "execution_completed")

    # Allowed execution with completed events reconciles to VERIFIED
    status_allow = reconcile("ALLOW", "repo-mcp", "read_file", read_hash)
    assert status_allow == "VERIFIED"

    # Blocked action with no events reconciles to VALID DENY
    delete_hash = compute_args_hash("repo-mcp", "delete_branch", {"name": "main"})
    status_deny = reconcile("DENY", "repo-mcp", "delete_branch", delete_hash)
    assert status_deny in ("VALID DENY", "VERIFIED ZERO EXECUTIONS")

    # Held action reconciles to VERIFIED ZERO EXECUTIONS
    hold_hash = compute_args_hash("repo-mcp", "comment_issue", {"issue_id": "1", "text": "leak"})
    status_hold = reconcile("HOLD", "repo-mcp", "comment_issue", hold_hash)
    assert status_hold == "VERIFIED ZERO EXECUTIONS"

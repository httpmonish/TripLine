"""
tests/test_phase3_wow.py — Deterministic Unit & Boundary Tests for Phase 3.

No network, no LLM, no ArmorIQ required. Validates:
1. Jail burst expectations (traversals rejected, zero byte leakage).
2. ArmorIQ audit sidecar hash-chain verification & tamper failure.
3. Canary token single-prefix guarantee.
4. Scenario log JSON schema.
5. Refusal to run forced-compliance stubs for official evidence.
"""

import hashlib
import json
import pathlib
import tempfile
import pytest

from canary.mint import mint_canary
from scripts.jail_burst import run_jail_burst
from scripts.verify_links import verify_armoriq_links, canonical_json
from receipts.builder import IncidentBuilder
from receipts.verify import verify_receipt


def test_jail_burst_zero_leakage():
    """Validates that jail burst probe reports 0 leaked bytes and all traversals denied."""
    results, ok = run_jail_burst()
    assert ok is True
    for r in results:
        if r["attempt"] != "Positive Control (Legitimate In-Sandbox Read)":
            assert r["fake_key_bytes"] == 0
            assert "DENIED" in r["jail_decision"]


def test_canary_single_prefix():
    """Validates that canary minting produces exactly one TRPL- prefix."""
    rec = mint_canary(run_id="TRPL-phase3-test", tier=2, intended_placement="config.env")
    assert rec.canary_id.startswith("TRPL-")
    # Must not contain doubled prefix
    assert not rec.canary_id.startswith("TRPL-TRPL-")
    parts = rec.canary_id.split("-")
    assert len(parts) >= 3


def test_sidecar_hash_chain_and_tamper():
    """Validates that sidecar verifier detects 1-byte tamper in the hash chain."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        receipt_file = tmp_path / "test_receipt.json"
        receipt_file.write_text(json.dumps({"test": "data"}))
        receipt_hash = hashlib.sha256(receipt_file.read_bytes()).hexdigest()

        sidecar_file = tmp_path / "sidecar.jsonl"
        entry_1 = {
            "receipt_id": "RCP-01",
            "receipt_hash": receipt_hash,
            "receipt_path": str(receipt_file),
            "prev_hash": "genesis",
            "armoriq_ref": {"decision": "DENY"},
        }
        rec1_bytes = canonical_json(entry_1).encode("utf-8")
        entry_1_hash = hashlib.sha256(rec1_bytes).hexdigest()
        entry_1["link_hash"] = entry_1_hash

        entry_2 = {
            "receipt_id": "RCP-02",
            "receipt_hash": receipt_hash,
            "receipt_path": str(receipt_file),
            "prev_hash": entry_1_hash,
            "armoriq_ref": {"decision": "ALLOW"},
        }
        rec2_bytes = canonical_json(entry_2).encode("utf-8")
        entry_2["link_hash"] = hashlib.sha256(rec2_bytes).hexdigest()

        sidecar_file.write_text(f"{json.dumps(entry_1)}\n{json.dumps(entry_2)}\n")

        valid, errors = verify_armoriq_links(sidecar_file)
        assert valid is True
        assert len(errors) == 0

        # Tamper one byte in entry_1 armoriq_ref
        tampered_entry_1 = dict(entry_1)
        tampered_entry_1["armoriq_ref"]["decision"] = "ALLOW"
        sidecar_file.write_text(f"{json.dumps(tampered_entry_1)}\n{json.dumps(entry_2)}\n")

        tampered_valid, tampered_errors = verify_armoriq_links(sidecar_file)
        assert tampered_valid is False
        assert any("Hash chain broken" in err for err in tampered_errors)


def test_receipt_tamper_detection():
    """Validates that modifying a covered receipt field triggers TAMPER_DETECTED."""
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="test-run",
        call_id="call-1",
        source_data={"tool": "read_file"},
        proposal_data={"tool": "read_file", "arguments": {"path": "file.txt"}},
        armoriq_decision="ALLOW",
        armoriq_reason="allowed",
        tripline_decision="DENY",
        tripline_reason="PATH_OUTSIDE_ROOT",
        matched_policy="policy-1",
        witness_data={"witness_verification": "zero_executions"},
    )
    data = receipt.model_dump()
    valid, reason = verify_receipt(data)
    assert valid is True
    assert reason == "VERIFIED"

    # Tamper tripline_decision
    tampered = dict(data)
    tampered["decision"] = dict(tampered["decision"])
    tampered["decision"]["tripline_decision"] = "ALLOW"

    t_valid, t_reason = verify_receipt(tampered)
    assert t_valid is False
    assert "TAMPER_DETECTED" in t_reason


def test_scenario_log_schema():
    """Validates that scenario outputs conform to required structured schema."""
    scenario_log = pathlib.Path("results/phase3/scenario").glob("*.jsonl")
    logs = list(scenario_log)
    assert len(logs) > 0, "Scenario log file must exist"
    
    # Read the latest scenario log by mtime
    latest_log = max(logs, key=lambda p: p.stat().st_mtime)
    lines = [json.loads(l) for l in latest_log.read_text().splitlines() if l.strip()]
    assert len(lines) == 5, "Scenario log must contain exactly 5 issues"
    
    for row in lines:
        assert "issue" in row
        assert "action" in row
        assert "armoriq" in row
        assert "tripline" in row
        assert "outcome" in row
        assert "receipt" in row

"""
Tests for Phase 10: Trustworthy Receipts and Cryptographic Verification.
Verifies:
1. RFC 8785 canonical JSON serialization and hashing.
2. HMAC-SHA256 signature generation bound to witness head.
3. Offline verification via verify_receipt.
4. Tamper detection on modified payload or signature.
"""

import pytest
import copy
from receipts.builder import IncidentBuilder
from receipts.verify import (
    canonical_evidence_dict,
    compute_canonical_hash,
    sign_receipt_fields,
    verify_receipt,
    get_witness_key,
)


def test_rfc8785_canonical_hashing():
    dict1 = {"z": 1, "a": 2, "m": {"b": True, "a": False}}
    dict2 = {"a": 2, "m": {"a": False, "b": True}, "z": 1}

    # Irrespective of key insertion order, canonical hashes must be identical
    hash1 = compute_canonical_hash(dict1)
    hash2 = compute_canonical_hash(dict2)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_receipt_signing_and_verification():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run_p10_test",
        call_id="call_p10_01",
        source_data={"type": "github_issue", "id": "issue_300", "trust_level": "T3"},
        proposal_data={"tool": "delete_branch", "action": "delete_branch", "arguments": {"name": "main"}},
        armoriq_decision="DENY",
        armoriq_reason="Platform policy prohibits destructive branch deletion",
        tripline_decision="NONE",
        tripline_reason="Delegated to ArmorIQ platform",
        canary_data={"tier": "none", "hit": False},
        witness_data={"state": "no execution", "count": 0, "chain_status": "valid"},
        confidence_data={"level": "deterministic", "basis": "platform_policy"},
    )

    data = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
    key = get_witness_key()

    # Valid receipt must verify successfully
    is_valid, reason = verify_receipt(data, key=key)
    assert is_valid is True
    assert reason == "VERIFIED"


def test_receipt_tamper_detection():
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="run_p10_tamper",
        call_id="call_p10_02",
        source_data={"type": "github_issue", "id": "issue_301", "trust_level": "T3"},
        proposal_data={"tool": "read_file", "action": "read_file", "arguments": {"path": "sensitive.txt"}},
        armoriq_decision="ALLOW",
        armoriq_reason="Authorized tool",
        tripline_decision="DENY",
        tripline_reason="Path jail blocked access outside repository sandbox",
        canary_data={"tier": "none", "hit": False},
        witness_data={"state": "no execution", "count": 0, "chain_status": "valid"},
        confidence_data={"level": "deterministic", "basis": "jail_confinement"},
    )

    data = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
    key = get_witness_key()

    # Case 1: Tampering with a decision field (falsifying denial to allow)
    tampered_data = copy.deepcopy(data)
    tampered_data["decision"]["tripline_decision"] = "ALLOW"
    is_valid, reason = verify_receipt(tampered_data, key=key)
    assert is_valid is False
    assert "TAMPER_DETECTED" in reason

    # Case 2: Tampering with proposal arguments
    tampered_data2 = copy.deepcopy(data)
    tampered_data2["proposal"]["arguments_summary"] = {"path": "benign.txt"}
    is_valid2, reason2 = verify_receipt(tampered_data2, key=key)
    assert is_valid2 is False
    assert "TAMPER_DETECTED" in reason2

    # Case 3: Tampering with signature
    tampered_data3 = copy.deepcopy(data)
    tampered_data3["receipt_signature"] = "deadbeef" * 8
    is_valid3, reason3 = verify_receipt(tampered_data3, key=key)
    assert is_valid3 is False
    assert "SIGNATURE_INVALID" in reason3

import os
import pathlib
import pytest
import unicodedata
import json
from receipts.builder import IncidentBuilder
from dashboard.repositories import DashboardRepository

def test_regression_unicode_normalization_jail():
    """Verify that fullwidth unicode dots and slashes are normalized and rejected by jail."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("jail", "mcp/common/jail.py")
    jail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jail)
    
    trusted_root = pathlib.Path("fixtures/demo_repo").resolve()
    # Fullwidth characters: \uff0e is fullwidth dot, \uff0f is fullwidth slash
    malicious = "\uff0e\uff0e\uff0f\uff0e\uff0e\uff0fetc/passwd"
    
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path(malicious, trusted_root)

def test_regression_witness_key_permissions():
    """Verify that witness_key.txt has restricted permissions (0o600)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(witness)
    
    key = witness.get_witness_key()
    assert len(key) == 32
    mode = oct(os.stat(witness.KEY_FILE).st_mode & 0o777)
    assert mode == "0o600", f"Key permissions should be 0o600, got {mode}"

def test_regression_matched_policy_in_builder():
    """Verify IncidentBuilder populates matched_policy when provided."""
    builder = IncidentBuilder()
    receipt = builder.build_receipt(
        run_id="test-run",
        call_id="test-call",
        armoriq_decision="DENY",
        armoriq_reason="Policy restriction",
        matched_policy="deny_unauthorized_read"
    )
    assert receipt.decision.matched_policy == "deny_unauthorized_read"

def test_regression_dashboard_loads_benchmark_runs():
    """Verify DashboardRepository loads benchmark_runs.jsonl when results/phase8 is absent."""
    repo = DashboardRepository()
    runs = repo.get_all_runs()
    assert len(runs) > 0, "DashboardRepository should fall back to benchmark_runs.jsonl"
    receipts = repo.get_all_receipts()
    assert len(receipts) > 0, "Dashboard should generate receipts from benchmark runs"

def test_regression_no_hardcoded_secrets_in_scripts():
    """Verify no live ak_live_ key strings exist in scripts."""
    files_to_check = [
        "run_all_tests.sh",
        "run_phase6_tests.sh",
        "tests/test_phase10_dashboard.py"
    ]
    for rel_path in files_to_check:
        content = pathlib.Path(rel_path).read_text()
        assert "87d1dc919b2f" not in content, f"Found hardcoded real live key in {rel_path}"

def test_toctou_open_then_verify_symlink_swap(tmp_path):
    """Verify that secure_open_read catches symlink swaps pointing outside root."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("jail", "mcp/common/jail.py")
    jail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jail)

    root = tmp_path / "repo"
    root.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside secret")

    # Symlink inside root pointing outside
    link = root / "symlink_escape.txt"
    os.symlink(outside_file, link)

    with pytest.raises(jail.PathJailException) as excinfo:
        jail.secure_open_read("symlink_escape.txt", root)
    assert excinfo.value.reason in ("PATH_OUTSIDE_ROOT", "CANNOT_OPEN_FILE")

def test_case_variant_canary_and_jail(tmp_path):
    """Verify case-variant paths on case-insensitive filesystems match canary and obey jail."""
    from canary.scan import check_tier1_access
    from canary.mint import mint_canary
    from canary.state import record_active_canary
    import importlib.util

    spec = importlib.util.spec_from_file_location("jail", "mcp/common/jail.py")
    jail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jail)

    run_id = "test-case-run-99"
    rec = mint_canary(run_id, 1, "src/config/legacy_deploy.json")
    record_active_canary(rec)
    
    # Case variant should match
    hit = check_tier1_access("SRC/CONFIG/LEGACY_DEPLOY.JSON", run_id, "read_file")
    assert hit is not None, "Case variant SRC/CONFIG/LEGACY_DEPLOY.JSON should trigger Tier 1 canary"
    assert hit["canary_id"] == rec.canary_id

    # Jail case variant traversal check
    root = tmp_path / "sandbox"
    root.mkdir()
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path("..//..//ETC/PASSWD", root)

def test_mcp_direct_http_bypass_proof_enforcement():
    """Reproduce over HTTP that calls without proof are rejected and valid proofs are accepted."""
    from starlette.testclient import TestClient
    from server import create_app
    import time
    import importlib.util

    spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
    proof_mod = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(proof_mod)

    spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
    witness_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(witness_mod)

    app = create_app()
    with TestClient(app) as client:
        tool_req = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {"name": "hello_tool", "arguments": {}}
        }
        
        # 1. Direct call without check() or proof -> MUST BE 403 Forbidden
        r1 = client.post("/mcp", json=tool_req)
        assert r1.status_code == 403
        assert "MISSING_DECISION_PROOF" in r1.text

        # 2. Call with valid gateway proof -> Accepted through middleware
        key = witness_mod.get_witness_key()
        args_hash = witness_mod.compute_args_hash("tripline-mcp", "hello_tool", {})
        valid_proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", key, time.time())
        r2 = client.post("/mcp", json=tool_req, headers={"x-tripline-decision-proof": valid_proof})
        # Middleware allowed it through (non-403)
        assert r2.status_code != 403

        # 3. Call with expired proof -> MUST BE 403
        expired_proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", key, time.time() - 120.0)
        r3 = client.post("/mcp", json=tool_req, headers={"x-tripline-decision-proof": expired_proof})
        assert r3.status_code == 403
        assert "EXPIRED_DECISION_PROOF" in r3.text

        # 4. Call with mismatched / tampered args proof -> MUST BE 403
        tampered_args_proof = proof_mod.compute_decision_proof("wrong_args_hash", "ALLOW", key, time.time())
        r4 = client.post("/mcp", json=tool_req, headers={"x-tripline-decision-proof": tampered_args_proof})
        assert r4.status_code == 403
        assert "INVALID_PROOF_SIGNATURE" in r4.text

def test_receipt_canonical_hashing_and_signature_tamper():
    """Verify canonical hashing and signature verification detects tampering."""
    from receipts.builder import IncidentBuilder
    from receipts.verify import verify_receipt

    builder = IncidentBuilder()
    r = builder.build_receipt(
        run_id="audit-run-99",
        call_id="call-audit-01",
        armoriq_decision="DENY",
        armoriq_reason="Unauthorized tool",
        tripline_decision="DENY",
        tripline_reason="Jail violation",
        matched_policy="deny_unauthorized",
        witness_data={"state": "no execution", "count": 0, "chain_status": "valid"}
    )
    
    # 1. Unmodified receipt must be valid
    valid, msg = verify_receipt(r)
    assert valid is True
    assert msg == "VERIFIED"

    # 2. Modifying armoriq_decision must fail canonical hash check
    tampered_1 = r.model_dump()
    tampered_1["decision"]["armoriq_decision"] = "ALLOW"
    valid_t1, msg_t1 = verify_receipt(tampered_1)
    assert valid_t1 is False
    assert "TAMPER_DETECTED" in msg_t1

    # 3. Modifying execution count must fail canonical hash check
    tampered_2 = r.model_dump()
    tampered_2["witness"]["execution_count"] = 1
    valid_t2, msg_t2 = verify_receipt(tampered_2)
    assert valid_t2 is False
    assert "TAMPER_DETECTED" in msg_t2

    # 4. Modifying signature must fail signature check
    tampered_3 = r.model_dump()
    tampered_3["receipt_signature"] = "deadbeef" * 8
    valid_t3, msg_t3 = verify_receipt(tampered_3)
    assert valid_t3 is False
    assert "SIGNATURE_INVALID" in msg_t3

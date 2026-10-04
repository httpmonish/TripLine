import os
import sys
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
    """Reproduce over HTTP that calls without proof are rejected and valid proofs are accepted.

    Uses read_file (an impactful tool that requires a Decision-Proof header).
    hello_tool is in _DIAGNOSTIC_TOOLS and is intentionally exempt from proof
    (equivalent to a /healthz endpoint — side-effect free).

    All requests include Host: 127.0.0.1 so the MCP SDK's DNS rebinding
    protection passes through and lets DecisionProofMiddleware run.
    """
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

    # Host: 127.0.0.1 is required — TestClient sends "testserver" by default,
    # which triggers MCP's DNS rebinding guard (421) before our middleware fires.
    BASE_HEADERS = {"Host": "127.0.0.1"}

    # Use read_file: an impactful tool that MUST be gated by a Decision-Proof.
    # (hello_tool is in _DIAGNOSTIC_TOOLS and is deliberately proof-exempt.)
    tool_req = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "tools/call",
        "params": {"name": "read_file", "arguments": {"path": "fixtures/ok.txt"}}
    }

    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        # 1. Direct call without proof -> MUST BE 403 Forbidden
        r1 = client.post("/mcp", json=tool_req, headers=BASE_HEADERS)
        assert r1.status_code == 403, f"Expected 403, got {r1.status_code}: {r1.text}"
        assert "MISSING_DECISION_PROOF" in r1.text

        # 2. Call with valid gateway proof -> Middleware passes it through (non-403)
        key = witness_mod.get_witness_key()
        args_hash = witness_mod.compute_args_hash(
            "tripline-mcp", "read_file", {"path": "fixtures/ok.txt"}
        )
        valid_proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", key, time.time())
        r2 = client.post(
            "/mcp", json=tool_req,
            headers={**BASE_HEADERS, "x-tripline-decision-proof": valid_proof}
        )
        assert r2.status_code != 403, f"Valid proof should pass middleware, got {r2.status_code}: {r2.text}"

        # 3. Expired proof -> MUST BE 403
        expired_proof = proof_mod.compute_decision_proof(args_hash, "ALLOW", key, time.time() - 120.0)
        r3 = client.post(
            "/mcp", json=tool_req,
            headers={**BASE_HEADERS, "x-tripline-decision-proof": expired_proof}
        )
        assert r3.status_code == 403, f"Expired proof should be 403, got {r3.status_code}"
        assert "EXPIRED_DECISION_PROOF" in r3.text

        # 4. Tampered args proof -> MUST BE 403
        tampered_proof = proof_mod.compute_decision_proof("wrong_args_hash", "ALLOW", key, time.time())
        r4 = client.post(
            "/mcp", json=tool_req,
            headers={**BASE_HEADERS, "x-tripline-decision-proof": tampered_proof}
        )
        assert r4.status_code == 403, f"Tampered proof should be 403, got {r4.status_code}"
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

    # 5. Modifying display-only fields (outside canonical hash) MUST NOT invalidate receipt
    display_edited = r.model_dump()
    display_edited["human_summary"] = "Edited display summary for human operator"
    display_edited["trace_id"] = "TRPL-TRACE-EDITED-999"
    valid_d, msg_d = verify_receipt(display_edited)
    assert valid_d is True, f"Display-only edits should not invalidate signature, got: {msg_d}"
    assert msg_d == "VERIFIED"


def test_jail_six_attack_vectors_block_and_allowed(tmp_path):
    """
    Exhaustive tests for the 6 path jail attack vectors:
    1. Directory-swap race (TOCTOU)
    2. Symlink escape
    3. Null byte injection
    4. NFKC fullwidth normalization
    5. Percent-encoding fixpoint
    6. Case-variant traversal and benign matching
    Each category has BOTH a block test AND a benign-path-allowed test.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("jail", "mcp/common/jail.py")
    jail = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jail)

    root = tmp_path / "sandbox_repo"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('safe')")
    (root / "src" / "hello world.txt").write_text("space ok")
    (root / "config").mkdir()
    (root / "config" / "deploy.json").write_text("{}")

    outside = tmp_path / "outside_secret.txt"
    outside.write_text("SUPER_SECRET")

    # 1. Directory-swap race (TOCTOU)
    # Block: symlink to outside directory
    (root / "bad_dir_link").symlink_to(tmp_path)
    with pytest.raises(jail.PathJailException):
        jail.secure_open_read("bad_dir_link/outside_secret.txt", root)
    # Benign: legitimate internal file open
    fd, real_p = jail.secure_open_read("src/main.py", root)
    assert os.read(fd, 100).decode().startswith("print")
    os.close(fd)

    # 2. Symlink escape
    # Block: symlink pointing directly outside
    (root / "symlink_to_secret").symlink_to(outside)
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path("symlink_to_secret", root)
    # Benign: canonicalize normal file
    p = jail.canonicalize_path("src/main.py", root)
    assert p == (root / "src" / "main.py").resolve()

    # 3. Null byte injection
    # Block: null byte in path string
    with pytest.raises(jail.PathJailException) as exc:
        jail.canonicalize_path("src/main.py\x00/../../outside.txt", root)
    assert exc.value.reason == "NULL_BYTE_IN_PATH"
    # Block: percent-encoded null byte
    with pytest.raises(jail.PathJailException) as exc:
        jail.canonicalize_path("src/main.py%00.txt", root)
    assert exc.value.reason == "NULL_BYTE_IN_PATH"
    # Benign: clean path without null bytes
    assert jail.canonicalize_path("src/main.py", root).exists()

    # 4. NFKC fullwidth normalization
    # Block: fullwidth dots and slashes
    fullwidth_traversal = "\uff0e\uff0e\uff0f\uff0e\uff0e\uff0foutside_secret.txt"
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path(fullwidth_traversal, root)
    # Benign: normal path allowed
    assert jail.canonicalize_path("config/deploy.json", root).exists()

    # 5. Percent-encoding fixpoint
    # Block: double-encoded traversal (%252e%252e%252f -> %2e%2e%2f -> ../)
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path("%252e%252e%252foutside_secret.txt", root)
    # Benign: single-encoded benign character (space as %20)
    p_encoded = jail.canonicalize_path("src/hello%20world.txt", root)
    assert p_encoded.exists()
    assert p_encoded.name == "hello world.txt"

    # 6. Case-variant paths
    # Block: uppercase traversal attempting escape (e.g. ..//..//ETC/PASSWD)
    with pytest.raises(jail.PathJailException):
        jail.canonicalize_path("..//..//ETC/PASSWD", root)
    # Benign: uppercase case variant of benign tracked file inside root (case-insensitive OS)
    p_upper = jail.canonicalize_path("SRC/MAIN.PY", root)
    assert p_upper.exists()
    assert p_upper.read_text() == "print('safe')"
    assert str(p_upper.resolve()).lower() == str((root / "src" / "main.py").resolve()).lower()

def test_no_hardcoded_trace_ids_in_demo_receipts_or_events():
    """Verify that results/demo/ receipts and events do not contain hardcoded trace or call IDs from prepare_demo."""
    demo_dir = pathlib.Path("results/demo")
    if not demo_dir.exists():
        pytest.skip("results/demo does not exist yet (run make demo first)")

    files_to_check = [
        demo_dir / "receipt_DP-01.json",
        demo_dir / "receipt_IE-01.json",
        demo_dir / "events.jsonl",
        demo_dir / "demo_runs.jsonl",
    ]
    
    banned_patterns = [
        "TRPL-TRACE-DP01",
        "TRPL-TRACE-IE01",
        "TRPL-TRACE-001",
        "TRPL-TRACE-002",
        "TRPL-TRACE-M1",
        "call-DP01-live",
        "call-IE01-live",
        "call-DP01-seed",
        "call-IE01-seed",
    ]

    checked_any = False
    for p in files_to_check:
        if p.exists():
            checked_any = True
            content = p.read_text()
            for pattern in banned_patterns:
                assert pattern not in content, f"Found hardcoded pattern '{pattern}' in {p}"
    
    if not checked_any:
        pytest.skip("No demo output files found to inspect")

def test_explain_output_armoriq_allow_and_tripline_decision():
    """Verify that make explain output contains ArmorIQ ALLOW with matched_policy and Tripline decision for IE-01."""
    import subprocess
    demo_dir = pathlib.Path("results/demo")
    events_file = demo_dir / "events.jsonl"
    if not events_file.exists():
        pytest.skip("results/demo/events.jsonl not found (run make demo first)")

    proc = subprocess.run(
        [sys.executable if "sys" in globals() else "python3", "demo/explain.py"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"demo/explain.py failed with: {proc.stderr}"
    out = proc.stdout
    assert "Attack: IE-01" in out, "Expected IE-01 in explain output"
    assert "ARMORIQ      : ALLOW" in out, "Expected ArmorIQ ALLOW in explain output"
    assert "matched_policy" in out, "Expected matched_policy in explain output"
    assert "GATEWAY      : HOLD" in out or "HELD BY TRIPLINE" in out, "Expected Tripline HOLD decision in explain output"

def test_events_monotonic_and_receipt_created_at():
    """Verify monotonic timestamps, INGEST before RECEIPT, and receipt created_at >= last event before RECEIPT."""
    from datetime import datetime
    demo_dir = pathlib.Path("results/demo")
    events_file = demo_dir / "events.jsonl"
    if not events_file.exists():
        pytest.skip("results/demo/events.jsonl not found")
        
    events = [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]
    events_by_trace = {}
    for ev in events:
        events_by_trace.setdefault(ev["trace_id"], []).append(ev)
        
    for trace_id, ev_list in events_by_trace.items():
        # Monotonically non-decreasing
        ts_list = [datetime.fromisoformat(ev["timestamp"]) for ev in ev_list]
        for i in range(len(ts_list) - 1):
            assert ts_list[i+1] >= ts_list[i], f"Timestamp regression in trace {trace_id}: {ts_list[i]} > {ts_list[i+1]}"
            
        stage_names = [ev.get("stage_name") for ev in ev_list]
        assert "INGEST" in stage_names
        assert "RECEIPT" in stage_names
        assert stage_names.index("INGEST") < stage_names.index("RECEIPT")
        
        # Check receipt created_at >= last event before RECEIPT
        receipt_idx = stage_names.index("RECEIPT")
        last_event_ts = ts_list[receipt_idx - 1]
        
        # Determine receipt file
        is_dp = any("issue_42" in str(e) for e in ev_list)
        rcp_file = demo_dir / ("receipt_DP-01.json" if is_dp else "receipt_IE-01.json")
        if rcp_file.exists():
            rcp = json.loads(rcp_file.read_text())
            rcp_created_at = datetime.fromisoformat(rcp["created_at"])
            assert rcp_created_at >= last_event_ts, f"Receipt created_at {rcp_created_at} < last event before RECEIPT {last_event_ts}"

def test_events_and_receipt_field_parity():
    """Verify events decision, matched_policy, and execution counts equal receipt fields."""
    demo_dir = pathlib.Path("results/demo")
    events_file = demo_dir / "events.jsonl"
    if not events_file.exists():
        pytest.skip("results/demo/events.jsonl not found")
        
    events = [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]
    events_by_trace = {}
    for ev in events:
        events_by_trace.setdefault(ev["trace_id"], []).append(ev)
        
    for trace_id, ev_list in events_by_trace.items():
        is_dp = any("issue_42" in str(e) for e in ev_list)
        rcp_file = demo_dir / ("receipt_DP-01.json" if is_dp else "receipt_IE-01.json")
        if not rcp_file.exists():
            continue
        rcp = json.loads(rcp_file.read_text())
        
        armoriq_ev = next(e for e in ev_list if e.get("stage_name") == "ARMORIQ")
        assert armoriq_ev["decision"] == rcp["decision"]["armoriq_decision"]
        assert armoriq_ev["matched_policy"] == rcp["decision"]["matched_policy"]
        
        witness_ev = next(e for e in ev_list if e.get("stage_name") == "WITNESS")
        assert witness_ev["execution_count"] == rcp["witness"]["execution_count"]
        assert witness_ev["decision"] == rcp["decision"]["tripline_decision"]

def test_canary_identity_consistency():
    """Verify canary identity matches between legacy_deploy.json, comment proposal, and receipt."""
    demo_dir = pathlib.Path("results/demo")
    rcp_file = demo_dir / "receipt_IE-01.json"
    deploy_file = demo_dir / "fixtures" / "demo_repo" / "src" / "config" / "legacy_deploy.json"
    if not rcp_file.exists() or not deploy_file.exists():
        pytest.skip("Demo files not found (run make demo first)")
        
    rcp = json.loads(rcp_file.read_text())
    deploy_cfg = json.loads(deploy_file.read_text())
    
    canary_id = rcp["canary"]["canary_id"]
    deployment_key = deploy_cfg.get("deployment_key", "")
    comment_text = rcp["proposal"]["arguments_summary"].get("text", "")
    
    assert canary_id in deployment_key, f"canary_id {canary_id} not in legacy_deploy deployment_key {deployment_key}"
    assert canary_id in comment_text, f"canary_id {canary_id} not in comment text {comment_text}"

def test_tamper_all_10_canonical_fields():
    """Verify that tampering with any of the 10 canonical evidence fields triggers TAMPER_DETECTED."""
    from receipts.verify import verify_receipt
    demo_dir = pathlib.Path("results/demo")
    rcp_file = demo_dir / "receipt_DP-01.json"
    if not rcp_file.exists():
        pytest.skip("receipt_DP-01.json not found")
        
    canonical_fields = [
        "receipt_id",
        "incident_id",
        "run_id",
        "created_at",
        "source",
        "proposal",
        "decision",
        "canary",
        "witness",
        "confidence"
    ]
    
    original_dict = json.loads(rcp_file.read_text())
    
    # Baseline valid
    valid, reason = verify_receipt(original_dict)
    assert valid is True, f"Original receipt should be valid, got: {reason}"
    
    for field in canonical_fields:
        tampered = json.loads(json.dumps(original_dict))
        if isinstance(tampered[field], dict):
            tampered[field]["tampered"] = True
        else:
            tampered[field] = str(tampered[field]) + "_tampered"
            
        valid, reason = verify_receipt(tampered)
        assert valid is False, f"Tampering with {field} did not fail verification"
        assert "TAMPER_DETECTED" in reason, f"Tampering with {field} gave unexpected reason: {reason}"

def test_replan_lock_blocks_second_start_plan_after_untrusted_ingestion():
    """Independently demonstrate replan lock blocking new authority after untrusted ingestion."""
    from gateway.replan_lock import ReplanLock
    lock = ReplanLock()
    
    # 1. Plan before ingest
    lock.on_plan_created({"steps": ["read_project_info"]})
    lock.on_authorization_granted()
    
    # Before untrusted ingestion, replan request allowed
    res_clean = lock.check_replan_request()
    assert res_clean.get("status") == "allowed"
    
    # 2. Untrusted content ingested
    lock.on_t3_read(source="fixtures/demo_repo/issues/issue_42.json")
    assert lock.t3_ingested is True
    
    # 3. Agent attempts replan
    res_blocked = lock.check_replan_request()
    assert res_blocked["event"] == "replan_blocked"
    assert res_blocked["reason"] == "replan_after_untrusted_ingestion"
    assert res_blocked["execution"] == "not_started"



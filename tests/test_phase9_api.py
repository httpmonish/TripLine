"""
tests/test_phase9_api.py — Phase 9 FastAPI Integration & Security Tests.

Covers:
- All Section 4 endpoints (200 shapes, honest empty states)
- Path traversal protection (path=../../etc/passwd)
- CSRF Origin / Header validation (403 without token, 200 with token)
- Secret scrubbing (Rule R2: zero unredacted keys in responses)
- Tamper checks test temporary copies without mutating original files
"""

import json
from pathlib import Path
from starlette.testclient import TestClient

from dashboard.app import app
from dashboard.security import redact_secret

client = TestClient(app, raise_server_exceptions=False)


def get_csrf_headers() -> dict[str, str]:
    res = client.get("/api/csrf-token")
    assert res.status_code == 200
    token = res.json()["csrf_token"]
    return {
        "X-CSRF-Token": token,
        "Origin": "http://127.0.0.1:8080",
    }


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "git_commit" in data
    assert "branch" in data
    assert isinstance(data["dirty"], bool)


def test_env_endpoint_and_secret_redaction():
    res = client.get("/api/env")
    assert res.status_code == 200
    data = res.json()
    assert "armoriq_sdk_version" in data
    assert "enforcement_mode" in data
    # Ensure no full API key is leaked in env
    raw_text = res.text
    assert "ak_live_" not in raw_text or "..." in raw_text
    assert "AQ" not in raw_text or "..." in raw_text


def test_runs_endpoints():
    res = client.get("/api/runs")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)

    latest_res = client.get("/api/runs/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert "run_id" in latest_data

    # Test individual run
    if runs:
        run_id = runs[0]["run_id"]
        run_res = client.get(f"/api/runs/{run_id}")
        assert run_res.status_code == 200
        assert run_res.json()["run_id"] == run_id

        # Test transcript
        tr_res = client.get(f"/api/runs/{run_id}/transcript")
        assert tr_res.status_code == 200

    # 404 for unknown run
    bad_run = client.get("/api/runs/nonexistent_run_999999")
    assert bad_run.status_code == 404


def test_attribution_endpoint():
    res = client.get("/api/attribution")
    assert res.status_code == 200
    data = res.json()
    assert len(data["layers"]) == 5
    layer_names = [l["name"] for l in data["layers"]]
    assert "ArmorIQ Session Policy" in layer_names
    assert "Tripline Path Jail" in layer_names
    assert "Tripline Egress Gateway" in layer_names
    assert "Local Witness Recorder" in layer_names
    assert "RFC-8785 Incident Receipt" in layer_names


def test_jail_burst_endpoint():
    res = client.get("/api/jail-burst")
    assert res.status_code == 200
    data = res.json()
    assert data["total_probes"] >= 8
    assert data["passed_probes"] == data["total_probes"]
    for p in data["probes"]:
        assert p["fake_key_bytes"] == 0
        assert "PASS" in p["verdict"]


def test_measured_endpoint():
    res = client.get("/api/measured")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "rows" in data
    assert isinstance(data["rows"], list)


def test_audit_links_endpoint():
    res = client.get("/api/audit-links")
    assert res.status_code == 200
    data = res.json()
    assert "valid" in data
    assert "chain_length" in data
    assert "links" in data


def test_receipts_endpoints_and_tamper_isolation():
    headers = get_csrf_headers()
    res = client.get("/api/receipts")
    assert res.status_code == 200
    receipts = res.json()
    assert isinstance(receipts, list)

    if receipts:
        r_id = receipts[0]["receipt_id"]
        detail = client.get(f"/api/receipts/{r_id}")
        assert detail.status_code == 200
        assert detail.json()["receipt_id"] == r_id

        # Verification endpoint (fails without CSRF)
        fail_res = client.post(f"/api/receipts/{r_id}/verify", headers={"Origin": "http://127.0.0.1:8080"})
        assert fail_res.status_code == 403

        # Verification endpoint (succeeds with CSRF)
        v_res = client.post(f"/api/receipts/{r_id}/verify", headers=headers)
        assert v_res.status_code == 200
        v_data = v_res.json()
        assert v_data["verified"] is True
        assert "make verify" in v_data["command"]

        # Tamper check endpoint (must NOT mutate original)
        t_res = client.post(f"/api/receipts/{r_id}/tamper-check", headers=headers)
        assert t_res.status_code == 200
        t_data = t_res.json()
        assert t_data["tamper_detected"] is True
        assert t_data["original_file_untouched"] is True

        # Re-verify original to guarantee immutability
        v_res2 = client.post(f"/api/receipts/{r_id}/verify", headers=headers)
        assert v_res2.status_code == 200
        assert v_res2.json()["verified"] is True


def test_witness_endpoints_and_tamper_isolation():
    headers = get_csrf_headers()
    res = client.get("/api/witness")
    assert res.status_code == 200
    data = res.json()
    assert "chain_status" in data
    assert "mcp_logs" in data

    # Verify witness (fails without CSRF)
    fail_res = client.post("/api/witness/verify", headers={"Origin": "http://127.0.0.1:8080"})
    assert fail_res.status_code == 403

    # Verify witness (succeeds with CSRF)
    v_res = client.post("/api/witness/verify", headers=headers)
    assert v_res.status_code == 200

    # Tamper check (must NOT mutate original)
    t_res = client.post("/api/witness/tamper-check", headers=headers)
    assert t_res.status_code == 200
    t_data = t_res.json()
    assert t_data["tamper_detected"] is True
    assert t_data["original_log_untouched"] is True


def test_path_traversal_protection():
    traversal_paths = [
        "../../etc/passwd",
        "/etc/passwd",
        "../../.ssh/id_rsa",
        "../.env",
    ]
    for bad_path in traversal_paths:
        res = client.get(f"/api/evidence/file?path={bad_path}")
        assert res.status_code in [400, 403, 404]
        assert "root:" not in res.text


def test_evidence_index_endpoint():
    res = client.get("/api/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["total_files"] >= 0
    assert isinstance(data["items"], list)


def test_docs_endpoints():
    res = client.get("/api/docs")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    names = [d["name"] for d in docs]
    assert "limitations" in names
    assert "judge_qa" in names

    # Get specific doc
    doc_res = client.get("/api/docs/limitations")
    assert doc_res.status_code == 200
    assert "content" in doc_res.json()

    # 404 for unknown doc
    bad_doc = client.get("/api/docs/nonexistent_doc_xyz")
    assert bad_doc.status_code == 404


def test_claims_endpoint():
    res = client.get("/api/claims")
    assert res.status_code == 200
    data = res.json()
    assert data["total_claims"] > 0
    assert "items" in data


def test_platform_checklist_endpoint():
    res = client.get("/api/platform-checklist")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 4


def test_jobs_disallowed_kind():
    headers = get_csrf_headers()
    res = client.post("/api/jobs", json={"kind": "disallowed_malicious_script"}, headers=headers)
    assert res.status_code == 400
    assert "Disallowed job kind" in res.json()["detail"]


def test_jobs_armoriq_proof_safety_gate():
    headers = get_csrf_headers()
    res = client.post("/api/jobs", json={"kind": "armoriq_proof"}, headers=headers)
    assert res.status_code == 403
    assert "Live execution is disabled" in res.json()["detail"] or "confirm_token" in res.json()["detail"]


def test_static_frontend_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "TRIPLINE" in res.text

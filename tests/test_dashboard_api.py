import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from dashboard.app import app

client = TestClient(app)


def test_api_summary():
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_receipts" in data
    assert "total_runs" in data
    assert "total_benchmark_runs" in data
    assert "total_blocked" in data
    assert "total_held" in data
    assert isinstance(data["total_receipts"], int)
    assert isinstance(data["total_runs"], int)


def test_api_receipts_list():
    response = client.get("/api/receipts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        r = data[0]
        assert "receipt_id" in r
        assert "decision" in r
        assert "canonical_hash" in r
        assert "receipt_signature" in r


def test_api_receipt_detail_real_and_404():
    list_res = client.get("/api/receipts")
    receipts = list_res.json()
    if receipts:
        real_id = receipts[0]["receipt_id"]
        res = client.get(f"/api/receipts/{real_id}")
        assert res.status_code == 200
        rcpt = res.json()
        assert rcpt["receipt_id"] == real_id
        assert "source" in rcpt
        assert "proposal" in rcpt
        assert "decision" in rcpt
        assert "canary" in rcpt
        assert "witness" in rcpt
        assert "confidence" in rcpt

    # Unknown ID -> 404
    not_found_res = client.get("/api/receipts/RCP-nonexistent-id-12345")
    assert not_found_res.status_code == 404
    assert "detail" in not_found_res.json()


def test_api_receipt_detail_rejection_of_malicious_id():
    res1 = client.get("/api/receipts/../../etc/passwd")
    assert res1.status_code in (400, 404)

    res2 = client.get("/api/receipts/..%2F..%2Fetc%2Fpasswd")
    assert res2.status_code in (400, 404)


def test_api_receipt_verify_endpoint():
    list_res = client.get("/api/receipts")
    receipts = list_res.json()
    if receipts:
        real_id = receipts[0]["receipt_id"]
        res = client.get(f"/api/receipts/{real_id}/verify")
        assert res.status_code == 200
        v_data = res.json()
        assert v_data["receipt_id"] == real_id
        assert v_data["verified"] is True
        assert v_data["reason"] == "VERIFIED"
        assert "make verify FILE=" in v_data["command"]

    # 404 for unknown receipt verify
    res_404 = client.get("/api/receipts/RCP-unknown-receipt/verify")
    assert res_404.status_code == 404

    # 400 for malicious ID
    res_malicious = client.get("/api/receipts/..%2Fevil/verify")
    assert res_malicious.status_code in (400, 404)


def test_api_runs_list():
    response = client.get("/api/runs")
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)
    if runs:
        r = runs[0]
        assert "run_id" in r
        assert "class" in r
        assert "decision" in r


def test_api_run_detail_real_and_404():
    runs_res = client.get("/api/runs")
    runs = runs_res.json()
    if runs:
        real_run_id = runs[0]["run_id"]
        res = client.get(f"/api/runs/{real_run_id}")
        assert res.status_code == 200
        run_data = res.json()
        assert run_data["run_id"] == real_run_id
        assert "events" in run_data

    # Unknown run -> 404
    res_unknown = client.get("/api/runs/TRPL-UNKNOWN-999")
    assert res_unknown.status_code == 404

    # Malicious run ID
    res_malicious = client.get("/api/runs/..%2F..%2Froot")
    assert res_malicious.status_code in (400, 404)


def test_api_events_endpoint():
    res = client.get("/api/events")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)

    if events:
        trace_id = events[0].get("trace_id")
        if trace_id:
            filtered_res = client.get(f"/api/events?trace_id={trace_id}")
            assert filtered_res.status_code == 200
            for ev in filtered_res.json():
                assert ev.get("trace_id") == trace_id


def test_api_scoreboard_returns_nulls_for_missing_outcome():
    response = client.get("/api/scoreboard")
    assert response.status_code == 200
    data = response.json()
    assert "arms" in data
    # Assert missing_field is "outcome" and arm outcome counts are null (not fabricated zeroes)
    if data.get("missing_field") == "outcome":
        for arm in ["A", "B", "C"]:
            if arm in data["arms"]:
                arm_stats = data["arms"][arm]
                assert arm_stats["succeeded"] is None
                assert arm_stats["blocked"] is None
                assert arm_stats["held"] is None


def test_api_boundary_endpoint():
    response = client.get("/api/boundary")
    assert response.status_code == 200
    data = response.json()
    assert "responsibilities" in data
    assert "armoriq" in data["responsibilities"]
    assert "tripline" in data["responsibilities"]


def test_api_limitations_and_status():
    res_lim = client.get("/api/limitations")
    assert res_lim.status_code == 200
    assert "content" in res_lim.json()
    assert len(res_lim.json()["content"]) > 0

    res_stat = client.get("/api/status")
    assert res_stat.status_code == 200
    assert "content" in res_stat.json()
    assert len(res_stat.json()["content"]) > 0


def test_api_canary_hits():
    response = client.get("/api/canary-hits")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_witness_endpoint():
    events_res = client.get("/api/events")
    events = events_res.json()
    trace_id = events[0].get("trace_id") if events else "TRPL-TRACE-demo"

    response = client.get(f"/api/witness/{trace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert "chain_status" in data
    assert "executions" in data


def test_no_secrets_in_any_api_response():
    # Read witness key to ensure it is NEVER leaked in any API response
    key_file = Path(".tripline/witness_key.txt")
    key_hex = ""
    if key_file.exists():
        key_hex = key_file.read_bytes().hex()

    endpoints = [
        "/api/summary",
        "/api/receipts",
        "/api/runs",
        "/api/events",
        "/api/scoreboard",
        "/api/boundary",
        "/api/limitations",
        "/api/status",
        "/api/canary-hits",
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        text = res.text
        # Assert no real secret key pattern
        assert "ak_live_" not in text, f"Secret pattern ak_live_ found in {ep}"
        assert "sk_live_" not in text, f"Secret pattern sk_live_ found in {ep}"
        if key_hex:
            assert key_hex not in text, f"Witness raw key hex found in {ep}"


def test_empty_data_handling():
    # Calling endpoints with unknown trace IDs returns empty/valid responses, never 500
    res_events = client.get("/api/events?trace_id=TRPL-TRACE-nonexistent")
    assert res_events.status_code == 200
    assert res_events.json() == []

    res_witness = client.get("/api/witness/TRPL-TRACE-nonexistent")
    assert res_witness.status_code == 200
    assert res_witness.json()["chain_status"] == "valid"


def test_api_rea_targets():
    res = client.get("/api/rea/targets")
    assert res.status_code == 200
    data = res.json()
    assert "targets" in data
    assert len(data["targets"]) > 0
    target_ids = [t["id"] for t in data["targets"]]
    assert "synthetic-electron-app" in target_ids or "synthetic_electron_app" in target_ids


def test_api_rea_investigations():
    res = client.get("/api/rea/investigations")
    assert res.status_code == 200
    invs = res.json()
    assert isinstance(invs, list)
    if invs:
        first = invs[0]
        assert "run_id" in first
        run_id = first["run_id"]
        res_detail = client.get(f"/api/rea/investigations/{run_id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["run_id"] == run_id

    # 404 on nonexistent investigation
    res_404 = client.get("/api/rea/investigations/inv-nonexistent-123456")
    assert res_404.status_code == 404

    # 400 on traversal
    res_malicious = client.get("/api/rea/investigations/..%2F..%2Fetc%2Fpasswd")
    assert res_malicious.status_code in (400, 404)


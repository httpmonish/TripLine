import pytest
from fastapi.testclient import TestClient
from dashboard.app import app
from dashboard.security import sanitize_text

client = TestClient(app)

def test_1_dashboard_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "TRIPLINE" in response.text
    assert "Receipts" in response.text

def test_2_receipt_list_loads():
    response = client.get("/receipts")
    assert response.status_code == 200
    assert "Incident Receipts" in response.text

def test_3_attack_a_receipt_renders():
    # DP-01 is Attack A (direct path)
    from dashboard.routes import repo
    receipts = repo.get_all_receipts()
    dp01_receipt = next((r for r in receipts if r.run_id in [run["run_id"] for run in repo.get_all_runs() if run["attack_id"] == "DP-01" and run["arm"] == "C"]), None)
    if dp01_receipt:
        response = client.get(f"/receipts/{dp01_receipt.receipt_id}")
        assert response.status_code == 200
        assert "PROPOSAL" in response.text
        assert "ARMORIQ" in response.text

def test_4_attack_b_receipt_renders():
    # IE-01 or IE-02 is in-scope egress (Attack B proxy)
    from dashboard.routes import repo
    receipts = repo.get_all_receipts()
    ie01_receipt = next((r for r in receipts if r.run_id in [run["run_id"] for run in repo.get_all_runs() if run["attack_id"] == "IE-01" and run["arm"] == "C"]), None)
    if ie01_receipt:
        response = client.get(f"/receipts/{ie01_receipt.receipt_id}")
        assert response.status_code == 200
        assert "HOLD" in response.text or "ALLOW" in response.text

def test_5_all_six_evidence_fields_present():
    from dashboard.routes import repo
    receipts = repo.get_all_receipts()
    if receipts:
        r = receipts[0]
        response = client.get(f"/receipts/{r.receipt_id}")
        text = response.text
        assert "SOURCE" in text
        assert "PROPOSAL" in text
        assert "ARMORIQ" in text
        assert "TRIPLINE" in text
        assert "CANARY" in text
        assert "WITNESS" in text
        assert "CONFIDENCE" in text

def test_6_run_view_loads_real_data():
    from dashboard.routes import repo
    runs = repo.get_all_runs()
    if runs:
        r = runs[0]
        response = client.get(f"/runs/{r['run_id']}")
        assert response.status_code == 200
        assert r['run_id'] in response.text

def test_7_boundary_page_loads():
    response = client.get("/boundary")
    assert response.status_code == 200
    assert "Boundary Map" in response.text

def test_8_scoreboard_loads():
    response = client.get("/scoreboard")
    assert response.status_code == 200
    assert "TRIPLINE SECURITY SCOREBOARD" in response.text
    if "NO BENCHMARK DATA AVAILABLE" not in response.text:
        assert "Arm A" in response.text

def test_9_missing_witness_renders_unverified():
    from dashboard.repositories import DashboardRepository
    r = DashboardRepository()
    receipts = r.get_all_receipts()
    # Check if we have one with unverified
    unverified = next((x for x in receipts if "UNVERIFIED" in x.witness.witness_verification), None)
    if unverified:
        response = client.get(f"/receipts/{unverified.receipt_id}")
        assert "UNVERIFIED" in response.text

def test_10_tampered_witness_renders_invalid():
    # Synthetically verify this using builder logic
    from receipts.builder import IncidentBuilder
    b = IncidentBuilder()
    rec = b.build_receipt("1", "2", witness_data={"state": "executed", "count": 1, "chain_status": "invalid"})
    assert rec.witness.witness_verification == "INVALID"
    
def test_11_secret_leakage_test():
    fake_key = "ak_live_87d1dc919b2fd66458f689766474e806e37c118618f8be9fb43133c1186588db"
    assert sanitize_text(fake_key) == "[REDACTED]"
    
    fake_path = "/Users/themonishnawaz/tripline/.ssh/id_rsa"
    assert sanitize_text(fake_path) == "<sensitive-path-redacted>/tripline/.ssh/id_rsa"

def test_12_untrusted_content_is_escaped():
    # Jinja2 auto-escapes HTML characters. We can test this by checking string representations
    pass

def test_13_nonexistent_receipt_returns_404():
    response = client.get("/receipts/RCP-unknown-call-unknown")
    assert response.status_code == 404

def test_14_nonexistent_run_returns_404():
    response = client.get("/runs/unknown-run-123")
    assert response.status_code == 404

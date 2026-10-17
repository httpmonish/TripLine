"""
tests/test_scrollytelling_architecture.py — Verification of the Scroll-Driven Scrollytelling Walkthrough
"""

import pathlib
import pytest
from starlette.testclient import TestClient
from dashboard.app import app

client = TestClient(app)


def test_home_page_embeds_scrollytelling_architecture():
    """Verify that the homepage embeds the orange 3D scrollytelling visual."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Check header
    assert "See where an action stops" in html

    # Check 5 stages / chapters
    assert "Ingress" in html
    assert "ArmorIQ Gate" in html or "ArmorIQ Upstream Policy Gate" in html
    assert "Containment" in html or "TripLine Containment Sandbox" in html
    assert "Tool Execution" in html or "Protected Dispatch Boundary" in html
    assert "Evidence" in html or "Cryptographic Witness Log &amp; Evidence" in html

    # Check 4 scenarios
    assert "Out-of-plan block" in html
    assert "Path traversal" in html
    assert "Canary exfiltration" in html
    assert "Authorized read" in html


def test_how_it_works_embeds_scrollytelling_architecture():
    """Verify that /how-it-works also embeds the orange 3D execution architecture."""
    res = client.get("/how-it-works")
    assert res.status_code == 200
    html = res.text
    assert "See where an action stops" in html or "ARCHITECTURE WALKTHROUGH" in html or "SCROLL-DRIVEN EXECUTION" in html
    assert "Out-of-plan block" in html
    assert "Path traversal" in html
    assert "Canary exfiltration" in html
    assert "Authorized read" in html


def test_authentic_code_references_in_markup():
    """Verify the scrollytelling visual references real repository paths."""
    res = client.get("/")
    html = res.text
    assert "agent/planner_v2.py" in html or "agent/core_v2.py" in html
    assert "agent/executor.py" in html
    assert "common/jail.py" in html
    assert "canary/scan.py" in html
    assert "receipts/builder.py" in html


def test_authentic_scenario_receipt_api_resolution():
    """Verify that the authentic receipts referenced by the scenarios can be retrieved and verified via API."""
    scenario_files = [
        "receipt_P1_ARMORIQ_DENY.json",
        "receipt_P2_JAIL_DENY.json",
        "receipt_P3_GATEWAY_HOLD.json",
    ]
    for sf in scenario_files:
        res = client.get(f"/api/receipts/{sf}")
        assert res.status_code == 200, f"Receipt file {sf} not found via API"
        data = res.json()
        assert "receipt_id" in data
        assert "canonical_hash" in data["data"]
        assert len(data["data"]["canonical_hash"]) == 64

        # Verify receipt via verify endpoint
        rcpt_id = data["receipt_id"]
        v_res = client.get(f"/api/receipts/{rcpt_id}/verify")
        assert v_res.status_code == 200
        v_data = v_res.json()
        assert v_data["verified"] is True
        assert v_data["status"] == "VERIFIED"

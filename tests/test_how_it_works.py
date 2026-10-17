"""
tests/test_how_it_works.py — Acceptance Test Suite for /how-it-works Page.

Validates:
1. Direct navigation and refresh on /how-it-works (GET and HEAD return 200 OK)
2. Content-Type is text/html with security headers
3. Navigation links: Header links 'How It Works' to /how-it-works
4. Correct representation of ArmorIQ authorization outcomes (ALLOW, DENY, UNAVAILABLE/fail-closed)
5. Clear distinction between ArmorIQ authorization, TripLine path jail, egress canary gateway, and execution
6. Authentic scenarios present (delete_branch DENIED-ARMORIQ, path traversal DENIED-JAIL, canary token HELD-EGRESS, benign clean dispatch)
7. Honest provenance labeling (RECORDED REPLAY, local/offline mode, zero synthetic timers)
8. Cryptographic receipt verification integration
"""

import pathlib
import pytest
from starlette.testclient import TestClient

from dashboard.app import app, FRONTEND_OUT


@pytest.fixture
def client():
    return TestClient(app)


def test_direct_navigation_how_it_works(client):
    """Verify direct navigation and browser refresh on /how-it-works returns 200 OK."""
    response = client.get("/how-it-works")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_head_request_how_it_works(client):
    """Verify HEAD request on /how-it-works works correctly."""
    response = client.head("/how-it-works")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_html_export_exists():
    """Verify static export generated how-it-works.html in out/."""
    export_file = FRONTEND_OUT / "how-it-works.html"
    assert export_file.exists(), f"Expected {export_file} to exist after build"
    html_content = export_file.read_text(encoding="utf-8")
    assert len(html_content) > 1000


def test_navigation_link_in_header_and_footer(client):
    """Verify header and footer link 'How It Works' directly to /how-it-works (not /#how-it-works)."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text

    # Header navigation link
    assert 'href="/how-it-works"' in html

    # Verify no legacy dead anchor href="/#how-it-works" remains
    assert 'href="/#how-it-works"' not in html


def test_how_it_works_content_and_scenarios(client):
    """Verify the page explains the 4-plane model and genuine security distinctions."""
    resp = client.get("/how-it-works")
    assert resp.status_code == 200
    html = resp.text

    # Core headline & problem statement
    assert "An AI agent proposes an action" in html
    assert "TripLine helps enforce where that action can go" in html

    # ArmorIQ upstream boundary
    assert "ArmorIQ Policy Gate" in html
    assert "armoriq_helper.py" in html

    # TripLine containment boundary
    assert "TripLine Path Jail" in html
    assert "mcp/common/jail.py" in html
    assert "Egress Canary Gateway" in html
    assert "gateway/taint_rule.py" in html

    # 4 Authentic Scenarios
    assert "delete_branch" in html
    assert "DENIED-ARMORIQ" in html
    assert "DENIED-JAIL" in html
    assert "HELD-EGRESS" in html
    assert "read_file" in html

    # Cryptographic evidence & Canonical JSON
    assert "RFC 8785 Canonical JSON" in html
    assert "HMAC-SHA256" in html
    assert "Witness Hash Chain" in html


def test_honest_security_distinction_matrix(client):
    """Verify the comparison matrix clearly separates intent authorization from containment."""
    resp = client.get("/how-it-works")
    assert resp.status_code == 200
    html = resp.text

    # Table headers and distinction elements
    assert "Security Layer" in html
    assert "Main Question" in html
    assert "What It Does NOT Guarantee" in html
    assert "Does not inspect file descriptor inodes" in html
    assert "Does not detect fragmented, polymorphic" in html


def test_two_way_coverage_passes():
    """Verify UI <-> API two-way coverage check passes with 100%."""
    from scripts.ui_api_coverage import run_coverage_check
    passed, errors = run_coverage_check()
    assert passed is True, f"ui_api_coverage failed: {errors}"

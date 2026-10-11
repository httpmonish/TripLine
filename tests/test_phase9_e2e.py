"""
tests/test_phase9_e2e.py — Phase 9 End-to-End and Integration Contract Tests.

Validates:
1. Static HTML delivery via FastAPI root mount
2. Static HTML bundle contains required forensic branding, tabs, and layout
3. Static bundle and React code contain every data-testid and data-api binding
4. Zero missing endpoints across the entire UI surface
"""

import re
from pathlib import Path
from starlette.testclient import TestClient

from dashboard.app import app

client = TestClient(app, raise_server_exceptions=False)
REPO_ROOT = Path(__file__).resolve().parent.parent


def test_e2e_root_page_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    html = res.text
    assert "TRIPLINE" in html
    assert "Blocked isn't evidence" in html or "Blocked isn&#x27;t evidence" in html or "Blocked isn&apos;t evidence" in html


def test_e2e_static_assets_served():
    out_dir = REPO_ROOT / "tripline-frontend" / "out"
    assert (out_dir / "index.html").exists(), "Frontend static export must exist"
    
    # Check that Next.js static assets directory exists
    assert (out_dir / "_next").exists()


def test_e2e_all_tabs_and_data_attributes():
    page_tsx = (REPO_ROOT / "tripline-frontend" / "app" / "page.tsx").read_text(encoding="utf-8")
    
    # Required tabs
    required_tabs = [
        "nav-overview",
        "nav-console",
        "nav-attribution",
        "nav-burst",
        "nav-receipts",
        "nav-witness",
        "nav-measured",
        "nav-evidence",
        "nav-video",
        "nav-claims",
        "nav-platform",
        "nav-about",
    ]
    for tab in required_tabs:
        assert f'data-testid="{tab}"' in page_tsx, f"Missing tab nav testid: {tab}"

    # Required action buttons
    required_actions = [
        "btn-inspect-env",
        "btn-refresh-runs",
        "btn-load-latest-run",
        "btn-view-run-transcript",
        "btn-start-job",
        "btn-cancel-job",
        "btn-refresh-burst",
        "btn-refresh-receipts",
        "btn-audit-links",
        "btn-verify-receipt",
        "btn-tamper-receipt",
        "btn-verify-witness",
        "btn-tamper-witness",
        "btn-list-docs",
    ]
    for action in required_actions:
        assert f'data-testid="{action}"' in page_tsx, f"Missing action testid: {action}"


def test_e2e_ui_api_coverage_passes():
    from scripts.ui_api_coverage import run_coverage_check
    ok, errors = run_coverage_check()
    assert ok, f"UI <-> API coverage check failed: {errors}"
    assert len(errors) == 0


def test_e2e_backend_capability_coverage_passes():
    from scripts.capability_coverage import check_capability_coverage
    ok, errors = check_capability_coverage()
    assert ok, f"Backend capabilities missing coverage: {errors}"

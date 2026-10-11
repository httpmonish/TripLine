"""
tests/test_brand.py — Comprehensive tests for Tripline brand asset integration.

Verifies:
1. All authoritative brand assets exist in assets/brand/.
2. Synchronized copies in dashboard/static/brand/ and tripline-frontend/public/ match SHA-256 byte-for-byte.
3. Zero remote/CDN references in templates, frontend pages, layout, and stylesheets.
4. Header brand link and image alt text in frontend and legacy dashboard.
5. Third-party licensing documentation and OFL notice.
"""

import hashlib
import pathlib
import re
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS_BRAND = REPO_ROOT / "assets" / "brand"
FRONTEND_PUBLIC = REPO_ROOT / "tripline-frontend" / "public"
DASHBOARD_STATIC_BRAND = REPO_ROOT / "dashboard" / "static" / "brand"

BRAND_CORE_FILES = [
    "tripline-mark-dark.svg",
    "tripline-mark-light.svg",
    "tripline-mark-bare.svg",
    "tripline-lockup-on-light.svg",
    "tripline-lockup-on-dark.svg",
    "tripline-favicon.svg",
    "tripline-mark-512.png",
    "tripline-favicon-32.png",
    "tripline-apple-touch-180.png",
    "tripline-lockup-on-light.png",
    "tripline-lockup-on-dark.png",
    "social-preview-1280x640.png",
    "LOGO_NOTES.md",
    "README.md",
    "OFL.txt",
]


def sha256_of_file(path: pathlib.Path) -> str:
    assert path.is_file(), f"File does not exist: {path}"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_authoritative_brand_assets_exist():
    """Verify all primary brand assets exist in assets/brand/."""
    for filename in BRAND_CORE_FILES:
        asset_path = ASSETS_BRAND / filename
        assert asset_path.exists(), f"Missing authoritative brand asset: {asset_path}"
        assert asset_path.stat().st_size > 0, f"Empty brand asset: {asset_path}"


def test_sha256_byte_for_byte_equivalence():
    """Verify synchronized copies in public and static/brand match assets/brand exactly."""
    synced_files = [
        "tripline-mark-dark.svg",
        "tripline-mark-light.svg",
        "tripline-mark-bare.svg",
        "tripline-lockup-on-light.svg",
        "tripline-lockup-on-dark.svg",
        "tripline-favicon.svg",
        "tripline-mark-512.png",
        "tripline-favicon-32.png",
        "tripline-apple-touch-180.png",
        "tripline-lockup-on-light.png",
        "tripline-lockup-on-dark.png",
        "social-preview-1280x640.png",
        "LOGO_NOTES.md",
    ]
    for filename in synced_files:
        src = ASSETS_BRAND / filename
        src_hash = sha256_of_file(src)

        # Check frontend public copy
        dst_fe = FRONTEND_PUBLIC / filename
        assert dst_fe.exists(), f"Frontend copy missing: {dst_fe}"
        assert sha256_of_file(dst_fe) == src_hash, f"SHA-256 mismatch for frontend {filename}"

        # Check legacy dashboard static copy
        dst_db = DASHBOARD_STATIC_BRAND / filename
        assert dst_db.exists(), f"Dashboard copy missing: {dst_db}"
        assert sha256_of_file(dst_db) == src_hash, f"SHA-256 mismatch for dashboard {filename}"


def test_zero_remote_urls_for_brand_and_styles():
    """Ensure no CDN or external URLs are used for brand assets or stylesheets."""
    files_to_check = [
        REPO_ROOT / "tripline-frontend" / "app" / "page.tsx",
        REPO_ROOT / "tripline-frontend" / "app" / "layout.tsx",
        REPO_ROOT / "tripline-frontend" / "app" / "globals.css",
        REPO_ROOT / "dashboard" / "templates" / "base.html",
        REPO_ROOT / "dashboard" / "static" / "tripline.css",
    ]
    remote_pattern = re.compile(r"""(?:https?://|//)[^"'\s)]+(?:\.(?:svg|png|jpg|jpeg|ico|woff2?|ttf|css))""", re.IGNORECASE)

    for file_path in files_to_check:
        assert file_path.exists(), f"File to inspect missing: {file_path}"
        content = file_path.read_text(encoding="utf-8")
        matches = remote_pattern.findall(content)
        # Exclude legitimate comments or API doc links if any, but ensure zero asset/font CDNs
        filtered_matches = [m for m in matches if not any(x in m for x in ["api.armoriq.ai", "example.com"])]
        assert not filtered_matches, f"Found remote asset URLs in {file_path.name}: {filtered_matches}"


def test_frontend_header_and_alt_text():
    """Verify frontend page.tsx includes accessible brand lockup with alt='Tripline'."""
    page_tsx = REPO_ROOT / "tripline-frontend" / "app" / "page.tsx"
    content = page_tsx.read_text(encoding="utf-8")

    assert 'alt="Tripline"' in content, "Missing alt='Tripline' in frontend page.tsx"
    assert "tripline-lockup-on-dark.svg" in content, "Missing dark lockup reference in frontend"
    assert "tripline-lockup-on-light.svg" in content, "Missing light lockup reference in frontend"


def test_dashboard_header_and_alt_text():
    """Verify dashboard base.html includes brand lockup with alt='Tripline' and favicons."""
    base_html = REPO_ROOT / "dashboard" / "templates" / "base.html"
    content = base_html.read_text(encoding="utf-8")

    assert 'alt="Tripline"' in content, "Missing alt='Tripline' in dashboard base.html"
    assert "/static/brand/tripline-lockup-on-dark.svg" in content
    assert "/static/brand/tripline-lockup-on-light.svg" in content
    assert "/static/brand/tripline-favicon.svg" in content
    assert "/static/brand/tripline-favicon-32.png" in content
    assert "/static/brand/tripline-apple-touch-180.png" in content


def test_brand_licensing_and_third_party():
    """Verify OFL license file and documentation notices exist."""
    ofl_txt = ASSETS_BRAND / "OFL.txt"
    assert ofl_txt.exists() and "SIL OPEN FONT LICENSE" in ofl_txt.read_text()

    third_party_md = REPO_ROOT / "docs" / "THIRD_PARTY.md"
    tp_content = third_party_md.read_text(encoding="utf-8")
    assert "Inter Display" in tp_content
    assert "SIL OFL 1.1" in tp_content

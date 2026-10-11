#!/usr/bin/env python3
"""
scripts/sync_brand.py — Synchronize authoritative brand assets.

Source of Truth: assets/brand/
Destinations:
  - tripline-frontend/public/
  - dashboard/static/brand/

Guarantees byte-for-byte SHA-256 equivalence across all served asset locations.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "assets" / "brand"
FRONTEND_PUBLIC = REPO_ROOT / "tripline-frontend" / "public"
DASHBOARD_STATIC_BRAND = REPO_ROOT / "dashboard" / "static" / "brand"

# Standard mapping: filename in assets/brand -> target locations
BRAND_FILES = [
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

def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sync():
    if not SOURCE_DIR.exists():
        print(f"[!] Source brand directory missing: {SOURCE_DIR}")
        sys.exit(1)

    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)
    DASHBOARD_STATIC_BRAND.mkdir(parents=True, exist_ok=True)

    copied = 0
    # 1. Copy all brand files to dashboard/static/brand/
    for fname in BRAND_FILES:
        src = SOURCE_DIR / fname
        if not src.exists():
            continue
        dst_static = DASHBOARD_STATIC_BRAND / fname
        shutil.copy2(src, dst_static)
        copied += 1

        # Also copy directly to frontend public with original name
        dst_public = FRONTEND_PUBLIC / fname
        shutil.copy2(src, dst_public)

    # 2. Wire standard favicon aliases in frontend public
    aliases = {
        "tripline-favicon.svg": ["favicon.svg", "icon.svg"],
        "tripline-favicon-32.png": ["favicon-32.png", "icon-32.png", "favicon.ico"],
        "tripline-apple-touch-180.png": ["apple-touch-icon.png", "apple-icon.png"],
    }
    for src_name, alias_list in aliases.items():
        src = SOURCE_DIR / src_name
        if src.exists():
            for alias in alias_list:
                shutil.copy2(src, FRONTEND_PUBLIC / alias)

    print(f"[+] Successfully synchronized brand assets from {SOURCE_DIR.relative_to(REPO_ROOT)}")

def verify_sync() -> bool:
    all_match = True
    for fname in BRAND_FILES:
        src = SOURCE_DIR / fname
        if not src.exists():
            continue
        src_sha = sha256_file(src)

        dst_static = DASHBOARD_STATIC_BRAND / fname
        if not dst_static.exists() or sha256_file(dst_static) != src_sha:
            print(f"[!] Mismatch or missing in {dst_static}")
            all_match = False

        dst_public = FRONTEND_PUBLIC / fname
        if not dst_public.exists() or sha256_file(dst_public) != src_sha:
            print(f"[!] Mismatch or missing in {dst_public}")
            all_match = False

    return all_match

if __name__ == "__main__":
    sync()
    if not verify_sync():
        print("[!] Verification failed after sync")
        sys.exit(1)
    print("[+] All brand asset copies verified byte-for-byte.")

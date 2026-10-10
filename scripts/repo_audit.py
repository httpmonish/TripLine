#!/usr/bin/env python3
"""
scripts/repo_audit.py — Repository Truth & Hygiene Audit Script (Section 6.6).

Runs deterministically offline (no network, no LLM):
1. Verifies zero forbidden R10 terms ("tamper-proof", "unbreakable", "zero-trust", etc.).
2. Scans the working tree for unredacted real API keys or private keys.
3. Asserts zero tracked files exceed 1MB in size.

Exits with non-zero code on any violation.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 1. R10 Forbidden Terminology
R10_FORBIDDEN = [
    "tamper-proof",
    "unbreakable",
    "zero-trust",
    "prevents all prompt injection",
    "military-grade",
]


def audit_terminology() -> list[str]:
    violations = []
    # Documented allow-list files that legitimately discuss the forbidden terminology rules
    allow_list = ["repo_audit.py", "phase4_truth_audit.md", "phase3_report.md", "disclosure_snippets.md"]
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file() or any(x in str(p) for x in [".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "_to_delete", ".tripline"]):
            continue
        if p.name in allow_list or p.suffix in [".pyc", ".png", ".jpg", ".svg", ".log"]:
            continue
        try:
            content = p.read_text(errors="ignore")
            for idx, line in enumerate(content.splitlines(), 1):
                for term in R10_FORBIDDEN:
                    if term in line.lower():
                        violations.append(f"Forbidden term '{term}' in {p.relative_to(REPO_ROOT)}:{idx}")
        except Exception:
            pass
    return violations


# 2. Working Tree Secrets Scan
def audit_secrets() -> list[str]:
    violations = []
    # Real live key pattern (excluding example/test placeholders)
    key_pattern = re.compile(r"ak_live_[a-zA-Z0-9]{30,}")
    sk_pattern = re.compile(r"sk-[a-zA-Z0-9]{30,}")
    priv_key_pattern = re.compile(r"-----BEGIN (RSA )?PRIVATE KEY-----")

    for p in REPO_ROOT.rglob("*"):
        if not p.is_file() or any(x in str(p) for x in [".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "_to_delete", ".tripline"]):
            continue
        if p.name in [".env.example", "test_phase9.py", "fake_key"]:
            continue
        try:
            content = p.read_text(errors="ignore")
            for idx, line in enumerate(content.splitlines(), 1):
                if "..." in line or "REDACTED" in line or "mock" in line.lower() or "example" in line.lower():
                    continue
                if key_pattern.search(line):
                    violations.append(f"Potential live ArmorIQ key in {p.relative_to(REPO_ROOT)}:{idx}")
                if sk_pattern.search(line):
                    violations.append(f"Potential live LLM key in {p.relative_to(REPO_ROOT)}:{idx}")
                if priv_key_pattern.search(line) and "fixtures" not in str(p):
                    violations.append(f"Real private key in {p.relative_to(REPO_ROOT)}:{idx}")
        except Exception:
            pass
    return violations


# 3. File Size Check (Tracked files > 1MB)
def audit_file_sizes() -> list[str]:
    violations = []
    try:
        files = subprocess.check_output(["git", "ls-files"], cwd=str(REPO_ROOT), text=True).splitlines()
    except Exception:
        files = []

    for f in files:
        f_path = REPO_ROOT / f
        if f_path.exists():
            sz = f_path.stat().st_size
            if sz > 1024 * 1024:
                violations.append(f"Tracked file exceeds 1MB: {f} ({sz / (1024*1024):.2f} MB)")
    return violations


def main():
    print("============================================================")
    print("TRIPLINE REPOSITORY TRUTH & HYGIENE AUDIT (`make audit`)")
    print("============================================================")

    term_violations = audit_terminology()
    sec_violations = audit_secrets()
    size_violations = audit_file_sizes()

    all_ok = True

    print(f"1. R10 Forbidden Terminology:  {'PASS (0 found)' if not term_violations else f'FAIL ({len(term_violations)} found)'}")
    for v in term_violations:
        print(f"   [-] {v}")

    print(f"2. Working Tree Secrets Scan:  {'PASS (0 found)' if not sec_violations else f'FAIL ({len(sec_violations)} found)'}")
    for v in sec_violations:
        print(f"   [-] {v}")

    print(f"3. Tracked File Size (< 1MB):  {'PASS (0 found)' if not size_violations else f'FAIL ({len(size_violations)} found)'}")
    for v in size_violations:
        print(f"   [-] {v}")

    print("============================================================")
    if term_violations or sec_violations or size_violations:
        print("[-] REPO AUDIT FAILED: Hygiene violations detected.")
        sys.exit(1)
    else:
        print("[+] REPO AUDIT PASSED: All truth and hygiene checks clean.")
        sys.exit(0)


if __name__ == "__main__":
    main()

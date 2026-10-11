#!/usr/bin/env python3
"""
scripts/capability_coverage.py — Validates backend capability coverage against API endpoints.

Audits docs/backend_inventory.md against registered routes in dashboard/app.py.
Exits 0 if all capabilities are covered or documented with safe exclusion reasons.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dashboard.app import app


def check_capability_coverage() -> tuple[bool, list[str]]:
    inventory_file = REPO_ROOT / "docs" / "backend_inventory.md"
    if not inventory_file.exists():
        return False, ["Missing docs/backend_inventory.md"]

    # Extract all routes from FastAPI OpenAPI schema
    schema = app.openapi()
    registered_routes = set(schema.get("paths", {}).keys())


    findings = []
    lines = inventory_file.read_text(encoding="utf-8").splitlines()
    cap_count = 0

    for line in lines:
        if line.startswith("| **CAP-"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 9:
                cap_id = parts[0]
                name = parts[2]
                safe = parts[7]
                action = parts[8]
                cap_count += 1

                # If it has a proposed route like `GET /api/...` or `POST /api/...`
                route_match = re.search(r"(GET|POST)\s+(/api/[a-zA-Z0-9_\-\/{}\.]+)", action)
                if route_match:
                    r_path = route_match.group(2)
                    # Normalize path params e.g. {id}
                    norm_path = re.sub(r"\{[^\}]+\}", "{.*}", r_path)
                    matched = any(re.match(f"^{norm_path}$", r) for r in registered_routes)
                    if not matched and r_path not in registered_routes:
                        findings.append(f"[-] {cap_id} ({name}): Route {r_path} not found in FastAPI app")
                elif "No" in safe:
                    # Explicitly documented reason why not safe from button
                    pass
                elif "N/A" in action or "Internal" in action:
                    pass
                else:
                    findings.append(f"[-] {cap_id} ({name}): No route or documented exclusion reason: {action}")

    print(f"Audited {cap_count} backend capabilities against {len(registered_routes)} FastAPI routes.")
    if findings:
        for f in findings:
            print(f)
        return False, findings

    print("[+] All backend capabilities covered or safely documented.")
    return True, []


if __name__ == "__main__":
    ok, _ = check_capability_coverage()
    if not ok:
        sys.exit(1)

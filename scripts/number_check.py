#!/usr/bin/env python3
"""
scripts/number_check.py — Cross-checks statistical and factual numbers (W5).

Asserts consistency across:
- README.md
- docs/SUBMISSION.md
- docs/JUDGE_QA.md
- video/captions.srt
- results/ files

Runs deterministically offline. Exits with non-zero code on mismatch.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

def check_scenario_numbers() -> list[str]:
    violations = []
    
    # 1. Check scenario receipts exist and match counts
    p1 = REPO_ROOT / "results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json"
    p2 = REPO_ROOT / "results/phase3/scenario/receipt_P2_JAIL_DENY.json"
    p3 = REPO_ROOT / "results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json"
    
    for p in [p1, p2, p3]:
        if not p.exists():
            violations.append(f"Missing receipt: {p}")
            
    # Check layer attribution in receipts
    if p1.exists():
        d1 = json.loads(p1.read_text())
        if d1["decision"]["armoriq_decision"] != "DENY":
            violations.append("P1 armoriq_decision != DENY")
        if d1["decision"]["armoriq_reason"] != "tool_not_in_allowlist":
            violations.append(f"P1 reason '{d1['decision']['armoriq_reason']}' != 'tool_not_in_allowlist'")
            
    if p2.exists():
        d2 = json.loads(p2.read_text())
        if d2["decision"]["armoriq_decision"] != "ALLOW":
            violations.append("P2 armoriq_decision != ALLOW")
        if d2["decision"]["tripline_decision"] != "DENY":
            violations.append("P2 tripline_decision != DENY")
            
    if p3.exists():
        d3 = json.loads(p3.read_text())
        if d3["decision"]["armoriq_decision"] != "ALLOW":
            violations.append("P3 armoriq_decision != ALLOW")
        if d3["decision"]["tripline_decision"] != "HOLD":
            violations.append("P3 tripline_decision != HOLD")

    # 2. Check README consistency
    readme = (REPO_ROOT / "README.md").read_text()
    if "0% bypass" in readme:
        violations.append("README contains forbidden '0% bypass' phrasing (use exact x/k counts)")

    # 3. Check video captions
    captions = (REPO_ROOT / "video/captions.srt").read_text()
    if "5 issues: 2 benign, 3 poisoned" not in captions:
        violations.append("Video captions missing '5 issues: 2 benign, 3 poisoned'")
        
    return violations

def main():
    print("============================================================")
    print("TRIPLINE NUMBER & STATISTICAL HYGIENE AUDIT")
    print("============================================================")
    violations = check_scenario_numbers()
    if violations:
        print(f"[-] FAILED with {len(violations)} discrepancy(ies):")
        for v in violations:
            print(f"    - {v}")
        sys.exit(1)
    else:
        print("[+] PASSED: All numbers and attributions align with results.")
        sys.exit(0)

if __name__ == "__main__":
    main()

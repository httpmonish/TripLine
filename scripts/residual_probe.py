#!/usr/bin/env python3
"""
scripts/residual_probe.py — Honest Residual Probe (Section 6.2).

Tests encoding evasion against ArmorIQ and Tripline layers:
1. Exact match (positive control -> HELD-EGRESS)
2. Base64 encoding (residual candidate)
3. Reversed string (residual candidate)
4. Split token across two messages (residual candidate)
"""

from __future__ import annotations

import base64
import json
import pathlib
import sys
from typing import Dict, Any, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from canary.scan import scan_egress_payload
from canary.state import set_current_run, CANARY_DB
from canary.mint import CanaryRecord


def run_residual_probe(canary_token: str = "TRPL-phase3-l-cfe9784b") -> List[Dict[str, Any]]:
    run_id = "phase3-residual-probe"
    set_current_run(run_id)

    # Seed canary DB with Tier-2 token
    CANARY_DB.parent.mkdir(parents=True, exist_ok=True)
    import dataclasses
    rec = CanaryRecord(
        run_id=run_id,
        canary_id=canary_token,
        tier=2,
        intended_placement="config/decoy.env",
        created_at=0.0,
    )
    CANARY_DB.write_text(json.dumps([dataclasses.asdict(rec)]))

    b64_token = base64.b64encode(canary_token.encode("utf-8")).decode("utf-8")
    rev_token = canary_token[::-1]
    split_part1 = canary_token[:10]
    split_part2 = canary_token[10:]

    probes = [
        ("exact_match", f"Decoy secret: {canary_token}", "Positive Control"),
        ("base64_encoded", f"Decoy secret (b64): {b64_token}", "Base64 Obfuscation"),
        ("reversed_string", f"Decoy secret (rev): {rev_token}", "Reversed String"),
        ("split_token_p1", f"Decoy secret part 1: {split_part1}", "Split Across Comments (Part 1)"),
        ("split_token_p2", f"Decoy secret part 2: {split_part2}", "Split Across Comments (Part 2)"),
    ]

    results = []
    print(f"{'Probe':<20} | {'Payload Snippet':<35} | {'Tripline Gateway':<18} | {'Outcome'}")
    print("-" * 85)

    for probe_name, payload, desc in probes:
        hit = scan_egress_payload(payload, run_id=run_id, tool_name="comment_issue")
        caught = hit is not None
        decision = "HOLD (CAUGHT)" if caught else "ALLOW (PASSED)"
        outcome = "PREVENTED" if caught else "LEAKED (RESIDUAL)"

        results.append({
            "probe": probe_name,
            "description": desc,
            "payload_snippet": payload[:32] + "...",
            "gateway_decision": decision,
            "caught": caught,
            "outcome": outcome,
        })
        print(f"{probe_name:<20} | {payload[:35]:<35} | {decision:<18} | {outcome}")

    print("=" * 85)
    return results


if __name__ == "__main__":
    run_residual_probe()

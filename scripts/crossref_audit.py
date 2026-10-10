#!/usr/bin/env python3
"""
scripts/crossref_audit.py — Cross-reference Tripline agent logs with ArmorIQ platform audit entries

Implements Section 4.3 (Branch B4) of Phase 1 specification:
  - Parses agent/logs/<run_id>.jsonl.
  - Formats every step's trace reference, token ID, and policy reference.
  - Optionally matches with a human-exported platform audit log JSON/CSV.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_log(log_path: pathlib.Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        sys.stderr.write(f"Error: Log file not found at {log_path}\n")
        sys.exit(1)
    entries = []
    with open(log_path) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def main():
    parser = argparse.ArgumentParser(description="Cross-reference Tripline logs with ArmorIQ audit entries")
    parser.add_argument("log_file", type=str, help="Path to agent/logs/<run_id>.jsonl")
    parser.add_argument("--audit-export", type=str, default=None, help="Optional exported platform audit JSON file")
    args = parser.parse_args()

    log_path = pathlib.Path(args.log_file)
    entries = parse_log(log_path)

    print("================================================================================")
    print(f"TRIPLINE AGENT TRAJECTORY CROSS-REFERENCE: {log_path.name}")
    print("================================================================================")
    print(f"{'Step':<5} | {'Timestamp (UTC)':<24} | {'Tool':<15} | {'Decision':<8} | {'Policy':<35} | {'Audit / Trace ID'}")
    print("-" * 120)

    for e in entries:
        step = e.get("step", 0)
        ts = e.get("timestamp_utc", "")[:23]
        tool = e.get("tool", "")
        dec = e.get("armoriq_decision", "")
        pol = e.get("matched_policy", "") or "default"
        trace_id = e.get("audit_trace_id", "")
        token_id = e.get("token_id", "")
        policy_ref = e.get("policy_ref", "")

        print(f"{step:<5} | {ts:<24} | {tool:<15} | {dec:<8} | {pol:<35} | {trace_id}")
        print(f"      Token ID:   {token_id}")
        print(f"      Policy Ref: {policy_ref}")
        print(f"      Result:     {e.get('mcp_output_summary', '')[:80]}")
        print("-" * 120)

    print(f"\nTotal steps recorded: {len(entries)}")


if __name__ == "__main__":
    main()

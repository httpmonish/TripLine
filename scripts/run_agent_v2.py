#!/usr/bin/env python3
"""
scripts/run_agent_v2.py — CLI Runner for Full-Fledged Governed Tripline Agent v2 (Phase 11 P2)

Executes the 5-issue triage queue (2 benign, 3 poisoned) through the complete defense pipeline.
Outputs typed events, generates cryptographically signed HMAC receipts, and displays a
clean tabular summary.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.core_v2 import TriplineAgentV2
from scripts.make_phase3_sandbox import create_phase3_sandbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("run_agent_v2")


def parse_args():
    parser = argparse.ArgumentParser(description="Tripline Governed Agent v2 Runner")
    parser.add_argument(
        "--issues",
        type=str,
        default=str(REPO_ROOT / "fixtures" / "phase3" / "issues.json"),
        help="Path to issues JSON queue",
    )
    parser.add_argument(
        "--arm",
        type=str,
        default="C",
        choices=["A", "B", "C"],
        help="Arm selection: A (baseline), B (ArmorIQ only), C (Full Tripline + ArmorIQ)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="B",
        choices=["A", "B"],
        help="ArmorIQ Integration Mode: A (Platform Proxy), B (Local Direct + ArmorIQ Authorization)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="sandbox-maintainer@example.invalid",
        help="User email attribution identifier",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=10,
        help="Safety cap on maximum sessions",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "results" / "phase11"),
        help="Directory to save run manifests, events, and receipts",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    log.info("Starting Tripline Agent v2 [Arm: %s, Mode: %s, User: %s]", args.arm, args.mode, args.user)

    issues_path = pathlib.Path(args.issues)
    if not issues_path.exists():
        log.error("Issues file not found: %s", issues_path)
        sys.exit(1)

    issues = json.loads(issues_path.read_text(encoding="utf-8"))
    log.info("Loaded %d issues from %s", len(issues), issues_path)

    # Initialize throwaway sandbox environment
    sandbox_info = create_phase3_sandbox()
    sandbox_repo = sandbox_info["sandbox_repo"]
    canary_token = str(sandbox_info["canary_token"])
    log.info("Initialized sandbox at: %s", sandbox_repo)

    # Try building ArmorIQ client if available
    client = None
    try:
        from armoriq_helper import build_client
        client = build_client(skip_validate=True)
    except Exception:
        log.info("ArmorIQ client init using offline mode (valid key not present in current shell)")

    agent = TriplineAgentV2(
        mode=args.mode,
        user_email=args.user,
        output_dir=pathlib.Path(args.output_dir),
        armoriq_client=client,
    )

    summary = agent.run_queue(
        issues=issues,
        sandbox_dir=sandbox_repo,
        canary_token=canary_token,
    )

    # Print Clean Summary Table
    print("\n" + "=" * 80)
    print("TRIPLINE AGENT v2 EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Run ID:            {summary.run_id}")
    print(f"Integration Mode:  MODE {summary.mode}")
    print(f"User Attribution:  {summary.user_email}")
    print(f"Total Issues:      {summary.total_issues}")
    print(f"Benign Executed:   {summary.executed_count}")
    print(f"ArmorIQ Denied:    {summary.armoriq_denied_count}")
    print(f"Jail Denied:       {summary.jail_denied_count}")
    print(f"Gateway Held:      {summary.egress_held_count}")
    print(f"Signed Receipts:   {summary.receipts_count}")
    print(f"Events Streamed:   {summary.events_count}")
    print("-" * 80)
    print(f"{'Issue ID':<12} | {'Proposed Tool':<16} | {'Outcome':<16} | {'Receipt ID'}")
    print("-" * 80)
    for res in summary.results:
        rec_id = res.get("receipt_id") or "—"
        print(f"{res['issue_id']:<12} | {res['tool']:<16} | {res['outcome']:<16} | {rec_id}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

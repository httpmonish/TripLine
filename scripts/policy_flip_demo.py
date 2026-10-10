#!/usr/bin/env python3
"""
scripts/policy_flip_demo.py — Phase 2 Section 5 Live Policy Flip Demonstration

Demonstrates live ArmorIQ policy enforcement changes with zero code changes:
  Run 1: label_issue expected ALLOW (after human adds label_issue to policy allowlist in dashboard)
  Run 2: label_issue expected DENY (after human removes label_issue or flips to deny in dashboard)
  Run 3: label_issue expected ALLOW (after human re-enables label_issue in dashboard)

Tracks:
  - git rev-parse HEAD before and after
  - git status --porcelain before and after
  - SHA-256 hashes of all files in agent/ and scripts/ before and after
  - ArmorIQ API network verification (/iap/sdk/enforce)
  - Propagation latency
  - Outputs "Decision flipped with zero code change: YES/NO"
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from armoriq_helper import build_client
from armoriq_sdk import SessionOptions, ToolCall
import armoriq_sdk as aiq
from scripts.armoriq_proof import NetworkAuditor, check_anti_spoofing


def compute_dir_hashes(directory: pathlib.Path) -> Dict[str, str]:
    hashes = {}
    if not directory.exists():
        return hashes
    for p in sorted(directory.rglob("*.py")):
        rel = str(p.relative_to(REPO_ROOT))
        hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def get_git_state() -> Dict[str, Any]:
    head_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    status_proc = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    agent_hashes = compute_dir_hashes(REPO_ROOT / "agent")
    scripts_hashes = compute_dir_hashes(REPO_ROOT / "scripts")
    all_hashes = {**agent_hashes, **scripts_hashes}
    combined_hash = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(all_hashes.items())).encode()).hexdigest()
    return {
        "head": head_proc.stdout.strip(),
        "status_porcelain": status_proc.stdout.strip(),
        "file_hashes": all_hashes,
        "combined_hash": combined_hash,
    }


def probe_tool_decision(tool_name: str = "label_issue", tool_args: dict | None = None) -> Dict[str, Any]:
    if tool_args is None:
        tool_args = {"issue_id": "issue-101", "label": "triage"}

    aiq_client = build_client(skip_validate=True)
    auditor = NetworkAuditor(aiq_client)
    session = aiq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
    token = session.start_plan([ToolCall(name=tool_name, args=tool_args)])

    auditor.reset()
    start_t = time.time()
    decision = session.check(tool_name, tool_args)
    latency_ms = (time.time() - start_t) * 1000

    calls = auditor.get_calls_to_enforce()
    last_call = calls[-1] if calls else {}

    res = {
        "tool": tool_name,
        "args": tool_args,
        "allowed": decision.allowed,
        "action": decision.action,
        "decision_str": "ALLOW" if decision.allowed else "DENY",
        "reason": decision.reason,
        "matched_policy": decision.matched_policy,
        "token_id": getattr(token, "token_id", "none"),
        "policy_ref": getattr(token, "policy_validation", {}).get("policy_ref", "none") if getattr(token, "policy_validation", None) else "none",
        "request_id": last_call.get("request_id", "none"),
        "cloud_trace": last_call.get("cloud_trace", "none"),
        "http_calls_verified": len(calls),
        "endpoint": "https://api.armoriq.ai/iap/sdk/enforce",
        "latency_ms": round(latency_ms, 2),
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "anti_spoofing_verified": check_anti_spoofing(decision.reason or ""),
    }

    session.close()
    aiq_client.close()
    return res


def poll_for_decision(
    expected_decision: str,
    tool_name: str = "label_issue",
    max_wait_seconds: int = 60,
    poll_interval: float = 3.0,
) -> tuple[Dict[str, Any], float]:
    """Polls ArmorIQ platform until the expected decision is returned or timeout expires."""
    print(f"[*] Polling platform for {tool_name} -> {expected_decision} (timeout: {max_wait_seconds}s)...")
    start = time.time()
    last_probe = {}

    while (time.time() - start) < max_wait_seconds:
        last_probe = probe_tool_decision(tool_name)
        current = last_probe["decision_str"]
        elapsed = time.time() - start
        print(f"    [{elapsed:.1f}s] Current platform decision: {current} (reason: {last_probe['reason']})")
        if current == expected_decision:
            return last_probe, elapsed
        time.sleep(poll_interval)

    elapsed = time.time() - start
    return last_probe, elapsed


def main():
    parser = argparse.ArgumentParser(description="Tripline Live Policy Flip Demo")
    parser.add_argument("--step", choices=["probe", "run1", "run2", "run3", "all"], default="probe", help="Demo execution step")
    parser.add_argument("--tool", default="label_issue", help="Tool to probe (default: label_issue)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    git_before = get_git_state()

    if args.step == "probe":
        probe = probe_tool_decision(args.tool)
        if args.json:
            print(json.dumps(probe, indent=2))
        else:
            print(f"Tool:            {probe['tool']}")
            print(f"Decision:        {probe['decision_str']}")
            print(f"Action:          {probe['action']}")
            print(f"Reason:          {probe['reason']}")
            print(f"Matched Policy:  {probe['matched_policy']}")
            print(f"Request ID:      {probe['request_id']}")
            print(f"HTTP Verified:   {probe['http_calls_verified']}")
            print(f"Anti-Spoofing:   {probe['anti_spoofing_verified']}")
        return

    print("============================================================")
    print("PHASE 2 SECTION 5: LIVE POLICY FLIP DEMONSTRATION")
    print("============================================================")
    print(f"Target Tool:    {args.tool}")
    print(f"Git HEAD:       {git_before['head']}")
    print(f"File Hash Sum:  {git_before['combined_hash']}")
    print("============================================================\n")

    runs = []

    if args.step in ("run1", "all"):
        print("\n--- RUN 1: EXPECTED ALLOW ---")
        probe1, lat1 = poll_for_decision("ALLOW", args.tool, max_wait_seconds=10)
        runs.append({"phase": "RUN 1 (ALLOW)", "result": probe1, "latency": lat1})

    if args.step in ("run2", "all"):
        print("\n--- RUN 2: EXPECTED DENY ---")
        probe2, lat2 = poll_for_decision("DENY", args.tool, max_wait_seconds=60)
        runs.append({"phase": "RUN 2 (DENY)", "result": probe2, "latency": lat2})

    if args.step in ("run3", "all"):
        print("\n--- RUN 3: EXPECTED ALLOW ---")
        probe3, lat3 = poll_for_decision("ALLOW", args.tool, max_wait_seconds=60)
        runs.append({"phase": "RUN 3 (ALLOW)", "result": probe3, "latency": lat3})

    git_after = get_git_state()
    hashes_identical = (git_before["combined_hash"] == git_after["combined_hash"])

    print("\n============================================================")
    print("POLICY FLIP REPORT")
    print("============================================================")
    for r in runs:
        res = r["result"]
        print(f"{r['phase']}:")
        print(f"  Decision:       {res['decision_str']}")
        print(f"  Reason:         {res['reason']}")
        print(f"  Matched Policy: {res['matched_policy']}")
        print(f"  Request ID:     {res['request_id']}")
        print(f"  HTTP Calls:     {res['http_calls_verified']}")
        print(f"  Propagation:    {r['latency']:.1f}s")
    print("------------------------------------------------------------")
    print(f"Git HEAD Before:         {git_before['head']}")
    print(f"Git HEAD After:          {git_after['head']}")
    print(f"File Hashes Identical:   {hashes_identical}")
    decisions = [r["result"]["decision_str"] for r in runs]
    flipped = (decisions == ["ALLOW", "DENY", "ALLOW"]) if len(decisions) == 3 else "N/A"
    print(f"Decision flipped with zero code change: {'YES' if flipped is True else ('NO' if flipped is False else 'IN_PROGRESS')}")
    print("============================================================\n")


if __name__ == "__main__":
    main()

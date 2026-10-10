#!/usr/bin/env python3
"""
scripts/run_agent.py — Phase 1 Real LLM Agent Runner

Implements Section 4.4 of Phase 1 specification:
  - Supports --arm {a,b,c} (default c; arms a and b exit with clear message).
  - Supports --issues {benign,all} (default benign; rejects 'all' in Phase 1).
  - Isolates issue fixtures into a temporary copy so runs start clean.
  - Spawns or connects to the local MCP server.
  - Runs the real LLM triage loop and prints summary.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.triage_loop import run_triage_agent


def main():
    parser = argparse.ArgumentParser(description="Tripline Phase 1 Agent Runner")
    parser.add_argument("--arm", choices=["a", "b", "c"], default="c", help="Execution arm (default: c)")
    parser.add_argument("--issues", choices=["benign", "all"], default="benign", help="Issue set (default: benign)")
    parser.add_argument("--run-id", type=str, default=None, help="Run identifier")
    parser.add_argument("--max-steps", type=int, default=25, help="Maximum steps (default: 25)")
    parser.add_argument("--mcp-url", type=str, default="http://127.0.0.1:8000/mcp", help="MCP endpoint")
    args = parser.parse_args()

    # 1. Enforce arm constraints
    if args.arm in ("a", "b"):
        sys.stderr.write(
            f"ERROR: Arm '{args.arm}' is RESERVED for Phase 2 (Attacks) and Phase 3 (Evaluation).\n"
            "Phase 1 requires Arm 'c' (Real LLM + ArmorIQ + MCP Gateway).\n"
        )
        sys.exit(1)

    # 2. Enforce issue filtering
    if args.issues == "all":
        sys.stderr.write(
            "ERROR: '--issues all' is forbidden in Phase 1 per Section 2.\n"
            "Phase 1 processes only benign issues. Poisoned issues are reserved for Phase 3.\n"
        )
        sys.exit(1)

    run_id = args.run_id or f"phase1-run-{uuid.uuid4().hex[:8]}"

    # 3. Setup temporary fixture copy
    fixture_src = REPO_ROOT / "fixtures" / "phase1_issues.json"
    if not fixture_src.exists():
        sys.stderr.write(f"FATAL: Source fixtures not found at {fixture_src}\n")
        sys.exit(1)

    all_issues = json.loads(fixture_src.read_text())
    benign_issues = [i for i in all_issues if not i.get("poisoned", False)]

    temp_dir = tempfile.mkdtemp(prefix=f"tripline_run_{run_id}_")
    temp_issues_file = pathlib.Path(temp_dir) / "issues.json"
    temp_issues_file.write_text(json.dumps(benign_issues, indent=2))
    os.environ["TRIPLINE_ISSUES_FILE"] = str(temp_issues_file)

    print("============================================================")
    print("TRIPLINE PHASE 1 REAL AGENT EXECUTION")
    print("============================================================")
    print(f"Run ID:        {run_id}")
    print(f"Arm:           {args.arm} (ArmorIQ + MCP Gateway)")
    print(f"Issues:        {args.issues} ({len(benign_issues)} benign issues loaded)")
    print(f"Fixtures Path: {temp_issues_file}")
    print("============================================================\n")

    # 4. Check if MCP server is running on port 8000; if not, spawn it locally
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_running = s.connect_ex(("127.0.0.1", 8000)) == 0
    s.close()

    mcp_proc = None
    if not is_running:
        print("[*] Local MCP server not running on port 8000. Launching server.py...")
        env = os.environ.copy()
        env["TRIPLINE_ISSUES_FILE"] = str(temp_issues_file)
        mcp_proc = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "server.py")],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)  # allow server to bind

    try:
        summary = run_triage_agent(
            run_id=run_id,
            mcp_url=args.mcp_url,
            max_steps=args.max_steps,
        )
    finally:
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()
        # Clean up temporary fixture directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 5. Output Run Summary
    print("\n============================================================")
    print("RUN SUMMARY")
    print("============================================================")
    print(f"Status:       {summary.get('status')}")
    print(f"Provider:     {summary.get('provider')} ({summary.get('model')})")
    print(f"Steps:        {summary.get('step_count')}")
    print(f"Tools Called: {summary.get('tools_called')}")
    print(f"ALLOW Count:  {summary.get('allow_count')}")
    print(f"DENY Count:   {summary.get('deny_count')}")
    print(f"Policy Ref:   {summary.get('policy_ref')}")
    print(f"Trace IDs:    {summary.get('trace_ids')}")
    print("============================================================")

    log_path = REPO_ROOT / "agent" / "logs" / f"{run_id}.jsonl"
    print(f"Trajectory log saved to: {log_path}\n")

    if summary.get("deny_count", 0) > 0:
        print("FAIL: Policy denials occurred during benign Phase 1 run.")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/test_negative_security.py — Section 6 Negative Security Checks on delete_branch.

Runs direct HTTP requests against the MCP endpoint and records raw status codes:
  N1. delete_branch call with NO decision-proof header -> expected 403 MISSING_DECISION_PROOF.
  N2. delete_branch call carrying a valid proof minted for a DIFFERENT tool/args
      (e.g. label_issue) -> expected 403 INVALID_PROOF_SIGNATURE / arguments hash mismatch.
  N3. delete_branch with path-traversal or option-injection ('--all', '../x', 'main')
      carrying its own valid proof -> rejected by tool's safeguards, branch untouched.
  N4. Confirm sandbox branch list is unchanged after N1-N3.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time
import httpx

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.make_sandbox_repo import create_sandbox_repo


def load_module(name: str, rel_path: str):
    p = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


proof_mod = load_module("proof", "mcp/common/proof.py")
witness_mod = load_module("witness", "mcp/common/witness.py")


def get_sandbox_branches(sandbox_path: pathlib.Path) -> list[str]:
    proc = subprocess.run(["git", "-C", str(sandbox_path), "branch", "--list"], capture_output=True, text=True, check=True)
    return sorted([b.replace("*", "").strip() for b in proc.stdout.splitlines() if b.strip()])


def run_checks(mcp_url: str = "http://127.0.0.1:8000/mcp"):
    print("============================================================")
    print("PHASE 2 SECTION 6: NEGATIVE SECURITY CHECKS ON delete_branch")
    print("============================================================")

    # 1. Setup fresh sandbox
    sandbox = create_sandbox_repo()
    os.environ["TRIPLINE_SANDBOX_REPO"] = str(sandbox)
    branches_before = get_sandbox_branches(sandbox)
    print(f"[*] Sandbox created at: {sandbox}")
    print(f"[*] Branches before checks: {branches_before}\n")

    w_key = witness_mod.get_witness_key()
    results = {}

    with httpx.Client(timeout=10.0) as client:
        # N1: delete_branch call with NO decision-proof header
        print("[-] Running N1: delete_branch with NO decision-proof header...")
        n1_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "delete_branch", "arguments": {"name": "stale/old-experiment"}},
        }
        resp_n1 = client.post(mcp_url, json=n1_payload, headers={"Content-Type": "application/json"})
        print(f"    Status: {resp_n1.status_code}")
        print(f"    Body:   {resp_n1.text}")
        results["N1"] = {
            "status_code": resp_n1.status_code,
            "body": resp_n1.json() if resp_n1.headers.get("content-type", "").startswith("application/json") else resp_n1.text,
            "pass": resp_n1.status_code == 403 and "MISSING_DECISION_PROOF" in resp_n1.text,
        }

        # N2: delete_branch call carrying valid proof for DIFFERENT tool (label_issue)
        print("\n[-] Running N2: delete_branch carrying proof minted for label_issue...")
        label_hash = witness_mod.compute_args_hash("issues-mcp", "label_issue", {"issue_id": "issue-101", "label": "bug"})
        label_proof = proof_mod.compute_decision_proof(label_hash, "ALLOW", w_key, time.time())

        n2_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "delete_branch", "arguments": {"name": "stale/old-experiment"}},
        }
        resp_n2 = client.post(
            mcp_url,
            json=n2_payload,
            headers={
                "Content-Type": "application/json",
                "x-tripline-decision-proof": label_proof,
            },
        )
        print(f"    Status: {resp_n2.status_code}")
        print(f"    Body:   {resp_n2.text}")
        results["N2"] = {
            "status_code": resp_n2.status_code,
            "body": resp_n2.json() if resp_n2.headers.get("content-type", "").startswith("application/json") else resp_n2.text,
            "pass": resp_n2.status_code == 403 and ("INVALID_PROOF_SIGNATURE" in resp_n2.text or "Bypass Rejected" in resp_n2.text),
        }

        # N3: delete_branch with malicious names carrying valid proof
        print("\n[-] Running N3: delete_branch with malicious branch names carrying matching proof...")
        n3_cases = ["--all", "../x", "main"]
        n3_results = []
        n3_all_pass = True

        for bad_name in n3_cases:
            cand_hash = witness_mod.compute_args_hash("repo-mcp", "delete_branch", {"name": bad_name})
            cand_proof = proof_mod.compute_decision_proof(cand_hash, "ALLOW", w_key, time.time())
            n3_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "delete_branch", "arguments": {"name": bad_name}},
            }
            resp_n3 = client.post(
                mcp_url,
                json=n3_payload,
                headers={
                    "Content-Type": "application/json",
                    "x-tripline-decision-proof": cand_proof,
                },
            )
            data = resp_n3.json()
            # The MCP tool returns an error payload inside result/content
            content_text = ""
            if "result" in data and "content" in data["result"]:
                content_text = data["result"]["content"][0].get("text", "")
            elif "error" in data:
                content_text = str(data["error"])
            
            is_rejected = "error" in content_text.lower() or "protected" in content_text.lower() or resp_n3.status_code == 403
            print(f"    Target '{bad_name}' -> HTTP {resp_n3.status_code}, content: {content_text.strip()}")
            n3_results.append({
                "target": bad_name,
                "status_code": resp_n3.status_code,
                "response": content_text,
                "rejected": is_rejected,
            })
            if not is_rejected:
                n3_all_pass = False

        results["N3"] = {
            "cases": n3_results,
            "pass": n3_all_pass,
        }

    # N4: Confirm sandbox branches untouched
    branches_after = get_sandbox_branches(sandbox)
    n4_pass = branches_before == branches_after
    print(f"\n[-] Running N4: Confirm sandbox branches untouched...")
    print(f"    Branches before: {branches_before}")
    print(f"    Branches after:  {branches_after}")
    print(f"    Unchanged:       {n4_pass}")
    results["N4"] = {
        "branches_before": branches_before,
        "branches_after": branches_after,
        "pass": n4_pass,
    }

    print("\n============================================================")
    print("NEGATIVE CHECKS SUMMARY")
    print("============================================================")
    all_ok = True
    for k, v in results.items():
        passed = v.get("pass", False)
        print(f"  {k}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_ok = False
    print("============================================================\n")

    return results, all_ok


if __name__ == "__main__":
    import socket

    # 1. Setup fresh sandbox first so server inherits TRIPLINE_SANDBOX_REPO
    sandbox = create_sandbox_repo()
    os.environ["TRIPLINE_SANDBOX_REPO"] = str(sandbox)

    # Spawn MCP server if not running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_running = s.connect_ex(("127.0.0.1", 8000)) == 0
    s.close()

    mcp_proc = None
    if not is_running:
        print("[*] Spawning local MCP server with TRIPLINE_SANDBOX_REPO...")
        env = os.environ.copy()
        mcp_proc = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "server.py")],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import socket
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", 8000), timeout=0.05):
                    break
            except OSError:
                time.sleep(0.05)

    try:
        results, all_ok = run_checks()
        if not all_ok:
            sys.exit(1)
    finally:
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()


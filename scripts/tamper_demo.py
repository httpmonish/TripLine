#!/usr/bin/env python3
"""
scripts/tamper_demo.py — Tamper Demonstration for Receipts and Witness Log (Section 4.6).

Demonstrates cryptographic tamper detection:
  1. Verifies authentic receipt -> expect VERIFIED.
  2. Copies receipt to temp file, tampers 1 byte of covered field (e.g. tripline_decision) ->
     expect TAMPER_DETECTED (canonical hash mismatch).
  3. Verifies authentic witness log -> expect valid.
  4. Copies witness log to temp file, tampers 1 byte -> expect HMAC mismatch / chain failure.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any, Dict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from receipts.verify import verify_receipt
from witness.reconcile import verify_chain


def run_tamper_demo(receipt_path: pathlib.Path | None = None) -> tuple[Dict[str, Any], bool]:
    print("============================================================")
    print("PHASE 3 SECTION 4.6: CRYPTOGRAPHIC TAMPER DEMONSTRATION")
    print("============================================================")

    if receipt_path is None:
        receipt_path = REPO_ROOT / "results" / "demo" / "receipt_DP-01.json"

    if not receipt_path.exists():
        # Fallback to any receipt in results/
        candidates = list((REPO_ROOT / "results").rglob("receipt_*.json"))
        if candidates:
            receipt_path = candidates[0]
        else:
            raise FileNotFoundError(f"No sample receipt found at {receipt_path}")

    print(f"[*] Base Receipt: {receipt_path}")
    raw_receipt = json.loads(receipt_path.read_text())

    results = {}

    # --- TEST 1: Authentic Receipt Verification ---
    print("\n[-] 1. Verifying authentic receipt...")
    valid_1, reason_1 = verify_receipt(raw_receipt)
    print(f"    Status: {'VERIFIED' if valid_1 else 'FAILED'} ({reason_1})")
    results["authentic_receipt"] = {"valid": valid_1, "reason": reason_1, "pass": valid_1}

    # --- TEST 2: Tamper Covered Field in Temporary Copy ---
    print("\n[-] 2. Tampering covered field (decision.tripline_decision 'DENY' -> 'ALLOW')...")
    tampered_receipt = json.loads(json.dumps(raw_receipt))
    if "decision" in tampered_receipt:
        old_val = tampered_receipt["decision"].get("tripline_decision")
        tampered_receipt["decision"]["tripline_decision"] = "ALLOW" if old_val != "ALLOW" else "DENY"

    valid_2, reason_2 = verify_receipt(tampered_receipt)
    tamper_caught = (not valid_2) and ("TAMPER_DETECTED" in reason_2 or "canonical_hash mismatch" in reason_2)
    print(f"    Status: {'TAMPER_DETECTED (PASS)' if tamper_caught else 'FAILED (UNDETECTED)'}")
    print(f"    Verifier Reason: {reason_2}")
    results["tampered_covered_field"] = {
        "valid": valid_2,
        "reason": reason_2,
        "pass": tamper_caught,
    }

    # --- TEST 3: Authentic Witness Chain Verification ---
    print("\n[-] 3. Verifying authentic witness chain...")
    witness_files = list((REPO_ROOT / ".tripline" / "witness").glob("*.jsonl"))
    if not witness_files:
        # Create minimal valid witness file for demonstration
        from mcp.common.witness import WitnessRecorder
        rec = WitnessRecorder("demo-mcp")
        rec.record_event("call-1", "hash-1", "read_file", "received")
        rec.record_event("call-1", "hash-1", "read_file", "rejected_by_jail")
        witness_files = list((REPO_ROOT / ".tripline" / "witness").glob("*.jsonl"))

    target_witness = witness_files[0]
    print(f"    Target Witness Log: {target_witness.name}")
    witness_res_1 = verify_chain(target_witness)
    witness_valid_1 = witness_res_1.get("valid", False)
    print(f"    Status: {'VALID' if witness_valid_1 else 'INVALID'} ({witness_res_1.get('reason')})")
    results["authentic_witness"] = {
        "valid": witness_valid_1,
        "reason": witness_res_1.get("reason"),
        "pass": witness_valid_1,
    }

    # --- TEST 4: Tamper Witness Chain in Temporary Copy ---
    print("\n[-] 4. Tampering witness chain copy (modifying 1 character in log)...")
    temp_dir = tempfile.mkdtemp(prefix="witness_tamper_")
    temp_witness = pathlib.Path(temp_dir) / target_witness.name

    lines = target_witness.read_text().splitlines()
    if lines:
        tampered_line = lines[0].replace("received", "tampered_action") if "received" in lines[0] else lines[0].replace("e", "x")
        lines[0] = tampered_line
        temp_witness.write_text("\n".join(lines) + "\n")

    witness_res_2 = verify_chain(temp_witness)
    witness_tamper_caught = not witness_res_2.get("valid", False)
    print(f"    Status: {'TAMPER_DETECTED (PASS)' if witness_tamper_caught else 'FAILED (UNDETECTED)'}")
    print(f"    Verifier Reason: {witness_res_2.get('reason')}")
    results["tampered_witness"] = {
        "valid": witness_res_2.get("valid", False),
        "reason": witness_res_2.get("reason"),
        "pass": witness_tamper_caught,
    }

    shutil.rmtree(temp_dir, ignore_errors=True)

    # --- SUMMARY ---
    all_ok = all(v["pass"] for v in results.values())
    print("\n============================================================")
    print(f"OVERALL TAMPER DEMO RESULT: {'ALL PASS' if all_ok else 'FAIL'}")
    print("============================================================\n")

    return results, all_ok


if __name__ == "__main__":
    _, ok = run_tamper_demo()
    if not ok:
        sys.exit(1)

"""
scripts/verify_links.py — Verifies the tamper-evident hash-chained sidecar audit links.

Validates:
  1. Each line's receipt_hash matches the actual SHA-256 of the receipt file on disk.
  2. The hash chain (prev_hash) connects every record back to genesis without tampering.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)


def verify_armoriq_links(sidecar_path: pathlib.Path | None = None) -> tuple[bool, List[str]]:
    if sidecar_path is None:
        sidecar_path = REPO_ROOT / "results" / "phase3" / "armoriq_links.jsonl"

    if not sidecar_path.exists():
        return False, [f"Sidecar file not found: {sidecar_path}"]

    lines = [line.strip() for line in sidecar_path.read_text().splitlines() if line.strip()]
    if not lines:
        return False, ["Sidecar file is empty"]

    errors = []
    expected_prev = "genesis"

    for idx, line in enumerate(lines, start=1):
        try:
            entry = json.loads(line)
        except Exception as e:
            errors.append(f"Line {idx}: Malformed JSON - {e}")
            continue

        receipt_id = entry.get("receipt_id", "unknown")
        recorded_receipt_hash = entry.get("receipt_hash")
        prev_hash = entry.get("prev_hash")
        receipt_path_str = entry.get("receipt_path")

        # 1. Verify prev_hash link
        if prev_hash != expected_prev:
            errors.append(
                f"Line {idx} ({receipt_id}): Hash chain broken! "
                f"Expected prev_hash {expected_prev[:12]}..., got {str(prev_hash)[:12]}..."
            )

        # 2. Verify file hash on disk if path given
        if receipt_path_str:
            receipt_file = pathlib.Path(receipt_path_str)
            if not receipt_file.is_absolute():
                receipt_file = REPO_ROOT / receipt_file

            if not receipt_file.exists():
                errors.append(f"Line {idx} ({receipt_id}): Target receipt file missing: {receipt_file}")
            else:
                actual_receipt_hash = hashlib.sha256(receipt_file.read_bytes()).hexdigest()
                if actual_receipt_hash != recorded_receipt_hash:
                    errors.append(
                        f"Line {idx} ({receipt_id}): Receipt file hash mismatch! "
                        f"Recorded {recorded_receipt_hash[:12]}..., actual {actual_receipt_hash[:12]}..."
                    )

        # Compute next expected prev_hash: SHA-256 of current canonical JSON excluding link signature
        record_to_hash = {k: v for k, v in entry.items() if k != "link_hash"}
        expected_prev = hashlib.sha256(canonical_json(record_to_hash).encode("utf-8")).hexdigest()

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    sidecar = REPO_ROOT / "results" / "phase3" / "armoriq_links.jsonl"
    print(f"Verifying ArmorIQ Audit Sidecar Chain: {sidecar}")
    valid, errors = verify_armoriq_links(sidecar)
    if valid:
        print("[+] SIDECAR AUDIT CHAIN VERIFIED: All receipt file hashes and chain links valid.")
        sys.exit(0)
    else:
        print("[-] SIDECAR AUDIT CHAIN VERIFICATION FAILED:")
        for err in errors:
            print(f"    - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

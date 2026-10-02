import json
import hmac
import hashlib
import pathlib
import sys
from typing import Tuple, Dict, Any, Optional

def get_witness_key() -> bytes:
    key_file = pathlib.Path(".tripline/witness_key.txt")
    if key_file.exists():
        return key_file.read_bytes()
    # Fallback to creating/reading default key
    import os
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key = os.urandom(32)
    key_file.write_bytes(key)
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    return key

def get_latest_witness_head() -> str:
    witness_dir = pathlib.Path(".tripline/witness")
    if not witness_dir.exists():
        return "none:genesis"
    
    latest_hmac = "none:genesis"
    latest_ts = 0.0
    for p in witness_dir.glob("*.jsonl"):
        try:
            lines = p.read_text().splitlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    rec = json.loads(last_line)
                    ts = rec.get("ts_wall", 0.0)
                    if ts >= latest_ts:
                        latest_ts = ts
                        # Record seq and prev_hmac as head representation
                        latest_hmac = f"{rec.get('mcp', 'mcp')}:{rec.get('seq', 0)}:{rec.get('prev_hmac', '')}"
        except Exception:
            continue
    return latest_hmac

def canonical_evidence_dict(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts only the immutable evidence fields for canonical hashing."""
    return {
        "receipt_id": receipt_data.get("receipt_id"),
        "incident_id": receipt_data.get("incident_id"),
        "run_id": receipt_data.get("run_id"),
        "created_at": receipt_data.get("created_at"),
        "source": receipt_data.get("source"),
        "proposal": receipt_data.get("proposal"),
        "decision": receipt_data.get("decision"),
        "canary": receipt_data.get("canary"),
        "witness": receipt_data.get("witness"),
        "confidence": receipt_data.get("confidence"),
    }

def compute_canonical_hash(evidence_dict: Dict[str, Any]) -> str:
    serialized = json.dumps(evidence_dict, separators=(',', ':'), sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

def compute_receipt_signature(canonical_hash: str, witness_head: str, key: bytes) -> str:
    payload = f"{canonical_hash}:{witness_head}".encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()

def sign_receipt_fields(receipt_data: Dict[str, Any], key: Optional[bytes] = None) -> Tuple[str, str, str]:
    """Returns (canonical_hash, witness_head, receipt_signature)."""
    if key is None:
        key = get_witness_key()
    evidence = canonical_evidence_dict(receipt_data)
    c_hash = compute_canonical_hash(evidence)
    w_head = get_latest_witness_head()
    sig = compute_receipt_signature(c_hash, w_head, key)
    return c_hash, w_head, sig

def verify_receipt(receipt: Any, key: Optional[bytes] = None) -> Tuple[bool, str]:
    """
    Verifies that the receipt's canonical hash matches its evidence fields,
    and that its cryptographic signature is valid.
    """
    if hasattr(receipt, "model_dump"):
        data = receipt.model_dump()
    elif hasattr(receipt, "dict"):
        data = receipt.dict()
    elif isinstance(receipt, dict):
        data = receipt
    else:
        return False, "INVALID_RECEIPT_TYPE"

    if key is None:
        key = get_witness_key()

    declared_hash = data.get("canonical_hash")
    declared_sig = data.get("receipt_signature")
    declared_head = data.get("witness_head_hmac")

    if not declared_hash or not declared_sig:
        return False, "UNSIGNED_RECEIPT"

    # 1. Verify canonical hash of evidence
    evidence = canonical_evidence_dict(data)
    expected_hash = compute_canonical_hash(evidence)
    if not hmac.compare_digest(declared_hash, expected_hash):
        return False, f"TAMPER_DETECTED: canonical_hash mismatch (expected {expected_hash}, got {declared_hash})"

    # 2. Verify signature
    expected_sig = compute_receipt_signature(declared_hash, declared_head or "", key)
    if not hmac.compare_digest(declared_sig, expected_sig):
        return False, "SIGNATURE_INVALID: Cryptographic signature mismatch"

    return True, "VERIFIED"

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m receipts.verify <path_to_receipt.json>")
        sys.exit(1)

    file_path = pathlib.Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    try:
        data = json.loads(file_path.read_text())
    except Exception as e:
        print(f"Error: invalid JSON in {file_path}: {e}")
        sys.exit(1)

    valid, reason = verify_receipt(data)
    if valid:
        print(f"[OK] Receipt {data.get('receipt_id')} verified: {reason}")
        print(f"     Canonical Hash: {data.get('canonical_hash')}")
        print(f"     Signature:      {data.get('receipt_signature')}")
        sys.exit(0)
    else:
        print(f"[FAILED] Receipt verification failed: {reason}")
        sys.exit(1)

if __name__ == "__main__":
    main()

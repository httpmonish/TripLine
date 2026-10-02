import time
import hmac
import hashlib
from typing import Tuple

DECISION_PROOF_HEADER = "X-Tripline-Decision-Proof"

def compute_decision_proof(args_hash: str, decision: str, secret_key: bytes, timestamp: float) -> str:
    """Computes an HMAC over args_hash, decision and timestamp."""
    payload = f"{args_hash}:{decision}:{int(timestamp)}".encode("utf-8")
    signature = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
    return f"{int(timestamp)}:{signature}"

def verify_decision_proof(proof_header: str, args_hash: str, secret_key: bytes, max_age: float = 60.0) -> Tuple[bool, str]:
    """
    Verifies that proof_header is a valid, unexpired decision proof for args_hash.
    Returns (is_valid, reason).
    """
    if not proof_header:
        return False, "MISSING_DECISION_PROOF"
        
    parts = proof_header.split(":")
    if len(parts) != 2:
        return False, "MALFORMED_DECISION_PROOF"
        
    ts_str, signature = parts
    try:
        ts = int(ts_str)
    except ValueError:
        return False, "INVALID_TIMESTAMP"
        
    now = time.time()
    if abs(now - ts) > max_age:
        return False, "EXPIRED_DECISION_PROOF"
        
    # Recompute expected signature for ALLOW/HOLD decisions
    # Gateway only issues proofs for ALLOW or HOLD
    valid = False
    for valid_dec in ("allow", "ALLOW", "hold", "HOLD"):
        expected = compute_decision_proof(args_hash, valid_dec, secret_key, ts).split(":")[1]
        if hmac.compare_digest(signature, expected):
            valid = True
            break
            
    if not valid:
        return False, "INVALID_PROOF_SIGNATURE"
        
    return True, "VALID"

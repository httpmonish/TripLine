import os
import json
import time
import hashlib
import hmac
import pathlib
from typing import Optional, Dict, Any

TRIPLINE_DIR = pathlib.Path(__file__).parent.parent.parent / ".tripline"
WITNESS_DIR = TRIPLINE_DIR / "witness"
KEY_FILE = TRIPLINE_DIR / "witness_key.txt"

def canonical_json(obj: Any) -> str:
    """Stable JSON serialization for deterministic hashing."""
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)

def compute_args_hash(mcp: str, action: str, params: Dict[str, Any]) -> str:
    """Deterministic hash of the tool invocation arguments."""
    payload = {
        "mcp": mcp,
        "action": action,
        "params": params
    }
    encoded = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def get_witness_key() -> bytes:
    if not KEY_FILE.exists():
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Create a default random test key if none exists
        KEY_FILE.write_bytes(os.urandom(32))
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return KEY_FILE.read_bytes()

def compute_hmac(key: bytes, record: Dict[str, Any]) -> str:
    # We must exclude the hmac of the current record itself if it is stored inside it,
    # but the instructions say record N contains prev_hmac.
    # We will just hash the exact canonical JSON of the record as written.
    encoded = canonical_json(record).encode("utf-8")
    return hmac.new(key, encoded, hashlib.sha256).hexdigest()

class WitnessRecorder:
    def __init__(self, mcp_name: str):
        self.mcp_name = mcp_name
        self.logfile = WITNESS_DIR / f"{mcp_name}.jsonl"
        WITNESS_DIR.mkdir(parents=True, exist_ok=True)
        self.key = get_witness_key()
    
    def get_last_record(self) -> Optional[Dict[str, Any]]:
        if not self.logfile.exists():
            return None
        # Reading large files by reading all lines is fine for MVP.
        lines = self.logfile.read_text().splitlines()
        if not lines:
            return None
        last_line = lines[-1].strip()
        if not last_line:
            return None
        return json.loads(last_line)
    
    def record_event(self,
                     call_id: str,
                     args_hash: str,
                     tool: str,
                     state: str,
                     side_effect: Any = "none",
                     result_hash: Optional[str] = None):
        last = self.get_last_record()
        
        seq = 1
        prev_hmac = ""
        if last:
            seq = last.get("seq", 0) + 1
            prev_hmac = compute_hmac(self.key, last)
            
        record = {
            "seq": seq,
            "prev_hmac": prev_hmac,
            "call_id": call_id,
            "args_hash": args_hash,
            "mcp": self.mcp_name,
            "tool": tool,
            "state": state,
            "side_effect": side_effect,
            "result_hash": result_hash,
            "ts_monotonic": time.monotonic(),
            "ts_wall": time.time()
        }
        
        # Append-only write
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(canonical_json(record) + "\n")

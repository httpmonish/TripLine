import json
import pathlib
from typing import List, Dict, Any, Tuple
import os
import sys
import importlib.util

def load_witness():
    p = pathlib.Path(__file__).parent.parent / "mcp" / "common" / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

witness_mod = load_witness()
compute_hmac = witness_mod.compute_hmac
get_witness_key = witness_mod.get_witness_key
canonical_json = witness_mod.canonical_json
WITNESS_DIR = witness_mod.WITNESS_DIR

def get_witness_dir() -> pathlib.Path:
    env = os.environ.get("TRIPLINE_WITNESS_DIR")
    if env:
        p = pathlib.Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p
    return WITNESS_DIR


def verify_chain(witness_file: pathlib.Path) -> Dict[str, Any]:
    """Verify the HMAC chain and sequence numbers of a witness file."""
    if not witness_file.exists():
        return {"valid": False, "reason": "File not found", "last_valid_seq": 0, "records": []}
    
    key = get_witness_key()
    lines = witness_file.read_text().splitlines()
    if not lines:
        return {"valid": False, "reason": "Empty witness file", "last_valid_seq": 0, "records": []}
        
    records = []
    expected_seq = 1
    expected_prev_hmac = ""
    
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except Exception:
            return {"valid": False, "reason": f"Malformed JSON at line {idx+1}", "last_valid_seq": expected_seq - 1, "records": records}
            
        if record.get("seq") != expected_seq:
            return {"valid": False, "reason": f"Sequence mismatch at seq {record.get('seq')}, expected {expected_seq}", "last_valid_seq": expected_seq - 1, "records": records}
            
        if record.get("prev_hmac") != expected_prev_hmac:
            return {"valid": False, "reason": f"HMAC mismatch at seq {expected_seq}", "last_valid_seq": expected_seq - 1, "records": records}
            
        records.append(record)
        expected_seq += 1
        expected_prev_hmac = compute_hmac(key, record)
        
    return {"valid": True, "reason": "Valid", "last_valid_seq": expected_seq - 1, "records": records}


def reconcile(decision: str, mcp: str, tool: str, args_hash: str) -> str:
    """
    decision: 'ALLOW', 'DENY', 'HOLD'
    mcp: MCP name e.g. 'repo-mcp'
    tool: e.g. 'write_patch'
    args_hash: expected args hash computed via compute_args_hash
    """
    witness_file = get_witness_dir() / f"{mcp}.jsonl"

    
    if not witness_file.exists():
        if decision in ["DENY", "HOLD"]:
            # Could be upstream denial.
            return "VALID DENY" if decision == "DENY" else "VERIFIED ZERO EXECUTIONS"
        return "UNVERIFIED"
        
    chain_info = verify_chain(witness_file)
    if not chain_info["valid"]:
        return "INVALID"
        
    records = chain_info["records"]
    
    # Filter for the specific call by args_hash
    # We might have multiple calls with the same args_hash, we evaluate them sequentially.
    # We need to find all events for this args_hash.
    events = [r for r in records if r["args_hash"] == args_hash and r["tool"] == tool]
    
    if not events:
        if decision in ["DENY", "HOLD"]:
            return "VALID DENY" if decision == "DENY" else "VERIFIED ZERO EXECUTIONS"
        return "UNVERIFIED"
        
    # We have some events. Group them by call_id if call_id is used.
    # Since call_id is empty string in our implementation, we group them chronologically.
    # Count execution_started and execution_completed.
    starts = sum(1 for r in events if r["state"] == "execution_started")
    completions = sum(1 for r in events if r["state"] == "execution_completed")
    
    if decision in ["DENY", "HOLD"]:
        if starts == 0:
            return "VERIFIED ZERO EXECUTIONS"
        else:
            return "INVALID" # Denied but executed?
            
    if decision == "ALLOW":
        if completions == 1:
            return "VERIFIED"
        elif completions > 1:
            # Maybe retry/duplicate
            return f"VERIFIED {completions} EXECUTIONS"
        elif starts > completions:
            return "started_without_completion"
        else:
            return "UNVERIFIED"
            
    return "UNVERIFIED"

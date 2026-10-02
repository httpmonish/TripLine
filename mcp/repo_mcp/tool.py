import os
import pathlib
import json
import importlib.util

def load_jail():
    p = pathlib.Path(__file__).parent.parent / "common" / "jail.py"
    spec = importlib.util.spec_from_file_location("jail", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

jail = load_jail()
canonicalize_path = jail.canonicalize_path
PathJailException = jail.PathJailException

FIXTURES_DIR = pathlib.Path(__file__).parent.parent.parent / "fixtures"
DEMO_REPO_DIR = FIXTURES_DIR / "demo_repo"

def _secure_resolve(path: str) -> pathlib.Path | str:
    # Server-side Tier 1 check
    from canary.state import get_current_run
    from canary.scan import check_tier1_access
    
    run_id = get_current_run()
    if run_id:
        t1_hit = check_tier1_access(path, run_id, "read_file")
        if t1_hit:
            # We just log it or we could block it, but Jail will block it anyway if outside.
            # "The canary signal should still be recorded even if the jail later rejects the request."
            # "SECURITY DECISION = jail/ArmorIQ". So we let jail do the rejection, or if jail allows it, we deny it?
            # "CANARY HIT = YES, SECURITY DECISION = jail/ArmorIQ"
            pass

    try:
        resolved = canonicalize_path(path, DEMO_REPO_DIR)
        return resolved
    except PathJailException as e:
        return f"error: {e.reason}"
    except Exception as e:
        return f"error: PATH_RESOLUTION_FAILED"

import hashlib
from typing import Any
import traceback

def load_witness():
    p = pathlib.Path(__file__).parent.parent / "common" / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

witness_mod = load_witness()
recorder = witness_mod.WitnessRecorder("repo-mcp")
compute_args_hash = witness_mod.compute_args_hash

def _hash_result(result: Any) -> str:
    encoded = witness_mod.canonical_json(result).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def list_dir(path: str = ".") -> str:
    """List directory contents in the repository."""
    args_hash = compute_args_hash("repo-mcp", "list_dir", {"path": path})
    recorder.record_event("", args_hash, "list_dir", "received")
    
    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        recorder.record_event("", args_hash, "list_dir", "rejected_by_jail")
        # Return structured error log
        return json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    recorder.record_event("", args_hash, "list_dir", "execution_started")
    if not resolved.exists():
        res = json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": "FILE_NOT_FOUND"})
        recorder.record_event("", args_hash, "list_dir", "execution_completed", result_hash=_hash_result(res))
        return res
        
    if not resolved.is_dir():
        res = json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": "NOT_A_DIRECTORY"})
        recorder.record_event("", args_hash, "list_dir", "execution_completed", result_hash=_hash_result(res))
        return res
        
    try:
        items = [f.name + ("/" if f.is_dir() else "") for f in resolved.iterdir()]
        res = "\n".join(items)
        recorder.record_event("", args_hash, "list_dir", "execution_completed", result_hash=_hash_result(res))
        return res
    except Exception as e:
        return f"error:list_failed:{e}"

def read_file(path: str) -> str:
    """Read a file from the repository."""
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": path})
    recorder.record_event("", args_hash, "read_file", "received")
    
    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        recorder.record_event("", args_hash, "read_file", "rejected_by_jail")
        return json.dumps({"tool": "read_file", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    recorder.record_event("", args_hash, "read_file", "execution_started")
    if not resolved.exists():
        res = json.dumps({"tool": "read_file", "path": path, "decision": "deny", "reason": "FILE_NOT_FOUND"})
        recorder.record_event("", args_hash, "read_file", "execution_completed", result_hash=_hash_result(res))
        return res
        
    try:
        res = resolved.read_text(errors="replace")
        recorder.record_event("", args_hash, "read_file", "execution_completed", result_hash=_hash_result(res))
        return res
    except Exception as e:
        return f"error:read_failed:{e}"

def write_patch(path: str, content: str) -> str:
    """Write/overwrite a file in the repository (simplified patch)."""
    args_hash = compute_args_hash("repo-mcp", "write_patch", {"path": path, "content": content})
    recorder.record_event("", args_hash, "write_patch", "received")
    
    # Server-side Tier 2 check
    from canary.state import get_current_run
    from canary.scan import scan_egress_payload
    run_id = get_current_run()
    if run_id:
        t2_hit = scan_egress_payload(content, run_id, "write_patch")
        if t2_hit:
            recorder.record_event("", args_hash, "write_patch", "rejected_by_jail")
            return json.dumps({"tool": "write_patch", "decision": "hold", "reason": "egress_canary_hit"})

    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        recorder.record_event("", args_hash, "write_patch", "rejected_by_jail")
        return json.dumps({"tool": "write_patch", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    recorder.record_event("", args_hash, "write_patch", "execution_started")
    try:
        sha_before = ""
        if resolved.exists():
            sha_before = hashlib.sha256(resolved.read_bytes()).hexdigest()
        
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content)
        
        sha_after = hashlib.sha256(resolved.read_bytes()).hexdigest()
        side_effect = {"path": path, "sha_before": sha_before, "sha_after": sha_after}
        
        res = f"success: wrote {path}"
        recorder.record_event("", args_hash, "write_patch", "execution_completed", side_effect=side_effect, result_hash=_hash_result(res))
        return res
    except Exception as e:
        return f"error:write_failed:{e}"

import os
import json
import pathlib
import hashlib
import importlib.util
from typing import Any

def load_witness():
    p = pathlib.Path(__file__).parent.parent / "common" / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

witness_mod = load_witness()
recorder = witness_mod.WitnessRecorder("issues-mcp")
compute_args_hash = witness_mod.compute_args_hash

def _hash_result(result: Any) -> str:
    encoded = witness_mod.canonical_json(result).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

FIXTURES_DIR = pathlib.Path(os.environ.get("TRIPLINE_FIXTURES_DIR", pathlib.Path(__file__).parent.parent.parent / "fixtures"))
ISSUES_FILE = pathlib.Path(os.environ.get("TRIPLINE_ISSUES_FILE", FIXTURES_DIR / "issues.json"))

def list_issues() -> str:
    """List all open issues."""
    args_hash = compute_args_hash("issues-mcp", "list_issues", {})
    recorder.record_event("", args_hash, "list_issues", "received")
    recorder.record_event("", args_hash, "list_issues", "execution_started")
    
    if not ISSUES_FILE.exists():
        res = "error: issues not found"
        recorder.record_event("", args_hash, "list_issues", "execution_completed", result_hash=_hash_result(res))
        return res
    
    issues = json.loads(ISSUES_FILE.read_text())
    res = json.dumps([{"id": i["id"], "title": i["title"], "status": i["status"]} for i in issues])
    recorder.record_event("", args_hash, "list_issues", "execution_completed", result_hash=_hash_result(res))
    return res

def read_issue(issue_id: str) -> str:
    """Read full details of a specific issue."""
    args_hash = compute_args_hash("issues-mcp", "read_issue", {"issue_id": issue_id})
    recorder.record_event("", args_hash, "read_issue", "received")
    recorder.record_event("", args_hash, "read_issue", "execution_started")
    
    if not ISSUES_FILE.exists():
        res = "error: issues not found"
        recorder.record_event("", args_hash, "read_issue", "execution_completed", result_hash=_hash_result(res))
        return res
        
    issues = json.loads(ISSUES_FILE.read_text())
    for issue in issues:
        if issue["id"] == issue_id:
            res = json.dumps(issue)
            recorder.record_event("", args_hash, "read_issue", "execution_completed", result_hash=_hash_result(res))
            return res
            
    res = f"error: issue {issue_id} not found"
    recorder.record_event("", args_hash, "read_issue", "execution_completed", result_hash=_hash_result(res))
    return res

def comment_issue(issue_id: str, text: str) -> str:
    """Add a comment to an issue."""
    import uuid
    from canary.state import get_current_run, get_current_trace, get_current_call
    trace_id = get_current_trace() or None
    call_id = get_current_call() or f"call-{uuid.uuid4().hex[:8]}"
    args_hash = compute_args_hash("issues-mcp", "comment_issue", {"issue_id": issue_id, "text": text})
    recorder.record_event(call_id, args_hash, "comment_issue", "received", trace_id=trace_id)
    
    # Server-side Tier 2 check
    from canary.scan import scan_egress_payload
    run_id = get_current_run()
    if run_id:
        t2_hit = scan_egress_payload(text, run_id, "comment_issue")
        if t2_hit:
            recorder.record_event(call_id, args_hash, "comment_issue", "held_by_gateway", side_effect="none", trace_id=trace_id)
            return json.dumps({"tool": "comment_issue", "decision": "hold", "reason": "egress_canary_hit"})
            
    recorder.record_event(call_id, args_hash, "comment_issue", "execution_started", trace_id=trace_id)
    res = f"comment added to {issue_id}"
    recorder.record_event(call_id, args_hash, "comment_issue", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
    return res

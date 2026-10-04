import time
import json
import pathlib
from typing import Optional, Dict, Any, Union
from .state import get_active_canaries, get_current_trace

def _log_canary_hit(hit_data: Dict[str, Any]):
    try:
        p = pathlib.Path(".tripline/canary_hits.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        record = dict(hit_data)
        record["trace_id"] = get_current_trace()
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass

def check_tier1_access(path: str, run_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Checks if the given path matches a Tier-1 canary placement for the run."""
    canaries = get_active_canaries(run_id)
    if not canaries:
        from .state import CANARY_DB
        from .mint import CanaryRecord
        if CANARY_DB.exists():
            try:
                data = json.loads(CANARY_DB.read_text())
                canaries = [CanaryRecord(**d) for d in data]
            except Exception:
                pass
    t1_canaries = [c for c in canaries if c.tier == 1]
    
    import unicodedata
    path_norm = unicodedata.normalize("NFKC", str(path)).strip("/").lower().replace("\\", "/")

    for c in t1_canaries:
        if tool_name == "list_dir":
            continue
            
        intended_norm = unicodedata.normalize("NFKC", str(c.intended_placement)).strip("/").lower().replace("\\", "/")
        if intended_norm in path_norm or path_norm in intended_norm or path_norm.endswith(intended_norm):
            hit = {
                "event": "canary_hit",
                "tier": 1,
                "run_id": run_id,
                "canary_id": c.canary_id,
                "tool": tool_name,
                "path": path,
                "attempt": True,
                "decision": "deny",
                "timestamp": time.time()
            }
            _log_canary_hit(hit)
            return hit
            
    return None

def scan_egress_payload(payload: Union[str, dict], run_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Scans the outbound payload for Tier-2 canary IDs."""
    if not payload:
        return None
        
    payload_str = str(payload)
    
    canaries = get_active_canaries(run_id)
    t2_canaries = [c for c in canaries if c.tier == 2]
    
    for c in t2_canaries:
        offset = payload_str.find(c.canary_id)
        if offset != -1:
            hit = {
                "event": "egress_canary_hit",
                "tier": 2,
                "run_id": run_id,
                "canary_id": c.canary_id,
                "tool": tool_name,
                "decision": "hold",
                "payload_offset": offset,
                "matched": True,
                "timestamp": time.time()
            }
            _log_canary_hit(hit)
            return hit
            
    return None

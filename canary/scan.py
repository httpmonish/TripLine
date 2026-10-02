import time
from typing import Optional, Dict, Any, Union
from .state import get_active_canaries

def check_tier1_access(path: str, run_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Checks if the given path matches a Tier-1 canary placement for the run."""
    canaries = get_active_canaries(run_id)
    t1_canaries = [c for c in canaries if c.tier == 1]
    
    for c in t1_canaries:
        # Note: listing the directory shouldn't trigger it, so we only trigger on exact read attempts.
        # But for safety, we assume the caller filters by tool_name (e.g. read_file vs list_dir).
        if tool_name == "list_dir":
            continue
            
        if c.intended_placement in path or path in c.intended_placement:
            return {
                "event": "canary_hit",
                "tier": 1,
                "run_id": run_id,
                "canary_id": c.canary_id,
                "tool": tool_name,
                "path": path,
                "attempt": True,
                "decision": "deny", # Will be overriden by ArmorIQ/Jail if they block it
                "timestamp": time.time()
            }
            
    return None


def scan_egress_payload(payload: Union[str, dict], run_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Scans the outbound payload for Tier-2 canary IDs."""
    if not payload:
        return None
        
    payload_str = str(payload)
    
    canaries = get_active_canaries(run_id)
    # We primarily care about Tier 2 egress
    t2_canaries = [c for c in canaries if c.tier == 2]
    
    for c in t2_canaries:
        offset = payload_str.find(c.canary_id)
        if offset != -1:
            return {
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
            
    return None

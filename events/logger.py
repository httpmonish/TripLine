import os
import json
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEFAULT_EVENTS_FILE = pathlib.Path("results/demo/events.jsonl")

def get_events_file() -> pathlib.Path:
    p = os.environ.get("TRIPLINE_EVENTS_FILE")
    if p:
        return pathlib.Path(p)
    return DEFAULT_EVENTS_FILE

def emit_event(
    trace_id: str,
    stage: int,
    stage_name: str,
    event: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Emits a structured forensic event at the exact moment it occurs in the pipeline.
    Appends immediately to events.jsonl with real-time UTC timestamp.
    """
    events_file = get_events_file()
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    record = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "stage_name": stage_name,
        "event": event,
        **kwargs
    }
    
    with open(events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
        
    return record

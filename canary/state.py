import dataclasses
import pathlib
import json
import os
from typing import List, Dict, Any
from .mint import CanaryRecord

CANARY_DB = pathlib.Path(__file__).parent.parent / ".tripline" / "canaries.json"

def record_active_canary(record: CanaryRecord):
    CANARY_DB.parent.mkdir(parents=True, exist_ok=True)
    if CANARY_DB.exists():
        data = json.loads(CANARY_DB.read_text())
    else:
        data = []
    
    data.append(dataclasses.asdict(record))
    CANARY_DB.write_text(json.dumps(data, indent=2))

def get_active_canaries(run_id: str) -> List[CanaryRecord]:
    if not CANARY_DB.exists():
        return []
    data = json.loads(CANARY_DB.read_text())
    return [CanaryRecord(**d) for d in data if d["run_id"] == run_id]

def set_current_run(run_id: str):
    """Sets the globally active run id for the MCP server context in demo mode."""
    p = CANARY_DB.parent / "current_run.txt"
    p.write_text(run_id)

def get_current_run() -> str:
    p = CANARY_DB.parent / "current_run.txt"
    if p.exists():
        return p.read_text().strip()
    return ""

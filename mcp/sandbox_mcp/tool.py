import os
import re
import shlex
import subprocess
import pathlib

SANDBOX_SB = """(version 1)
(allow default)
(deny network*)
(allow network* (local ip) (local unix))
"""

SB_FILE = pathlib.Path(__file__).parent / "sandbox.sb"

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
recorder = witness_mod.WitnessRecorder("sandbox-mcp")
compute_args_hash = witness_mod.compute_args_hash

def _hash_result(result: Any) -> str:
    encoded = witness_mod.canonical_json(result).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def _ensure_sb():
    if not SB_FILE.exists():
        SB_FILE.write_text(SANDBOX_SB)

def run_tests(test_selector: str) -> str:
    """
    Run pytest with the given selector (e.g. 'test_issue_1').
    Executes in a sandbox with NO NETWORK ACCESS.
    Rejects arbitrary extra commands or shell characters.
    """
    args_hash = compute_args_hash("sandbox-mcp", "run_tests", {"test_selector": test_selector})
    recorder.record_event("", args_hash, "run_tests", "received")
    
    _ensure_sb()
    
    # Strict validation of test_selector to prevent arbitrary execution
    # Only allow word characters, dashes, dots, slashes.
    if not re.match(r"^[\w\.\-/:]+$", test_selector):
        recorder.record_event("", args_hash, "run_tests", "rejected_by_jail")
        return "error: invalid test selector (arbitrary arguments rejected)"
        
    if test_selector.startswith("-"):
        recorder.record_event("", args_hash, "run_tests", "rejected_by_jail")
        return "error: test selector cannot start with a flag"
        
    recorder.record_event("", args_hash, "run_tests", "execution_started")
    cwd = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "demo_repo"
    
    cmd = [
        "sandbox-exec",
        "-f",
        str(SB_FILE),
        "../../.venv313/bin/pytest",
        "test_demo.py::" + test_selector if "::" not in test_selector and "/" not in test_selector else test_selector
    ]
    
    try:
        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=10)
        res = result.stdout + "\n" + result.stderr
        recorder.record_event("", args_hash, "run_tests", "execution_completed", result_hash=_hash_result(res))
        return res
    except subprocess.TimeoutExpired:
        res = "error: test execution timed out"
        recorder.record_event("", args_hash, "run_tests", "execution_completed", result_hash=_hash_result(res))
        return res
    except Exception as e:
        return f"error: sandbox execution failed: {e}"

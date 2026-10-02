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

def _ensure_sb():
    if not SB_FILE.exists():
        SB_FILE.write_text(SANDBOX_SB)

def run_tests(test_selector: str) -> str:
    """
    Run pytest with the given selector (e.g. 'test_issue_1').
    Executes in a sandbox with NO NETWORK ACCESS.
    Rejects arbitrary extra commands or shell characters.
    """
    _ensure_sb()
    
    # Strict validation of test_selector to prevent arbitrary execution
    # Only allow word characters, dashes, dots, slashes.
    if not re.match(r"^[\w\.\-/:]+$", test_selector):
        return "error: invalid test selector (arbitrary arguments rejected)"
        
    if test_selector.startswith("-"):
        return "error: test selector cannot start with a flag"
        
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
        return result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        return "error: test execution timed out"
    except Exception as e:
        return f"error: sandbox execution failed: {e}"

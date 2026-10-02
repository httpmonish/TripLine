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
    try:
        resolved = canonicalize_path(path, DEMO_REPO_DIR)
        return resolved
    except PathJailException as e:
        return f"error: {e.reason}"
    except Exception as e:
        return f"error: PATH_RESOLUTION_FAILED"

def list_dir(path: str = ".") -> str:
    """List directory contents in the repository."""
    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        # Return structured error log
        return json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    if not resolved.exists():
        return json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": "FILE_NOT_FOUND"})
        
    if not resolved.is_dir():
        return json.dumps({"tool": "list_dir", "path": path, "decision": "deny", "reason": "NOT_A_DIRECTORY"})
        
    try:
        items = [f.name + ("/" if f.is_dir() else "") for f in resolved.iterdir()]
        return "\n".join(items)
    except Exception as e:
        return f"error:list_failed:{e}"

def read_file(path: str) -> str:
    """Read a file from the repository."""
    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        return json.dumps({"tool": "read_file", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    if not resolved.exists():
        return json.dumps({"tool": "read_file", "path": path, "decision": "deny", "reason": "FILE_NOT_FOUND"})
        
    try:
        return resolved.read_text(errors="replace")
    except Exception as e:
        return f"error:read_failed:{e}"

def write_patch(path: str, content: str) -> str:
    """Write/overwrite a file in the repository (simplified patch)."""
    resolved = _secure_resolve(path)
    if isinstance(resolved, str):
        return json.dumps({"tool": "write_patch", "path": path, "decision": "deny", "reason": resolved.replace("error: ", "")})
        
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content)
        return f"success: wrote {path}"
    except Exception as e:
        return f"error:write_failed:{e}"

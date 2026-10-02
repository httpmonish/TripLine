import pathlib
import importlib.util

def load_jail():
    p = pathlib.Path(__file__).parent.parent / "mcp" / "common" / "jail.py"
    spec = importlib.util.spec_from_file_location("jail", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

jail = load_jail()
canonicalize_path = jail.canonicalize_path
PathJailException = jail.PathJailException

def validate_gateway_path(raw_path: str, trusted_root: pathlib.Path) -> dict:
    """
    Early warning check for paths in the gateway.
    Returns {"decision": "allow"|"deny", "reason": "..."}
    """
    try:
        canonicalize_path(raw_path, trusted_root)
        return {"decision": "allow", "reason": "safe_path"}
    except PathJailException as e:
        return {"decision": "deny", "reason": e.reason}

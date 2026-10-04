import pytest
import re
import subprocess
import pathlib

def test_phase12_security_boundary_integrity():
    """Path jail rejects paths outside repo root even without a gateway session."""
    import importlib.util, pathlib
    tool_path = pathlib.Path(__file__).parent.parent / "mcp" / "repo_mcp" / "tool.py"
    spec = importlib.util.spec_from_file_location("repo_mcp_tool", tool_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod._secure_resolve("../../etc/passwd")
    assert isinstance(result, str) and result.startswith("error:"), (
        f"Expected path jail to return error: string, got {result!r}"
    )


def test_phase12_no_fallback_to_unsafe_defaults():
    """Replan lock returns blocked status when replan is attempted after untrusted ingestion."""
    from gateway.replan_lock import ReplanLock
    lock = ReplanLock()
    # Set up state: plan -> authorized -> t3 ingested (simulates untrusted input arriving)
    lock.on_plan_created({"tools": ["read_file"]})
    lock.on_authorization_granted()
    lock.on_t3_read("untrusted_issue_body")
    result = lock.check_replan_request()
    assert result.get("event") == "replan_blocked", (
        f"Expected replan_blocked, got {result}"
    )



def test_phase12_secret_scan():
    """Scans all tracked and untracked files for exposed API key patterns."""
    patterns = [
        re.compile(r"ak_(live|test|claw)_[a-zA-Z0-9]{16,}"),
        re.compile(r"sk-(ant|proj)-[a-zA-Z0-9_\-]{16,}"),
    ]
    # Check tracked and untracked non-ignored files
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        text=True
    )
    files_to_check = [f.strip() for f in output.splitlines() if f.strip()]
    
    violations = []
    for file_path_str in files_to_check:
        path = pathlib.Path(file_path_str)
        # Skip this test file itself
        if path.name == "test_phase12_hardening.py":
            continue
        # Skip binary / cache files / git objects
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".pyc", ".db", ".sqlite"]:
            continue
        if any(part in path.parts for part in [".git", ".pytest_cache", ".venv313", "__pycache__"]):
            continue
        if not path.is_file():
            continue
            
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        for pat in patterns:
            matches = pat.findall(content)
            if matches:
                violations.append((file_path_str, pat.pattern, len(matches)))
            
    assert not violations, f"Secret pattern detected in repository files: {violations}"

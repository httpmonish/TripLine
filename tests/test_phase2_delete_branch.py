"""
tests/test_phase2_delete_branch.py — Unit tests for delete_branch safeguards and behavior.
"""

import json
import os
import pathlib
import pytest
import shutil
import tempfile

import importlib.util

def load_delete_branch_mod():
    p = pathlib.Path(__file__).resolve().parent.parent / "mcp" / "repo_mcp" / "delete_branch.py"
    spec = importlib.util.spec_from_file_location("delete_branch_mod", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

delete_branch_mod = load_delete_branch_mod()
delete_branch = delete_branch_mod.delete_branch
from scripts.make_sandbox_repo import create_sandbox_repo, MARKER_FILE_NAME


@pytest.fixture
def sandbox_repo(tmp_path):
    sandbox = create_sandbox_repo(tmp_path / "sandbox")
    old_env = os.environ.get("TRIPLINE_SANDBOX_REPO")
    os.environ["TRIPLINE_SANDBOX_REPO"] = str(sandbox)
    yield sandbox
    if old_env is not None:
        os.environ["TRIPLINE_SANDBOX_REPO"] = old_env
    else:
        os.environ.pop("TRIPLINE_SANDBOX_REPO", None)


def test_delete_branch_successful(sandbox_repo):
    """Deleting an existing non-protected branch succeeds."""
    res_str = delete_branch("stale/old-experiment")
    res = json.loads(res_str)
    assert res["status"] == "deleted"
    assert res["name"] == "stale/old-experiment"

    # Verify branch is gone in git
    import subprocess
    proc = subprocess.run(["git", "-C", str(sandbox_repo), "branch", "--list", "stale/old-experiment"], capture_output=True, text=True)
    assert "stale/old-experiment" not in proc.stdout


def test_delete_branch_nonexistent(sandbox_repo):
    """Deleting a non-existent branch returns not_found or error."""
    res_str = delete_branch("nonexistent-branch-123")
    res = json.loads(res_str)
    assert res["status"] in ("not_found", "error")


def test_safeguard_refuses_unset_env(sandbox_repo):
    """Refuses if TRIPLINE_SANDBOX_REPO is unset."""
    os.environ.pop("TRIPLINE_SANDBOX_REPO", None)
    res = json.loads(delete_branch("stale/old-experiment"))
    assert res["status"] == "error"
    assert "unset" in res["error"]


def test_safeguard_refuses_project_repo():
    """Refuses if TRIPLINE_SANDBOX_REPO points to the project repo."""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    os.environ["TRIPLINE_SANDBOX_REPO"] = str(repo_root)
    res = json.loads(delete_branch("stale/old-experiment"))
    assert res["status"] == "error"
    assert "project repository" in res["error"] or "marker" in res["error"]


def test_safeguard_refuses_missing_marker(sandbox_repo):
    """Refuses if marker file is missing."""
    marker = sandbox_repo / MARKER_FILE_NAME
    if marker.exists():
        marker.unlink()
    res = json.loads(delete_branch("stale/old-experiment"))
    assert res["status"] == "error"
    assert "marker" in res["error"]


def test_safeguard_refuses_protected_branches(sandbox_repo):
    """Refuses main, master, develop, and release/*."""
    for protected in ["main", "master", "develop", "release/v1.0.0"]:
        res = json.loads(delete_branch(protected))
        assert res["status"] == "error"
        assert "protected" in res["error"] or "currently checked-out" in res["error"]


def test_safeguard_refuses_current_branch(sandbox_repo):
    """Refuses to delete currently checked-out branch."""
    res = json.loads(delete_branch("main"))
    assert res["status"] == "error"


def test_safeguard_rejects_option_injection(sandbox_repo):
    """Rejects names starting with '-'."""
    for bad in ["--all", "-D", "-m"]:
        res = json.loads(delete_branch(bad))
        assert res["status"] == "error"
        assert "option injection" in res["error"] or "invalid characters" in res["error"]


def test_safeguard_rejects_path_traversal(sandbox_repo):
    """Rejects '..' in branch name."""
    res = json.loads(delete_branch("../feature"))
    assert res["status"] == "error"
    assert "traversal" in res["error"] or "invalid characters" in res["error"]


def test_safeguard_rejects_whitespace(sandbox_repo):
    """Rejects whitespace in branch name."""
    res = json.loads(delete_branch("feature branch"))
    assert res["status"] == "error"
    assert "whitespace" in res["error"]

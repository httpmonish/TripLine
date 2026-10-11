import sys
import json
import uuid
import time
import pytest
import asyncio
import pathlib
import subprocess
import copy
import importlib.util
from typing import Dict, Any

def load_witness():
    p = pathlib.Path(__file__).parent.parent / "mcp" / "common" / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_reconcile():
    p = pathlib.Path(__file__).parent.parent / "witness" / "reconcile.py"
    spec = importlib.util.spec_from_file_location("reconcile", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

witness = load_witness()
reconcile_mod = load_reconcile()

WITNESS_DIR = witness.WITNESS_DIR
KEY_FILE = witness.KEY_FILE
compute_args_hash = witness.compute_args_hash
canonical_json = witness.canonical_json

verify_chain = reconcile_mod.verify_chain
reconcile = reconcile_mod.reconcile

FIXTURES_DIR = pathlib.Path(__file__).parent.parent / "fixtures"
DEMO_REPO_DIR = FIXTURES_DIR / "demo_repo"
ISSUES_FILE = FIXTURES_DIR / "issues.json"

@pytest.fixture(autouse=True)
def setup_teardown(tmp_path, monkeypatch):
    global WITNESS_DIR, FIXTURES_DIR, DEMO_REPO_DIR, ISSUES_FILE
    # Isolated witness dir
    test_witness = tmp_path / "witness"
    test_witness.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TRIPLINE_WITNESS_DIR", str(test_witness))
    monkeypatch.setattr(witness, "WITNESS_DIR", test_witness)
    monkeypatch.setattr(reconcile_mod, "WITNESS_DIR", test_witness)
    prev_witness = WITNESS_DIR
    WITNESS_DIR = test_witness

    # Isolated fixtures dir (copy tracked fixtures so real fake_key is never touched)
    test_fixtures = tmp_path / "fixtures"
    import shutil
    shutil.copytree(pathlib.Path(__file__).parent.parent / "fixtures", test_fixtures)
    prev_fixtures = FIXTURES_DIR
    FIXTURES_DIR = test_fixtures
    DEMO_REPO_DIR = test_fixtures / "demo_repo"
    ISSUES_FILE = test_fixtures / "issues.json"

    yield

    WITNESS_DIR = prev_witness
    FIXTURES_DIR = prev_fixtures
    DEMO_REPO_DIR = prev_fixtures / "demo_repo"
    ISSUES_FILE = prev_fixtures / "issues.json"

def load_mcp_tool(mcp_dir: str):
    p = pathlib.Path(__file__).parent.parent / "mcp" / mcp_dir / "tool.py"
    spec = importlib.util.spec_from_file_location(mcp_dir, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _run_mcp_tool(mcp: str, tool: str, **kwargs):
    if mcp == "repo-mcp":
        mod = load_mcp_tool("repo_mcp")
        if tool == "list_dir":
            return mod.list_dir(**kwargs)
        elif tool == "read_file":
            return mod.read_file(**kwargs)
        elif tool == "write_patch":
            return mod.write_patch(**kwargs)
    elif mcp == "issues-mcp":
        mod = load_mcp_tool("issues_mcp")
        if tool == "list_issues":
            return mod.list_issues()
        elif tool == "read_issue":
            return mod.read_issue(**kwargs)
        elif tool == "comment_issue":
            return mod.comment_issue(**kwargs)
    elif mcp == "sandbox-mcp":
        mod = load_mcp_tool("sandbox_mcp")
        return mod.run_tests(**kwargs)
    return None

def test_witness_record_creation():
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    
    f = WITNESS_DIR / "repo-mcp.jsonl"
    assert f.exists()
    lines = f.read_text().splitlines()
    assert len(lines) >= 2 # received, execution_started, execution_completed (wait list_dir might have 3)
    
    records = [json.loads(l) for l in lines]
    assert records[0]["state"] == "received"
    assert records[-1]["state"] == "execution_completed"

def test_allowed_execution():
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "src/main.py"})
    _run_mcp_tool("repo-mcp", "read_file", path="src/main.py")
    
    res = reconcile("ALLOW", "repo-mcp", "read_file", args_hash)
    assert res == "VERIFIED"

def test_denied_before_mcp():
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "doesnotexist.py"})
    # Do not execute the tool!
    res = reconcile("DENY", "repo-mcp", "read_file", args_hash)
    assert res == "VALID DENY"

def test_mcp_jail_rejection():
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "../../outside.txt"})
    _run_mcp_tool("repo-mcp", "read_file", path="../../outside.txt")
    
    res = reconcile("DENY", "repo-mcp", "read_file", args_hash)
    assert res == "VERIFIED ZERO EXECUTIONS"

def test_held_egress():
    from canary.plant import plant_canaries
    run_id = str(uuid.uuid4())
    res_plant = plant_canaries(run_id, DEMO_REPO_DIR, FIXTURES_DIR)
    t2_id = res_plant["t2"].canary_id
    
    from canary.state import set_current_run
    set_current_run(run_id)
    
    args_hash = compute_args_hash("repo-mcp", "write_patch", {"path": "src/main.py", "content": f"leak {t2_id}"})
    _run_mcp_tool("repo-mcp", "write_patch", path="src/main.py", content=f"leak {t2_id}")
    
    res = reconcile("HOLD", "repo-mcp", "write_patch", args_hash)
    assert res == "VERIFIED ZERO EXECUTIONS"

def test_tampered_record():
    args_hash = compute_args_hash("repo-mcp", "list_dir", {"path": "."})
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    
    # Tamper with the state of the first record
    rec = json.loads(lines[0])
    rec["state"] = "execution_started"
    lines[0] = canonical_json(rec)
    f.write_text("\n".join(lines) + "\n")
    
    res = verify_chain(f)
    assert not res["valid"]

def test_removed_record():
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    # Remove second line
    del lines[1]
    f.write_text("\n".join(lines) + "\n")
    
    res = verify_chain(f)
    assert not res["valid"]
    assert "Sequence mismatch" in res["reason"] or "HMAC mismatch" in res["reason"]

def test_sequence_tampering():
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    rec = json.loads(lines[-1])
    rec["seq"] = 999
    lines[-1] = canonical_json(rec)
    f.write_text("\n".join(lines) + "\n")
    
    res = verify_chain(f)
    assert not res["valid"]
    assert "Sequence mismatch" in res["reason"]

def test_args_hash_tampering():
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["args_hash"] = "fakehash"
    lines[0] = canonical_json(rec)
    f.write_text("\n".join(lines) + "\n")
    
    res = verify_chain(f)
    assert not res["valid"]

def test_tool_tampering():
    _run_mcp_tool("repo-mcp", "list_dir", path=".")
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["tool"] = "write_patch"
    lines[0] = canonical_json(rec)
    f.write_text("\n".join(lines) + "\n")
    
    res = verify_chain(f)
    assert not res["valid"]

def test_missing_witness():
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "src/main.py"})
    # Do not execute, simulating missing evidence
    res = reconcile("ALLOW", "repo-mcp", "read_file", args_hash)
    assert res == "UNVERIFIED"

def test_write_side_effect():
    content = "print('hello')"
    args_hash = compute_args_hash("repo-mcp", "write_patch", {"path": "src/main.py", "content": content})
    _run_mcp_tool("repo-mcp", "write_patch", path="src/main.py", content=content)
    
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    completed_rec = json.loads(lines[-1])
    assert completed_rec["state"] == "execution_completed"
    assert "sha_before" in completed_rec["side_effect"]
    assert "sha_after" in completed_rec["side_effect"]
    
    res = reconcile("ALLOW", "repo-mcp", "write_patch", args_hash)
    assert res == "VERIFIED"

def test_write_rejection():
    args_hash = compute_args_hash("repo-mcp", "write_patch", {"path": "../../outside.txt", "content": "123"})
    _run_mcp_tool("repo-mcp", "write_patch", path="../../outside.txt", content="123")
    
    f = WITNESS_DIR / "repo-mcp.jsonl"
    lines = f.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["state"] == "received"
    assert json.loads(lines[1])["state"] == "rejected_by_jail"
    
    res = reconcile("DENY", "repo-mcp", "write_patch", args_hash)
    assert res == "VERIFIED ZERO EXECUTIONS"

def test_double_execution():
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "src/main.py"})
    _run_mcp_tool("repo-mcp", "read_file", path="src/main.py")
    _run_mcp_tool("repo-mcp", "read_file", path="src/main.py")
    
    res = reconcile("ALLOW", "repo-mcp", "read_file", args_hash)
    assert "2 EXECUTIONS" in res

def test_partial_execution():
    # We will simulate a partial execution by writing the logs manually 
    # to emulate a crash right after execution_started.
    args_hash = compute_args_hash("repo-mcp", "read_file", {"path": "src/main.py"})
    
    rec = witness.WitnessRecorder("repo-mcp")
    rec.record_event("", args_hash, "read_file", "received")
    rec.record_event("", args_hash, "read_file", "execution_started")
    
    res = reconcile("ALLOW", "repo-mcp", "read_file", args_hash)
    assert res == "started_without_completion"

def test_key_inaccessibility():
    # The agent does not know the key.
    # LLM cannot read KEY_FILE if restricted by path jail.
    # In Phase 4, the path jail canonicalizes and prevents `../../.tripline`
    # Let's test that jail explicitly blocks it!
    res = _run_mcp_tool("repo-mcp", "read_file", path="../../.tripline/witness_key.txt")
    assert "DENY" in res or "error" in res or "DENIED" in res or "deny" in res or "error:" in res

def test_witness_file_manipulation():
    # The agent cannot write to the witness log through write_patch
    res = _run_mcp_tool("repo-mcp", "write_patch", path="../../.tripline/witness/repo-mcp.jsonl", content="fake")
    assert "DENY" in res or "error" in res or "DENIED" in res or "deny" in res or "error:" in res



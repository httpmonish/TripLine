import asyncio
import pytest
from mcp import Client
from agent.loop import AgentLoop
from gateway.replan_lock import ReplanLock, LifecycleState
from agent.planner import Planner
import fixtures.reset_demo_repo as reset_repo
import os

API_KEY = os.environ.get("ARMORIQ_API_KEY", "")
HAS_KEY = bool(API_KEY)
if not HAS_KEY:
    try:
        import pathlib
        _cred_file = pathlib.Path.home() / ".armoriq" / "credentials.json"
        if _cred_file.exists():
            import json
            _data = json.loads(_cred_file.read_text())
            _k = _data.get("apiKey", "")
            if isinstance(_k, str) and _k.startswith("ak_"):
                HAS_KEY = True
    except Exception:
        pass

needs_key = pytest.mark.skipif(not HAS_KEY, reason="ARMORIQ_API_KEY not set")

def _mcp_server_reachable() -> bool:
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 8000), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False

needs_mcp = pytest.mark.skipif(not _mcp_server_reachable(), reason="MCP server not running")


@pytest.fixture(autouse=True)
def reset_fixtures():
    reset_repo.reset()


def test_plan_before_ingest():
    # Test 1 & 2: Plan Before Ingest and T3 Tracking
    lock = ReplanLock()
    planner = Planner()
    
    plan = planner.create_initial_plan("Fix issue #3")
    lock.on_plan_created(plan)
    lock.on_authorization_granted()
    
    assert lock.state == LifecycleState.AUTHORIZED
    assert not lock.t3_ingested
    
    # Read issue simulates T3 ingestion
    lock.on_t3_read("read_issue")
    assert lock.t3_ingested
    assert lock.state == LifecycleState.T3_INGESTED
    
    events = lock.events
    # Check ordering
    plan_idx = next(i for i, e in enumerate(events) if e["event"] == "plan_created")
    auth_idx = next(i for i, e in enumerate(events) if e["event"] == "authorization_granted")
    t3_idx = next(i for i, e in enumerate(events) if e["event"] == "t3_ingested")
    
    assert plan_idx < t3_idx
    assert auth_idx < t3_idx

def test_plan_before_ingest_violation():
    lock = ReplanLock()
    with pytest.raises(RuntimeError):
        lock.on_t3_read("read_issue")

@needs_key
@needs_mcp
def test_attack_d_plan_laundering():
    # Test 3, 4, 5
    async def _run():
        loop = AgentLoop()
        result = await loop.run_task("Fix issue #1", "attack_d")
        
        events = result["events"]
        t3_idx = next(i for i, e in enumerate(events) if e["event"] == "t3_ingested")
        replan_req_idx = next(i for i, e in enumerate(events) if e["event"] == "replan_requested")
        replan_block_idx = next(i for i, e in enumerate(events) if e["event"] == "replan_blocked")
        
        assert t3_idx < replan_req_idx < replan_block_idx
        
        # Ensure no malicious execution
        malicious_step = next((s for s in result["steps"] if s["tool"] == "malicious_hack"), None)
        assert malicious_step is not None
        assert malicious_step["allowed"] == False
        assert malicious_step["error"] == "ArmorIQ Denied: Replan blocked (T3 ingested)"
        assert result["status"] == "failed_auth"

    asyncio.run(_run())

@needs_key
@needs_mcp
def test_legitimate_replan_fallback():
    # Test 6: Legitimate Replan
    # Native human-approved re-plan/hold was not available in the installed SDK/mock,
    # so Tripline fails closed.
    async def _run():
        loop = AgentLoop()
        result = await loop.run_task("Fix issue #1", "legitimate_replan")
        
        events = result["events"]
        # It's blocked anyway because there's no native approval capability in the demo mock that works async.
        replan_block = next((e for e in events if e["event"] == "replan_blocked"), None)
        assert replan_block is not None
        
        legit_step = next((s for s in result["steps"] if s["tool"] == "read_project_info"), None)
        assert legit_step is not None
        assert legit_step["allowed"] == False
        assert legit_step["error"] == "ArmorIQ Denied: Replan blocked (T3 ingested)"
        
    asyncio.run(_run())

@needs_key
@needs_mcp
def test_normal_post_t3_action():
    # Test 7: Normal post-t3 action
    async def _run():
        loop = AgentLoop()
        # Normal flow (issue-1) should succeed and use allowed tools post T3
        result = await loop.run_task("Fix issue #1", "issue-1")
        assert result["status"] == "success"
        
        events = result["events"]
        t3_idx = next(i for i, e in enumerate(events) if e["event"] == "t3_ingested")
        assert t3_idx is not None
        
        # Tools after t3 (like list_dir, read_file, write_patch) were executed
        steps_after_t3 = [s for s in result["steps"] if s["tool"] in ["list_dir", "read_file", "write_patch"]]
        for step in steps_after_t3:
            assert step["allowed"] == True
            assert step["error"] is None
            
    asyncio.run(_run())

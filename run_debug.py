import asyncio
from agent.loop import AgentLoop
from canary.plant import plant_canaries
import uuid
import agent.loop
from agent.llm import LLMAdapter
import os
from pathlib import Path

DEMO_REPO_DIR = Path(__file__).parent / "demo_repo"
FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"

async def _run():
    original_loop_uuid4 = agent.loop.uuid.uuid4
    original_uuid4 = uuid.uuid4
    
    run_uuid = uuid.uuid4()
    run_id = str(run_uuid)
    print(f"RUN_ID planted: {run_id}")
    res = plant_canaries(run_id, DEMO_REPO_DIR, FIXTURES_DIR)
    t2_id = res["t2"].canary_id
    print(f"T2 canary ID: {t2_id}")
    
    call_count = 0
    def mock_uuid4():
        nonlocal call_count
        if call_count == 0:
            call_count += 1
            print(f"DEBUG: Returning run_uuid {run_uuid}")
            return run_uuid
        ret = original_uuid4()
        print(f"DEBUG: Returning new uuid {ret}")
        return ret
        
    agent.loop.uuid.uuid4 = mock_uuid4
    original_gen = LLMAdapter.generate
    
    loop = AgentLoop()
    
    payload = {"issue_id": "issue-3", "text": f"Deployment config: {t2_id}"}
    LLMAdapter.generate = lambda self, t, i, s: {"tool": "comment_issue", "arguments": payload}
    
    artifact = await loop.run_task("Task", "issue-3")
    
    print(f"STATUS: {artifact['status']}")
    print(f"PROVENANCE: {artifact['provenance']}")

asyncio.run(_run())

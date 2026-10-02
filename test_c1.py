import asyncio
from provenance.models import ContextItem, generate_content_hash, verify_context_item
from provenance.match import normalize_content, find_c1_match, check_c0_association
from provenance.ledger import record_item, get_run_context, DB_PATH
from agent.loop import AgentLoop
from fixtures.reset_demo_repo import reset
reset()

async def run():
    loop = AgentLoop()
    result = await loop.run_task("Fix issue #3", "attack_a")
    run_id = result["run_id"]
    items = get_run_context(run_id)
    print("PROVENANCE:", result["provenance"])
    for i in items:
        if i.source_type.startswith("tool_output:read_issue"):
            print("ISSUE_CONTENT:", i.normalized_content)
            print("MATCH:", find_c1_match("~/.ssh/fake_key", run_id))
    
asyncio.run(run())

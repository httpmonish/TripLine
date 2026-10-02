import asyncio
import json
import logging
from typing import Any, Dict

from mcp import Client
from armoriq_helper import build_client
from armoriq_sdk import SessionOptions, ToolCall
from .llm import LLMAdapter
from .planner import Planner
from gateway.replan_lock import ReplanLock
from gateway.taint_rule import evaluate_taint
from gateway.budget import ToolBudget
import uuid
import time
from provenance.models import ContextItem, generate_content_hash
from provenance.ledger import record_item
from provenance.match import find_c1_match, check_c0_association, normalize_content

logger = logging.getLogger(__name__)

class AgentLoop:
    def __init__(self, mcp_url="http://127.0.0.1:8000/mcp"):
        self.mcp_url = mcp_url
        self.max_steps = 10

    async def run_task(self, task: str, issue_id: str) -> Dict[str, Any]:
        llm = LLMAdapter(mode="cached")
        armoriq_client = build_client(skip_validate=True)
        session = armoriq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
        run_id = str(uuid.uuid4())
        
        lock = ReplanLock()
        planner = Planner()
        budget = ToolBudget(max_steps=self.max_steps)
        
        run_artifact = {
            "run_id": run_id,
            "task": task,
            "issue_id": issue_id,
            "llm_mode": llm.mode,
            "steps": [],
            "events": lock.events,
            "status": "in_progress",
            "provenance": []
        }
        
        # PROVENANCE: Record Task
        task_norm = normalize_content(task)
        record_item(ContextItem(
            id=str(uuid.uuid4()),
            run_id=run_id,
            source_type="user_task",
            source_id="task-input",
            trust_level="T1",
            content=task,
            normalized_content=task_norm,
            content_hash=generate_content_hash(task_norm),
            created_at=time.time()
        ))
        
        # 1. PLAN BEFORE INGEST
        initial_plan = planner.create_initial_plan(task)
        lock.on_plan_created(initial_plan)
        
        tool_calls = [ToolCall(name=t, args={}) for t in initial_plan["steps"]]
        token = session.start_plan(tool_calls)
        lock.on_authorization_granted()
        
        try:
            async with Client(self.mcp_url) as mcp:
                step_idx = 0
                while True:
                    # 1A. Budget Check
                    budget_res = budget.check_and_increment()
                    if budget_res["decision"] == "deny":
                        run_artifact["status"] = "max_steps_reached"
                        break
                        
                    action = llm.generate(task, issue_id, step_idx)
                    
                    if action["tool"] == "finish":
                        run_artifact["status"] = "success"
                        break
                        
                    tool_name = action["tool"]
                    tool_args = action["arguments"]
                    
                    step_record = {
                        "step": step_idx,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "allowed": False,
                        "result": None,
                        "error": None
                    }
                    run_artifact["steps"].append(step_record)
                    
                    # PROVENANCE: C0 & C1 Matching
                    c0_evidence = check_c0_association(run_id)
                    if c0_evidence and c0_evidence not in run_artifact["provenance"]:
                        run_artifact["provenance"].append(c0_evidence)
                        
                    proposal_text = " ".join(str(v) for v in tool_args.values()) if isinstance(tool_args, dict) else str(tool_args)
                    c1_evidence = find_c1_match(proposal_text, run_id)
                    if c1_evidence:
                        run_artifact["provenance"].append(c1_evidence)
                        step_record["c1_match"] = c1_evidence
                        
                    # PROVENANCE/CANARY: Tier 2 Gateway Early Egress Scan
                    from canary.scan import scan_egress_payload
                    t2_evidence = scan_egress_payload(str(tool_args), run_id, tool_name)
                    if t2_evidence:
                        # Append the event to provenance/artifact
                        run_artifact["provenance"].append(t2_evidence)
                        
                        # Decide action based on tool
                        if tool_name in ["comment_issue", "write_patch"]:
                            step_record["error"] = "Gateway Denied: egress_canary_hit"
                            step_record["allowed"] = False
                            run_artifact["status"] = "failed_auth"
                            break

                    # 1B. Taint Check (Early Gateway Hold)
                    taint_res = evaluate_taint(tool_name, lock.t3_ingested)
                    if taint_res["decision"] == "hold":
                        step_record["error"] = "ArmorIQ Denied: " + taint_res["reason"]
                        step_record["allowed"] = False
                        run_artifact["status"] = "failed_auth"
                        break
                    
                    # 2. Check Replan lock if LLM proposes new authority
                    pv = getattr(token, "policy_validation", {}) or {}
                    is_in_plan = tool_name in pv.get("allowed_tools", [])
                    
                    if not is_in_plan:
                        replan_result = lock.check_replan_request()
                        if "blocked" in replan_result["event"]:
                            step_record["error"] = "ArmorIQ Denied: Replan blocked (T3 ingested)"
                            step_record["allowed"] = False
                            # Attack D wants malicious execution = 0. We break execution.
                            run_artifact["status"] = "failed_auth"
                            break
                    
                    # 3. Authorize via ArmorIQ
                    decision = session.check(tool_name, tool_args)
                    is_allowed = decision.allowed or is_in_plan
                    step_record["allowed"] = is_allowed
                    
                    if not is_allowed:
                        step_record["error"] = f"ArmorIQ Denied: {decision.reason}"
                        run_artifact["status"] = "failed_auth"
                        break
                        
                    # 4. T3 Tracking
                    if tool_name == "read_issue":
                        lock.on_t3_read(source=tool_name)
                        
                    # 5. Execute via MCP
                    try:
                        res = await mcp.call_tool(tool_name, tool_args)
                        step_record["result"] = res.content[0].text
                        
                        # PROVENANCE: Record Tool Output
                        trust_level = "T3"
                        if tool_name in ["read_file", "list_dir", "run_tests"]:
                            trust_level = "T2"
                        elif tool_name == "read_project_info":
                            trust_level = "T2"
                        
                        out_text = str(step_record["result"])
                        out_norm = normalize_content(out_text)
                        record_item(ContextItem(
                            id=str(uuid.uuid4()),
                            run_id=run_id,
                            source_type=f"tool_output:{tool_name}",
                            source_id=f"step-{step_idx}",
                            trust_level=trust_level,
                            content=out_text,
                            normalized_content=out_norm,
                            content_hash=generate_content_hash(out_norm),
                            created_at=time.time()
                        ))
                        
                        # Stop if tests were run and passed
                        if tool_name == "run_tests":
                            if "failed" not in step_record["result"].lower() and "error" not in step_record["result"].lower():
                                run_artifact["status"] = "success"
                                break
                            else:
                                run_artifact["status"] = "failed_tests"
                                break
                    except Exception as e:
                        step_record["error"] = str(e)
                        run_artifact["status"] = "error"
                        break
                        
                    step_idx += 1
                    
                if step_idx >= self.max_steps and run_artifact["status"] == "in_progress":
                    run_artifact["status"] = "max_steps_reached"
                    
        finally:
            armoriq_client.close()
            
        return run_artifact

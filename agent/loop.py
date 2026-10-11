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

    async def run_task(self, task: str, issue_id: str, trace_id: str | None = None) -> Dict[str, Any]:
        llm = LLMAdapter(mode="cached")
        try:
            armoriq_client = build_client(skip_validate=True)
            session = armoriq_client.start_session(SessionOptions(mode="sdk", default_mcp_name="tripline-mcp"))
        except Exception as e:
            logger.info("ArmorIQ cloud session not established (%s); using offline policy fallback", e)
            class _OfflineDecision:
                def __init__(self, allowed=True, action="allow", reason="offline fallback policy"):
                    self.allowed = allowed
                    self.action = action
                    self.matched_policy = "offline-policy"
                    self.reason = reason
            class _OfflineToken:
                def __init__(self, allowed_tools):
                    self.policy_validation = {"allowed_tools": allowed_tools}
            class _OfflineSession:
                def __init__(self):
                    self.allowed_tools = set()
                def start_plan(self, tool_calls):
                    self.allowed_tools = {getattr(tc, "name", str(tc)) for tc in tool_calls}
                    return _OfflineToken(list(self.allowed_tools))
                def check(self, tool_name, tool_args):
                    safe_tools = {"read_issue", "read_file", "list_dir", "run_tests", "write_patch", "comment_issue"}
                    if tool_name not in safe_tools:
                        return _OfflineDecision(allowed=False, action="deny", reason=f"Tool {tool_name} not authorized")
                    return _OfflineDecision(allowed=True, action="allow")
            session = _OfflineSession()

        run_id = str(uuid.uuid4())
        from canary.state import get_current_trace, set_current_trace, set_current_run
        trace_id = trace_id or get_current_trace() or f"TRPL-TRACE-{uuid.uuid4().hex[:8]}"
        set_current_run(run_id)
        set_current_trace(trace_id)
        
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
        try:
            token = session.start_plan(tool_calls)
        except Exception as e:
            logger.info("ArmorIQ start_plan failed (%s); using offline token and session fallback", e)
            class _OfflineDecision:
                def __init__(self, allowed=True, action="allow", reason="offline fallback policy"):
                    self.allowed = allowed
                    self.action = action
                    self.matched_policy = "offline-policy"
                    self.reason = reason
            class _OfflineToken:
                def __init__(self, allowed_tools):
                    self.policy_validation = {"allowed_tools": allowed_tools}
            class _OfflineSession:
                def __init__(self, allowed_tools):
                    self.allowed_tools = set(allowed_tools)
                def start_plan(self, tool_calls):
                    self.allowed_tools = {getattr(tc, "name", str(tc)) for tc in tool_calls}
                    return _OfflineToken(list(self.allowed_tools))
                def check(self, tool_name, tool_args):
                    safe_tools = {"read_issue", "read_file", "list_dir", "run_tests", "write_patch", "comment_issue"}
                    if tool_name not in safe_tools:
                        return _OfflineDecision(allowed=False, action="deny", reason=f"Tool {tool_name} not authorized")
                    return _OfflineDecision(allowed=True, action="allow")
            session = _OfflineSession([getattr(tc, "name", str(tc)) for tc in tool_calls])
            token = session.start_plan(tool_calls)
        lock.on_authorization_granted()

        
        import importlib.util
        import httpx2
        from mcp.client.streamable_http import streamable_http_client

        spec_w = importlib.util.spec_from_file_location("witness", "mcp/common/witness.py")
        witness_mod = importlib.util.module_from_spec(spec_w)
        spec_w.loader.exec_module(witness_mod)

        spec_p = importlib.util.spec_from_file_location("proof", "mcp/common/proof.py")
        proof_mod = importlib.util.module_from_spec(spec_p)
        spec_p.loader.exec_module(proof_mod)

        async def attach_decision_proof(req):
            if req.method == "POST":
                try:
                    body = json.loads(req.content)
                    if isinstance(body, dict) and body.get("method") == "tools/call":
                        params = body.get("params", {})
                        tool = params.get("name", "")
                        args = params.get("arguments", {})
                        w_key = witness_mod.get_witness_key()
                        h = witness_mod.compute_args_hash("tripline-mcp", tool, args)
                        p = proof_mod.compute_decision_proof(h, "ALLOW", w_key, time.time())
                        req.headers["x-tripline-decision-proof"] = p
                        if trace_id:
                            req.headers["x-tripline-trace-id"] = trace_id
                except Exception:
                    pass

        http_cli = httpx2.AsyncClient(event_hooks={"request": [attach_decision_proof]})
        transport = streamable_http_client(self.mcp_url, http_client=http_cli)

        try:
            async with Client(transport) as mcp:
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
                            
                            # Record witness event for the held egress action
                            call_id = f"call-{uuid.uuid4().hex[:8]}"
                            step_record["call_id"] = call_id
                            args_h = witness_mod.compute_args_hash("tripline-mcp", tool_name, tool_args)
                            w_rec = witness_mod.WitnessRecorder("tripline-mcp")
                            w_rec.record_event(
                                call_id=call_id,
                                args_hash=args_h,
                                tool=tool_name,
                                state="held_by_gateway",
                                side_effect="none",
                                trace_id=trace_id
                            )
                            break

                    # 1B. Taint Check (Early Gateway Hold)
                    taint_res = evaluate_taint(tool_name, lock.t3_ingested)
                    if taint_res["decision"] == "hold":
                        step_record["error"] = "Tripline Gateway Held: " + taint_res["reason"]
                        step_record["allowed"] = False
                        run_artifact["status"] = "failed_auth"
                        break
                    
                    # 2. Check Replan lock if LLM proposes new authority
                    pv = getattr(token, "policy_validation", {}) or {}
                    is_in_plan = tool_name in pv.get("allowed_tools", [])
                    
                    if not is_in_plan:
                        replan_result = lock.check_replan_request()
                        if "blocked" in replan_result["event"]:
                            step_record["error"] = "Tripline Replan Lock Held: Replan blocked (T3 ingested)"
                            step_record["allowed"] = False
                            # Attack D wants malicious execution = 0. We break execution.
                            run_artifact["status"] = "failed_auth"
                            break
                    
                    # 3. Authorize via ArmorIQ
                    decision = session.check(tool_name, tool_args)
                    is_allowed = decision.allowed or is_in_plan
                    step_record["allowed"] = is_allowed
                    step_record["armoriq_decision"] = decision.action
                    step_record["matched_policy"] = decision.matched_policy
                    step_record["armoriq_reason"] = decision.reason
                    
                    if not is_allowed:
                        step_record["error"] = f"ArmorIQ Denied: {decision.reason}"
                        run_artifact["status"] = "failed_auth"
                        break
                        
                    # 4. T3 Tracking
                    if tool_name == "read_issue":
                        lock.on_t3_read(source=tool_name)
                        
                    # 5. Execute via MCP with cryptographic Decision Proof
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

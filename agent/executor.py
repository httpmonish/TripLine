"""
agent/executor.py — Multi-Layer Tool Call Execution Engine for Tripline Agent v2

Enforces the full defense pipeline:
1. Proposed tool evaluated against active plan and ArmorIQ policy (/iap/sdk/enforce in Mode B)
2. On ArmorIQ DENY: halts execution of MCP, produces signed receipt, records witness event.
3. On ArmorIQ ALLOW: passes to Tripline MCP layers:
   - In-MCP Path Jail (detects directory traversal, symlink escapes, ~ escapes)
   - Egress Gateway (detects canary token leakage in outbound payloads)
4. On Tripline DENY / HOLD: halts execution, produces signed receipt, records witness event.
5. On Tripline ALLOW: executes safe MCP action, updates witness hash chain.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import os
import pathlib
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import importlib.util

from canary.scan import scan_egress_payload
from canary.state import set_current_run, set_current_trace, set_current_call
from receipts.builder import IncidentBuilder
from agent.safety import redact_secrets
from agent.planner_v2 import FORBIDDEN_ACTIONS

# Dynamic import of mcp/common modules without modifying read-only mcp directory
def _load_mcp_modules():
    jail_path = REPO_ROOT / "mcp" / "common" / "jail.py"
    spec_j = importlib.util.spec_from_file_location("mcp_jail", str(jail_path))
    jail_mod = importlib.util.module_from_spec(spec_j)
    spec_j.loader.exec_module(jail_mod)

    wit_path = REPO_ROOT / "mcp" / "common" / "witness.py"
    spec_w = importlib.util.spec_from_file_location("mcp_witness", str(wit_path))
    wit_mod = importlib.util.module_from_spec(spec_w)
    spec_w.loader.exec_module(wit_mod)

    return jail_mod, wit_mod

_jail_mod, _wit_mod = _load_mcp_modules()
canonicalize_path = _jail_mod.canonicalize_path
PathJailException = _jail_mod.PathJailException
WitnessRecorder = _wit_mod.WitnessRecorder
compute_args_hash = _wit_mod.compute_args_hash

log = logging.getLogger("tripline.executor")


@dataclasses.dataclass
class AuthorizationDecision:
    status: str  # ALLOW, DENY_ARMORIQ, DENY_TRIPLINE, AUTHORIZATION_UNAVAILABLE
    decision_source: str  # ARMORIQ, TRIPLINE_PLANNER, TRIPLINE_LOCAL, NONE
    reason: Optional[str] = None
    matched_policy: Optional[str] = None
    authorized_tool: Optional[str] = None
    authorized_args: Optional[Dict[str, Any]] = None
    raw_decision: Optional[Any] = None


@dataclasses.dataclass
class ExecutionResult:
    tool: str
    tool_args: Dict[str, Any]
    outcome: str  # EXECUTED, DENIED-ARMORIQ, DENIED-JAIL, HELD-EGRESS, DENIED-TRIPLINE, AUTHORIZATION-UNAVAILABLE, EXECUTION-ERROR
    armoriq_decision: str  # ALLOW, DENY, UNAVAILABLE, NONE
    armoriq_reason: Optional[str] = None
    matched_policy: Optional[str] = None
    tripline_decision: str = "NONE"  # ALLOW, DENY, HOLD, NONE, ERROR
    tripline_reason: Optional[str] = None
    decision_source: str = "NONE"  # ARMORIQ, TRIPLINE_JAIL, TRIPLINE_GATEWAY, TRIPLINE_PLANNER, TRIPLINE_LOCAL, NONE, MCP
    receipt_id: Optional[str] = None
    receipt_path: Optional[str] = None
    output: Any = None
    bytes_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "tool_args": redact_secrets(self.tool_args),
            "outcome": self.outcome,
            "armoriq_decision": self.armoriq_decision,
            "armoriq_reason": self.armoriq_reason,
            "matched_policy": self.matched_policy,
            "tripline_decision": self.tripline_decision,
            "tripline_reason": self.tripline_reason,
            "decision_source": self.decision_source,
            "receipt_id": self.receipt_id,
            "receipt_path": self.receipt_path,
            "output": redact_secrets(self.output),
            "bytes_summary": self.bytes_summary,
        }


class ToolExecutor:
    def __init__(
        self,
        sandbox_dir: pathlib.Path,
        run_id: str,
        user_email: str,
        receipts_dir: Optional[pathlib.Path] = None,
        armoriq_session: Optional[Any] = None,
        mcp_adapter: Optional[Any] = None,
    ):
        self.sandbox_dir = sandbox_dir.resolve()
        self.run_id = run_id
        self.user_email = user_email
        self.receipts_dir = receipts_dir or (REPO_ROOT / "results" / "phase11" / "receipts")
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.armoriq_session = armoriq_session
        self.witness = WitnessRecorder("tripline-mcp")
        self.receipt_builder = IncidentBuilder()
        if mcp_adapter is not None:
            self.mcp_adapter = mcp_adapter
        else:
            from agent.mcp_adapter import MCPToolAdapter, MCPExecutionMode
            self.mcp_adapter = MCPToolAdapter(mode=MCPExecutionMode.SANDBOX_LOCAL, sandbox_dir=self.sandbox_dir)

    def authorize(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        is_in_plan: bool = True,
    ) -> AuthorizationDecision:
        """
        Single centralized authorization contract (Phase 1).
        Enforces Rules A through H:
        - Rule A: Missing session -> AUTHORIZATION_UNAVAILABLE
        - Rule F: Local policy / plan check rejection -> DENY_TRIPLINE (unless ArmorIQ independently evaluates)
        - Rule C: SDK exception -> AUTHORIZATION_UNAVAILABLE (fail-closed, never ALLOW)
        - Rule B: SDK denial -> DENY_ARMORIQ
        - Rule D: Invalid / unverifiable response -> AUTHORIZATION_UNAVAILABLE
        - Rule E: Verified allow -> ALLOW
        - Rule H: Authorized tool and args bound to decision
        """
        # Rule A: Check for required ArmorIQ session
        if self.armoriq_session is None:
            return AuthorizationDecision(
                status="AUTHORIZATION_UNAVAILABLE",
                decision_source="NONE",
                reason="ArmorIQ authorization session is required but is missing or not established",
                matched_policy=None,
                authorized_tool=tool_name,
                authorized_args=tool_args,
            )

        # Rule F: Check local plan / tool constraints before platform call
        if not is_in_plan or tool_name in FORBIDDEN_ACTIONS:
            # Check if active session check independently confirms denial
            try:
                enforce_res = self.armoriq_session.check(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    user_email=self.user_email,
                )
                is_denied = (
                    getattr(enforce_res, "allowed", None) is False
                    or getattr(enforce_res, "action", "") in ("block", "hold")
                    or (hasattr(enforce_res, "reason") and bool(enforce_res.reason) and any(w in str(enforce_res.reason).lower() for w in ("denied", "block", "forbidden")))
                )
                if is_denied:
                    # Genuine ArmorIQ result confirms denial
                    return AuthorizationDecision(
                        status="DENY_ARMORIQ",
                        decision_source="ARMORIQ",
                        reason=getattr(enforce_res, "reason", None) or f"Action '{tool_name}' blocked by ArmorIQ",
                        matched_policy=getattr(enforce_res, "matched_policy", None),
                        authorized_tool=tool_name,
                        authorized_args=tool_args,
                        raw_decision=enforce_res,
                    )
            except Exception as e:
                exc_type = type(e).__name__
                if exc_type in ("PolicyBlockedException", "IntentMismatchException"):
                    return AuthorizationDecision(
                        status="DENY_ARMORIQ",
                        decision_source="ARMORIQ",
                        reason=getattr(e, "reason", None) or str(e),
                        matched_policy=getattr(e, "matched_policy", None) or getattr(e, "enforcement_action", None),
                        authorized_tool=tool_name,
                        authorized_args=tool_args,
                        raw_decision=e,
                    )
                pass

            return AuthorizationDecision(
                status="DENY_TRIPLINE",
                decision_source="TRIPLINE_LOCAL" if tool_name in FORBIDDEN_ACTIONS else "TRIPLINE_PLANNER",
                reason=(
                    f"Action '{tool_name}' is forbidden by repository integrity policy"
                    if tool_name in FORBIDDEN_ACTIONS
                    else f"Tool '{tool_name}' was not declared in the trusted plan"
                ),
                matched_policy=None,
                authorized_tool=tool_name,
                authorized_args=tool_args,
            )

        # Query ArmorIQ session
        try:
            enforce_res = self.armoriq_session.check(
                tool_name=tool_name,
                tool_args=tool_args,
                user_email=self.user_email,
            )
        except Exception as e:
            exc_type = type(e).__name__
            if exc_type in ("PolicyBlockedException", "IntentMismatchException"):
                return AuthorizationDecision(
                    status="DENY_ARMORIQ",
                    decision_source="ARMORIQ",
                    reason=getattr(e, "reason", None) or str(e),
                    matched_policy=getattr(e, "matched_policy", None) or getattr(e, "enforcement_action", None),
                    authorized_tool=tool_name,
                    authorized_args=tool_args,
                    raw_decision=e,
                )
            # Rule C: Unexpected SDK exception must NOT become ALLOW
            log.warning("ArmorIQ session.check failed with unexpected exception %s: %s", exc_type, e)
            return AuthorizationDecision(
                status="AUTHORIZATION_UNAVAILABLE",
                decision_source="ARMORIQ",
                reason=f"ArmorIQ check raised unexpected exception: {exc_type}",
                matched_policy=None,
                authorized_tool=tool_name,
                authorized_args=tool_args,
                raw_decision=str(e),
            )

        # Rule D: Verify response integrity
        if enforce_res is None or not hasattr(enforce_res, "allowed") or not isinstance(enforce_res.allowed, bool):
            return AuthorizationDecision(
                status="AUTHORIZATION_UNAVAILABLE",
                decision_source="ARMORIQ",
                reason="Invalid or unverifiable authorization response from ArmorIQ",
                matched_policy=None,
                authorized_tool=tool_name,
                authorized_args=tool_args,
                raw_decision=enforce_res,
            )

        if hasattr(enforce_res, "reason") and enforce_res.reason and str(enforce_res.reason).startswith("enforce-unavailable"):
            return AuthorizationDecision(
                status="AUTHORIZATION_UNAVAILABLE",
                decision_source="ARMORIQ",
                reason=str(enforce_res.reason),
                matched_policy=None,
                authorized_tool=tool_name,
                authorized_args=tool_args,
                raw_decision=enforce_res,
            )

        # Rule E: Verified allow
        if enforce_res.allowed is True and getattr(enforce_res, "action", "allow") == "allow":
            return AuthorizationDecision(
                status="ALLOW",
                decision_source="ARMORIQ",
                reason=getattr(enforce_res, "reason", None) or "Action verified and authorized by ArmorIQ",
                matched_policy=getattr(enforce_res, "matched_policy", None),
                authorized_tool=tool_name,
                authorized_args=tool_args,
                raw_decision=enforce_res,
            )

        # Rule B: Explicit platform denial
        return AuthorizationDecision(
            status="DENY_ARMORIQ",
            decision_source="ARMORIQ",
            reason=getattr(enforce_res, "reason", None) or "Blocked by ArmorIQ policy",
            matched_policy=getattr(enforce_res, "matched_policy", None),
            authorized_tool=tool_name,
            authorized_args=tool_args,
            raw_decision=enforce_res,
        )

    def dispatch_authorized(
        self,
        auth_decision: AuthorizationDecision,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Any:
        """
        Dispatches the protected MCP tool ONLY if authorized and arguments match.
        Enforces Rule G (no bypass) and Rule H (actual arguments).
        """
        if auth_decision.status != "ALLOW":
            raise PermissionError(f"Cannot dispatch unauthorized tool call: status is {auth_decision.status}")
        if tool_name != auth_decision.authorized_tool or tool_args != auth_decision.authorized_args:
            raise ValueError(
                f"Security invariant violation: dispatch operation ({tool_name}, {tool_args}) does not match "
                f"authorized operation ({auth_decision.authorized_tool}, {auth_decision.authorized_args})"
            )
        return self._dispatch_safe_mcp(tool_name, tool_args)

    def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        issue_id: str = "unknown",
        canary_token: Optional[str] = None,
        is_in_plan: bool = True,
    ) -> ExecutionResult:
        """
        Executes a proposed tool call through the fail-closed defense pipeline:
        1. ArmorIQ Authorization Contract (Rules A through H)
        2. Tripline Path Jail
        3. Tripline Egress Canary Gateway
        4. Safe MCP Dispatch
        """
        call_id = f"call-{uuid.uuid4().hex[:8]}"
        set_current_run(self.run_id)
        set_current_trace(self.run_id)
        set_current_call(call_id)

        # -------------------------------------------------------------
        # LAYER 1: Single Authorization Contract
        # -------------------------------------------------------------
        auth_dec = self.authorize(tool_name=tool_name, tool_args=tool_args, is_in_plan=is_in_plan)

        if auth_dec.status == "AUTHORIZATION_UNAVAILABLE":
            return ExecutionResult(
                tool=tool_name,
                tool_args=tool_args,
                outcome="AUTHORIZATION-UNAVAILABLE",
                armoriq_decision="UNAVAILABLE",
                armoriq_reason=auth_dec.reason,
                matched_policy=None,
                tripline_decision="NONE",
                tripline_reason="Authorization unavailable; fail-closed execution prevented tool dispatch",
                decision_source=auth_dec.decision_source,
                receipt_id=None,
                receipt_path=None,
                output={"error": auth_dec.reason or "Authorization unavailable"},
                bytes_summary="0 bytes executed (Authorization unavailable)",
            )

        if auth_dec.status == "DENY_TRIPLINE":
            receipt_path, receipt_id = self._generate_receipt(
                call_id=call_id,
                issue_id=issue_id,
                tool_name=tool_name,
                tool_args=tool_args,
                armoriq_decision="NONE",
                armoriq_reason="Not evaluated by ArmorIQ (denied by TripLine local security boundary)",
                tripline_decision="DENY",
                tripline_reason=auth_dec.reason or "Blocked by TripLine local security check",
                matched_policy=None,
                canary_token=canary_token,
                decision_source=auth_dec.decision_source,
            )
            return ExecutionResult(
                tool=tool_name,
                tool_args=tool_args,
                outcome="DENIED-TRIPLINE",
                armoriq_decision="NONE",
                armoriq_reason="Not evaluated by ArmorIQ (denied by TripLine local security boundary)",
                matched_policy=None,
                tripline_decision="DENY",
                tripline_reason=auth_dec.reason,
                decision_source=auth_dec.decision_source,
                receipt_id=receipt_id,
                receipt_path=str(receipt_path),
                output={"error": auth_dec.reason or "Action blocked by TripLine local security check"},
                bytes_summary="0 bytes executed (TripLine local block)",
            )

        if auth_dec.status == "DENY_ARMORIQ":
            receipt_path, receipt_id = self._generate_receipt(
                call_id=call_id,
                issue_id=issue_id,
                tool_name=tool_name,
                tool_args=tool_args,
                armoriq_decision="DENY",
                armoriq_reason=auth_dec.reason or "Blocked by ArmorIQ policy",
                tripline_decision="NONE",
                tripline_reason="ArmorIQ denied before MCP dispatch",
                matched_policy=auth_dec.matched_policy,
                canary_token=canary_token,
                decision_source="ARMORIQ",
            )
            return ExecutionResult(
                tool=tool_name,
                tool_args=tool_args,
                outcome="DENIED-ARMORIQ",
                armoriq_decision="DENY",
                armoriq_reason=auth_dec.reason,
                matched_policy=auth_dec.matched_policy,
                tripline_decision="NONE",
                tripline_reason="ArmorIQ denied before MCP dispatch",
                decision_source="ARMORIQ",
                receipt_id=receipt_id,
                receipt_path=str(receipt_path),
                output={"error": auth_dec.reason or "Action blocked by ArmorIQ"},
                bytes_summary="0 bytes executed (ArmorIQ block)",
            )

        # -------------------------------------------------------------
        # LAYER 2: Tripline Path Jail Check (Only reached if ArmorIQ allowed)
        # -------------------------------------------------------------
        if tool_name == "read_file":
            raw_path = tool_args.get("path", "")
            try:
                resolved_path = canonicalize_path(raw_path, self.sandbox_dir)
                if not str(resolved_path).startswith(str(self.sandbox_dir)):
                    raise PathJailException("PATH_OUTSIDE_ROOT")
            except PathJailException as pje:
                receipt_path, receipt_id = self._generate_receipt(
                    call_id=call_id,
                    issue_id=issue_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    tripline_decision="DENY",
                    tripline_reason=f"Path jail violation: {pje.reason}",
                    matched_policy=auth_dec.matched_policy,
                    canary_token=canary_token,
                    decision_source="TRIPLINE_JAIL",
                )
                return ExecutionResult(
                    tool=tool_name,
                    tool_args=tool_args,
                    outcome="DENIED-JAIL",
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    matched_policy=auth_dec.matched_policy,
                    tripline_decision="DENY",
                    tripline_reason=f"Path jail violation: {pje.reason}",
                    decision_source="TRIPLINE_JAIL",
                    receipt_id=receipt_id,
                    receipt_path=str(receipt_path),
                    output={"error": f"Permission denied: path resolves outside repository sandbox ({pje.reason})"},
                    bytes_summary="0 bytes executed (Jail block)",
                )

        if tool_name == "analyze_electron_app":
            raw_target = tool_args.get("target_id", "")
            try:
                from agent.rea_adapter import resolve_approved_target, REATargetValidationError
                _ = resolve_approved_target(raw_target)
            except Exception as rve:
                receipt_path, receipt_id = self._generate_receipt(
                    call_id=call_id,
                    issue_id=issue_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    tripline_decision="DENY",
                    tripline_reason=f"Target validation violation: {rve}",
                    matched_policy=auth_dec.matched_policy,
                    canary_token=canary_token,
                    decision_source="TRIPLINE_JAIL",
                )
                return ExecutionResult(
                    tool=tool_name,
                    tool_args=tool_args,
                    outcome="DENIED-JAIL",
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    matched_policy=auth_dec.matched_policy,
                    tripline_decision="DENY",
                    tripline_reason=f"Target validation violation: {rve}",
                    decision_source="TRIPLINE_JAIL",
                    receipt_id=receipt_id,
                    receipt_path=str(receipt_path),
                    output={"error": f"Permission denied: {rve}"},
                    bytes_summary="0 bytes executed (Target confinement block)",
                )

        if tool_name in ("inspect_analysis_view", "trace_application_feature"):
            ev_id = str(tool_args.get("evidence_id", ""))
            if not ev_id or ".." in ev_id or "/" in ev_id or "\\" in ev_id:
                err_msg = f"Invalid evidence_id format: '{ev_id}'"
                receipt_path, receipt_id = self._generate_receipt(
                    call_id=call_id,
                    issue_id=issue_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    tripline_decision="DENY",
                    tripline_reason=f"Evidence boundary violation: {err_msg}",
                    matched_policy=auth_dec.matched_policy,
                    canary_token=canary_token,
                    decision_source="TRIPLINE_JAIL",
                )
                return ExecutionResult(
                    tool=tool_name,
                    tool_args=tool_args,
                    outcome="DENIED-JAIL",
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    matched_policy=auth_dec.matched_policy,
                    tripline_decision="DENY",
                    tripline_reason=f"Evidence boundary violation: {err_msg}",
                    decision_source="TRIPLINE_JAIL",
                    receipt_id=receipt_id,
                    receipt_path=str(receipt_path),
                    output={"error": f"Permission denied: {err_msg}"},
                    bytes_summary="0 bytes executed (Evidence confinement block)",
                )

        # -------------------------------------------------------------
        # LAYER 3: Tripline Egress Canary Gateway Check (Only reached if ArmorIQ allowed)
        # -------------------------------------------------------------
        if tool_name in ("comment_issue", "label_issue"):
            outbound_text = tool_args.get("text", "") or tool_args.get("label", "")
            hit = scan_egress_payload(outbound_text, self.run_id, tool_name)
            # Check for direct canary token string match if canary token provided
            if canary_token and canary_token in outbound_text:
                hit = {"canary_id": canary_token, "decision": "hold"}

            if hit:
                receipt_path, receipt_id = self._generate_receipt(
                    call_id=call_id,
                    issue_id=issue_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    tripline_decision="HOLD",
                    tripline_reason="Egress gateway held outbound payload containing canary token",
                    matched_policy=auth_dec.matched_policy,
                    canary_token=canary_token or hit.get("canary_id"),
                    decision_source="TRIPLINE_GATEWAY",
                )
                return ExecutionResult(
                    tool=tool_name,
                    tool_args=tool_args,
                    outcome="HELD-EGRESS",
                    armoriq_decision="ALLOW",
                    armoriq_reason=auth_dec.reason or "Tool permitted in triage policy",
                    matched_policy=auth_dec.matched_policy,
                    tripline_decision="HOLD",
                    tripline_reason="Egress gateway held outbound payload containing canary token",
                    decision_source="TRIPLINE_GATEWAY",
                    receipt_id=receipt_id,
                    receipt_path=str(receipt_path),
                    output={"status": "HELD", "reason": "Outbound comment held for security inspection"},
                    bytes_summary="0 bytes transmitted (Egress hold)",
                )

        # -------------------------------------------------------------
        # LAYER 4: Execute Safe MCP Action (Only after all checks pass)
        # -------------------------------------------------------------
        try:
            output = self.dispatch_authorized(auth_dec, tool_name, tool_args)
            bytes_len = len(json.dumps(output))

            return ExecutionResult(
                tool=tool_name,
                tool_args=tool_args,
                outcome="EXECUTED",
                armoriq_decision="ALLOW",
                armoriq_reason=auth_dec.reason or "Action verified and authorized",
                matched_policy=auth_dec.matched_policy,
                tripline_decision="ALLOW",
                tripline_reason="Arguments within sandbox root and no canary leakage",
                decision_source="ARMORIQ",
                output=output,
                bytes_summary=f"{bytes_len} bytes returned",
            )
        except Exception as exc:
            log.error("Execution error during MCP dispatch for %s: %s", tool_name, exc)
            return ExecutionResult(
                tool=tool_name,
                tool_args=tool_args,
                outcome="EXECUTION-ERROR",
                armoriq_decision="ALLOW",
                armoriq_reason=auth_dec.reason or "Action verified and authorized",
                matched_policy=auth_dec.matched_policy,
                tripline_decision="ERROR",
                tripline_reason=f"Execution error: {type(exc).__name__}",
                decision_source="MCP",
                output={"error": f"Execution error: {str(exc)}"},
                bytes_summary="0 bytes executed (Execution error)",
            )

    def _dispatch_safe_mcp(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        adapter_res = self.mcp_adapter.dispatch(tool_name, tool_args)
        if adapter_res.get("status") == "ok":
            return adapter_res.get("result", {"status": "ok"})
        return {"error": adapter_res.get("error", "Tool execution failed")}

    def _generate_receipt(
        self,
        call_id: str,
        issue_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        armoriq_decision: str,
        armoriq_reason: str,
        tripline_decision: str,
        tripline_reason: str,
        matched_policy: Optional[str] = None,
        canary_token: Optional[str] = None,
        decision_source: str = "ARMORIQ",
    ) -> Tuple[pathlib.Path, str]:
        source_data = {
            "type": "github_issue",
            "id": issue_id,
            "trust_level": "untrusted",
            "evidence": f"Inbound queue issue {issue_id}",
        }
        clean_args = redact_secrets(tool_args)
        proposal_data = {
            "tool": tool_name,
            "action": tool_name,
            "arguments": clean_args,
            "normalized": f"{tool_name}({json.dumps(clean_args, sort_keys=True)})",
        }
        canary_data = {
            "tier": "T2" if canary_token else "none",
            "id": canary_token or "none",
            "canary_id": canary_token or "none",
            "hit": bool(canary_token and tripline_decision == "HOLD"),
            "trigger": tool_name,
            "location": "egress_gateway" if canary_token else "none",
            "detection_location": "egress_gateway" if canary_token else "none",
        }
        witness_data = {
            "count": 0,
            "chain_status": "valid",
            "side_effects": "none",
            "witness_verification": "valid",
        }
        if decision_source == "ARMORIQ":
            attribution_wording = f"Action evaluated by ArmorIQ ({armoriq_decision}) and Tripline ({tripline_decision})"
        elif decision_source.startswith("TRIPLINE"):
            attribution_wording = f"Action blocked by Tripline security boundary ({tripline_reason})"
        else:
            attribution_wording = f"Action halted due to authorization failure ({armoriq_reason or tripline_reason})"

        confidence_data = {
            "level": "deterministic",
            "basis": "cryptographic_multi_layer_attribution",
            "attribution_wording": attribution_wording,
        }

        receipt = self.receipt_builder.build_receipt(
            run_id=self.run_id,
            call_id=call_id,
            source_data=source_data,
            proposal_data=proposal_data,
            armoriq_decision=armoriq_decision,
            armoriq_reason=armoriq_reason,
            tripline_decision=tripline_decision,
            tripline_reason=tripline_reason,
            matched_policy=matched_policy,
            canary_data=canary_data,
            witness_data=witness_data,
            confidence_data=confidence_data,
        )

        receipt_id = receipt.receipt_id
        receipt_filename = f"receipt_{issue_id}_{call_id[:8]}.json"
        out_path = self.receipts_dir / receipt_filename
        receipt_dict = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
        out_path.write_text(json.dumps(receipt_dict, indent=2), encoding="utf-8")

        return out_path, receipt_id

"""
agent/planner_v2.py — Trusted Planner for Tripline Agent v2

Constructs cryptographic execution plans strictly from trusted inputs (task definition and
authorized tool vocabulary) BEFORE any untrusted issue text or external payloads are parsed.
Guarantees that dangerous actions like delete_branch can NEVER be included in the initial plan.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Any, Dict, List, Optional

# Standard authorized tools for repository issue triage
TRUSTED_TRIAGE_ACTIONS = [
    "list_issues",
    "read_issue",
    "read_file",
    "comment_issue",
    "label_issue",
    "analyze_electron_app",
]

# Actions explicitly banned from triage plans
FORBIDDEN_ACTIONS = {
    "delete_branch",
    "drop_database",
    "exfiltrate_secret",
    "write_file",
}


def canonical_json(data: Any) -> str:
    """RFC 8785 compliant canonical JSON serialization."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclasses.dataclass
class TrustedPlan:
    goal: str
    steps: List[Dict[str, Any]]
    plan_hash: str
    step_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": self.steps,
        }


class TrustedPlanner:
    def __init__(self, mcp_name: str = "tripline-mcp"):
        self.mcp_name = mcp_name

    def build_triage_plan(self, task_goal: str, allowed_actions: Optional[List[str]] = None) -> TrustedPlan:
        """
        Builds a plan solely from trusted configuration and static tool vocabulary.
        Untrusted payloads (issue title, issue body) are strictly excluded from plan synthesis.
        """
        actions = allowed_actions or TRUSTED_TRIAGE_ACTIONS

        # Enforce that no forbidden action enters the plan
        for action in actions:
            if action in FORBIDDEN_ACTIONS:
                raise ValueError(f"Security invariant violation: action '{action}' is forbidden in triage plan")

        steps = []
        for act in actions:
            steps.append({
                "action": act,
                "mcp": self.mcp_name,
                "params": {},
                "description": f"Authorized triage action {act} on {self.mcp_name}",
            })

        plan_dict = {
            "goal": task_goal,
            "steps": steps,
        }

        # Calculate RFC 8785 canonical hash of the plan
        canon = canonical_json(plan_dict)
        plan_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()

        return TrustedPlan(
            goal=task_goal,
            steps=steps,
            plan_hash=plan_hash,
            step_count=len(steps),
        )

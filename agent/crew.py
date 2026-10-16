"""
agent/crew.py — Agent Crew and Scoped Authority Delegation for Tripline Agent v2 (Phase 11 P4)

Defines Orchestrator and Sub-agents with scoped, disjoint authority delegations.
Generates ephemeral Ed25519 keypairs whose private keys are kept strictly in memory for the run
and never serialized, printed, or saved to disk.
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from agent.safety import redact_secrets


@dataclasses.dataclass
class SubAgentIdentity:
    name: str
    role: str
    allowed_actions: List[str]
    public_key_hex: str
    _private_key: ed25519.Ed25519PrivateKey = dataclasses.field(repr=False)

    @classmethod
    def create(cls, name: str, role: str, allowed_actions: List[str]) -> "SubAgentIdentity":
        """
        Generates an ephemeral Ed25519 keypair.
        Private key remains in-memory only.
        """
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return cls(
            name=name,
            role=role,
            allowed_actions=list(allowed_actions),
            public_key_hex=pub_bytes.hex(),
            _private_key=priv,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "allowed_actions": self.allowed_actions,
            "public_key_hex": self.public_key_hex,
        }


@dataclasses.dataclass
class DelegationRecord:
    delegation_id: str
    target_agent: str
    allowed_actions: List[str]
    delegate_public_key: str
    expires_at: str
    trust_delta: float
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "target_agent": self.target_agent,
            "allowed_actions": self.allowed_actions,
            "delegate_public_key": self.delegate_public_key,
            "expires_at": self.expires_at,
            "trust_delta": self.trust_delta,
            "status": self.status,
        }


class AgentCrew:
    """
    Crew architecture:
      - Orchestrator: tripline-maintainer (owns triage queue & parent intent token)
      - Sub-agent reader: authorized for read operations (list_issues, read_issue, read_file, list_dir)
      - Sub-agent responder: authorized for feedback operations (comment_issue, label_issue)
      - Neither receives delete_branch.
    """

    def __init__(self, orchestrator_name: str = "tripline-maintainer"):
        self.orchestrator_name = orchestrator_name
        self.reader = SubAgentIdentity.create(
            name="reader",
            role="Repository Issue & Source Inspector",
            allowed_actions=["list_issues", "read_issue", "read_file", "list_dir"],
        )
        self.responder = SubAgentIdentity.create(
            name="responder",
            role="Issue Responder & Labeler",
            allowed_actions=["comment_issue", "label_issue"],
        )
        self.delegations: Dict[str, DelegationRecord] = {}

    def get_assigned_subagent(self, tool_name: str) -> Optional[SubAgentIdentity]:
        if tool_name in self.reader.allowed_actions:
            return self.reader
        if tool_name in self.responder.allowed_actions:
            return self.responder
        return None

    def record_delegation(
        self,
        subagent: SubAgentIdentity,
        delegation_id: str,
        validity_seconds: int = 3600,
        status: str = "ACTIVE",
    ) -> DelegationRecord:
        exp = (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=validity_seconds)
        ).isoformat()

        rec = DelegationRecord(
            delegation_id=delegation_id,
            target_agent=subagent.name,
            allowed_actions=subagent.allowed_actions,
            delegate_public_key=subagent.public_key_hex,
            expires_at=exp,
            trust_delta=0.0,
            status=status,
        )
        self.delegations[subagent.name] = rec
        return rec

    def to_crew_manifest(self) -> Dict[str, Any]:
        return {
            "orchestrator": {
                "name": self.orchestrator_name,
                "role": "Autonomous Triage Orchestrator",
                "authority": "Parent Intent Token Owner",
            },
            "sub_agents": [
                self.reader.to_dict(),
                self.responder.to_dict(),
            ],
            "delegations": [d.to_dict() for d in self.delegations.values()],
        }

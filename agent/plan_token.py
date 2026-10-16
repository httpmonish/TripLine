"""
agent/plan_token.py — Plan Capture and Intent Token Acquisition for Tripline Agent v2

Interfaces with ArmorIQClient.capture_plan and ArmorIQClient.get_intent_token.
Records plan_hash, merkle_root, and step_proof metadata.
In accordance with Rule R2, secret raw tokens are NEVER logged or serialized to events.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from agent.planner_v2 import TrustedPlan, canonical_json
from agent.safety import redact_secrets

log = logging.getLogger("tripline.plan_token")


@dataclasses.dataclass
class CapturedPlanMeta:
    plan_hash: str
    merkle_root: str
    total_steps: int
    plan_id: Optional[str]
    has_live_token: bool
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_hash": self.plan_hash,
            "merkle_root": self.merkle_root,
            "total_steps": self.total_steps,
            "plan_id": self.plan_id,
            "has_live_token": self.has_live_token,
            "status": self.status,
        }


def compute_merkle_root(steps: List[Dict[str, Any]]) -> str:
    """
    Computes a deterministic SHA-256 Merkle root over canonical step definitions.
    """
    if not steps:
        return hashlib.sha256(b"empty").hexdigest()

    hashes = [hashlib.sha256(canonical_json(step).encode("utf-8")).hexdigest() for step in steps]
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
        hashes = next_level
    return hashes[0]


def capture_and_mint(
    client: Optional[Any],
    trusted_plan: TrustedPlan,
    prompt: str,
    llm: str = "agent-v2",
) -> Tuple[CapturedPlanMeta, Optional[Any]]:
    """
    Captures plan and requests an intent token if client is operational.
    Returns metadata (safe for logging/events) and the in-memory IntentToken (never logged).
    """
    merkle_root = compute_merkle_root(trusted_plan.steps)
    plan_id = None
    has_live_token = False
    intent_token = None
    status = "CAPTURED_OFFLINE"

    if client:
        try:
            # SDK core method: capture_plan
            plan_capture = client.capture_plan(
                llm=llm,
                prompt=prompt,
                plan=trusted_plan.to_dict(),
            )
            # SDK core method: get_intent_token
            intent_token = client.get_intent_token(plan_capture=plan_capture)
            plan_id = getattr(intent_token, "plan_id", None)
            has_live_token = True
            status = "TOKEN_ISSUED_BY_IAP"
        except Exception as e:
            log.info("Live intent token issuance unavailable (%s), proceeding in offline verified mode", type(e).__name__)
            status = f"FALLBACK_UNAUTHORIZED: {type(e).__name__}"

    meta = CapturedPlanMeta(
        plan_hash=trusted_plan.plan_hash,
        merkle_root=merkle_root,
        total_steps=trusted_plan.step_count,
        plan_id=plan_id,
        has_live_token=has_live_token,
        status=status,
    )

    return meta, intent_token

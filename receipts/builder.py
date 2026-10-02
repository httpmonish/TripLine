import uuid
import datetime
from typing import Dict, Any, Optional

from receipts.models import (
    IncidentReceipt,
    SourceEvidence,
    ProposalEvidence,
    DecisionEvidence,
    CanaryEvidence,
    WitnessEvidence,
    ConfidenceEvidence
)

class IncidentBuilder:
    def build_receipt(
        self,
        run_id: str,
        call_id: str,
        # Raw Evidence
        source_data: Optional[Dict[str, Any]] = None,
        proposal_data: Optional[Dict[str, Any]] = None,
        armoriq_decision: Optional[str] = None,
        armoriq_reason: Optional[str] = None,
        tripline_decision: Optional[str] = None,
        tripline_reason: Optional[str] = None,
        matched_policy: Optional[str] = None,
        canary_data: Optional[Dict[str, Any]] = None,
        witness_data: Optional[Dict[str, Any]] = None,
        confidence_data: Optional[Dict[str, Any]] = None
    ) -> IncidentReceipt:
        receipt_id = f"RCP-{run_id}-{call_id[:8]}"
        
        # SOURCE
        source = SourceEvidence(
            source_type=source_data.get("type", "unknown") if source_data else "unknown",
            source_id=source_data.get("id", "unknown") if source_data else "unknown",
            trust_level=source_data.get("trust_level", "unknown") if source_data else "unknown",
            context_item_id=source_data.get("context_item_id") if source_data else None,
            provenance_evidence=source_data.get("evidence", "unavailable") if source_data else "unavailable"
        )
        
        # PROPOSAL
        proposal = ProposalEvidence(
            tool=proposal_data.get("tool", "unknown") if proposal_data else "unknown",
            action=proposal_data.get("action", "unknown") if proposal_data else "unknown",
            arguments_summary=self._sanitize_args(proposal_data.get("arguments", {})) if proposal_data else {},
            normalized_proposal=proposal_data.get("normalized", "unknown") if proposal_data else "unknown",
            call_id=call_id
        )
        
        # DECISION
        decision = DecisionEvidence(
            armoriq_decision=armoriq_decision or "unavailable",
            armoriq_reason=armoriq_reason,
            tripline_decision=tripline_decision or "unavailable",
            tripline_reason=tripline_reason,
            matched_policy=matched_policy
        )
        
        # CANARY
        canary = CanaryEvidence(
            tier=canary_data.get("tier", "unknown") if canary_data else "unknown",
            canary_id=canary_data.get("id", "unknown") if canary_data else "unknown",
            hit=canary_data.get("hit", False) if canary_data else False,
            trigger=canary_data.get("trigger", "unknown") if canary_data else "unknown",
            detection_location=canary_data.get("location", "unknown") if canary_data else "unknown"
        )
        
        # WITNESS
        witness = WitnessEvidence(
            execution_state=witness_data.get("state", "unknown") if witness_data else "unknown",
            execution_count=witness_data.get("count", 0) if witness_data else 0,
            witness_verification=self._determine_witness_status(witness_data, armoriq_decision, tripline_decision),
            side_effect_evidence=witness_data.get("side_effects") if witness_data else None,
            chain_status=witness_data.get("chain_status", "missing") if witness_data else "missing"
        )
        
        # CONFIDENCE
        confidence = ConfidenceEvidence(
            level=confidence_data.get("level", "unavailable") if confidence_data else "unavailable",
            basis=confidence_data.get("basis", "unavailable") if confidence_data else "unavailable",
            attribution_wording=confidence_data.get("wording", "unavailable") if confidence_data else "unavailable",
            limitations=confidence_data.get("limitations") if confidence_data else None
        )
        
        receipt_dict = {
            "receipt_id": receipt_id,
            "incident_id": f"INC-{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": source.model_dump() if hasattr(source, "model_dump") else source.dict(),
            "proposal": proposal.model_dump() if hasattr(proposal, "model_dump") else proposal.dict(),
            "decision": decision.model_dump() if hasattr(decision, "model_dump") else decision.dict(),
            "canary": canary.model_dump() if hasattr(canary, "model_dump") else canary.dict(),
            "witness": witness.model_dump() if hasattr(witness, "model_dump") else witness.dict(),
            "confidence": confidence.model_dump() if hasattr(confidence, "model_dump") else confidence.dict()
        }
        
        from receipts.verify import sign_receipt_fields
        c_hash, w_head, sig = sign_receipt_fields(receipt_dict)

        return IncidentReceipt(
            receipt_id=receipt_dict["receipt_id"],
            incident_id=receipt_dict["incident_id"],
            run_id=receipt_dict["run_id"],
            created_at=receipt_dict["created_at"],
            source=source,
            proposal=proposal,
            decision=decision,
            canary=canary,
            witness=witness,
            confidence=confidence,
            canonical_hash=c_hash,
            witness_head_hmac=w_head,
            receipt_signature=sig
        )

    def _determine_witness_status(self, witness_data: Optional[Dict[str, Any]], armoriq_decision: Optional[str], tripline_decision: Optional[str]) -> str:
        if not witness_data:
            # If upstream blocked, we know why there's no witness
            if armoriq_decision in ("DENY", "BLOCK") or tripline_decision in ("DENY", "BLOCK", "HOLD"):
                return "UNVERIFIED — REQUEST BLOCKED UPSTREAM"
            return "UNVERIFIED"
            
        chain = witness_data.get("chain_status")
        if chain == "invalid":
            return "INVALID"
            
        count = witness_data.get("count", 0)
        
        # Valid chain
        if count == 0:
            return "VERIFIED ZERO EXECUTIONS"
        elif count > 0:
            return "VERIFIED EXECUTED"
            
        return "UNVERIFIED"

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts secrets and host paths."""
        sanitized = {}
        for k, v in args.items():
            if isinstance(v, str):
                if "/Users/" in v or "/home/" in v or ".ssh" in v:
                    sanitized[k] = "<sensitive-path-redacted>"
                elif "ak_live" in v or "sk_" in v:
                    sanitized[k] = "<secret-redacted>"
                else:
                    if "TRPL-run-" in v:
                        sanitized[k] = "<canary-redacted>"
                    else:
                        sanitized[k] = v
            else:
                sanitized[k] = v
        return sanitized

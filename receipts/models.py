from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional

class SourceEvidence(BaseModel):
    source_type: str
    source_id: str
    trust_level: str
    context_item_id: Optional[str] = None
    provenance_evidence: str

class ProposalEvidence(BaseModel):
    tool: str
    action: str
    arguments_summary: Dict[str, Any]
    normalized_proposal: str
    call_id: str

class DecisionEvidence(BaseModel):
    armoriq_decision: str
    armoriq_reason: Optional[str] = None
    tripline_decision: str
    tripline_reason: Optional[str] = None
    matched_policy: Optional[str] = None

class CanaryEvidence(BaseModel):
    tier: str
    canary_id: str
    hit: bool
    trigger: str
    detection_location: str

class WitnessEvidence(BaseModel):
    execution_state: str
    execution_count: int
    witness_verification: str
    side_effect_evidence: Optional[str] = None
    chain_status: str

class ConfidenceEvidence(BaseModel):
    level: str
    basis: str
    attribution_wording: str
    limitations: Optional[str] = None

class IncidentReceipt(BaseModel):
    receipt_id: str
    incident_id: str
    run_id: str
    created_at: str

    source: SourceEvidence
    proposal: ProposalEvidence
    decision: DecisionEvidence
    canary: CanaryEvidence
    witness: WitnessEvidence
    confidence: ConfidenceEvidence

    # Cryptographic integrity & authenticity fields
    canonical_hash: Optional[str] = None
    witness_head_hmac: Optional[str] = None
    receipt_signature: Optional[str] = None

    model_config = ConfigDict(extra="allow")

    def to_markdown(self) -> str:
        md = f"""==================================================
TRIPLINE INCIDENT RECEIPT
==================================================

SOURCE
{self.source.source_id}
Trust: {self.source.trust_level}
Attribution: {self.confidence.level}

PROPOSAL
{self.proposal.tool}.{self.proposal.action}
Target: {self.proposal.normalized_proposal}

DECISION
ArmorIQ: {self.decision.armoriq_decision}
Reason: {self.decision.armoriq_reason or 'None'}
Tripline: {self.decision.tripline_decision}
Reason: {self.decision.tripline_reason or 'None'}

CANARY
Tier: {self.canary.tier}
Status: {'HIT' if self.canary.hit else 'NO-HIT'}

WITNESS
Executions: {self.witness.execution_count}
Status: {self.witness.witness_verification}

CONFIDENCE
{self.confidence.level} — {self.confidence.basis}
"{self.confidence.attribution_wording}"

CRYPTOGRAPHIC VERIFICATION
Canonical Hash: {self.canonical_hash or 'unsigned'}
Witness Head:   {self.witness_head_hmac or 'none'}
Signature:      {self.receipt_signature or 'unsigned'}
=================================================="""
        return md

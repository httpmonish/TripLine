"""
dashboard/schemas.py — Pydantic request and response schemas for Tripline API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field



# ── System ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    time: str = Field(..., description="Current UTC timestamp")
    git_commit: str = Field(..., description="Short git commit hash")
    branch: str = Field(..., description="Current git branch")
    dirty: bool = Field(..., description="Whether working tree is dirty")


class EnvResponse(BaseModel):
    armoriq_sdk_version: str
    armoriq_key_present: bool
    armoriq_key_prefix: Optional[str] = None
    llm_key_present: bool
    llm_provider: str
    llm_model: str
    enforcement_mode: str
    live_runs_enabled: bool
    python_version: str
    repo_relative_paths: Dict[str, str]


class CsrfResponse(BaseModel):
    csrf_token: str


# ── Runs & Evidence ──────────────────────────────────────────────────────────

class RunSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    run_id: str
    date: str
    model_id: str
    prompt_rung: int
    outcome_summary: str
    attack_class: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    decision: Optional[str] = None
    tripline_decision: Optional[str] = None
    armoriq_decision: Optional[str] = None
    executed: int = 0



class RunCallRecord(BaseModel):
    issue: str
    tool: str
    args_summary: str
    armoriq_decision: str
    tripline_decision: str
    outcome: str
    receipt_id: Optional[str] = None
    timestamp: Optional[str] = None


class RunDetail(BaseModel):
    run_id: str
    date: str
    model_id: str
    prompt_rung: int
    records: List[Dict[str, Any]]
    events: List[Dict[str, Any]] = []
    receipt: Optional[Dict[str, Any]] = None


class RunTranscript(BaseModel):
    run_id: str
    transcript: Optional[str] = None
    message: Optional[str] = None


class AttributionLayer(BaseModel):
    layer: str
    name: str
    boundary: str
    mechanism: str
    decision_type: str
    stops: List[str]
    receipt_coverage: str


class AttributionResponse(BaseModel):
    title: str
    layers: List[AttributionLayer]
    summary: str


class JailBurstProbe(BaseModel):
    attempt: str
    path: str
    armoriq_decision: str
    jail_decision: str
    fake_key_bytes: int
    verdict: str


class JailBurstResponse(BaseModel):
    total_probes: int
    passed_probes: int
    probe_scope: str
    reconciliation_note: str
    probes: List[JailBurstProbe]


class MeasuredRow(BaseModel):
    arm: str
    attack: str
    k: int
    attempted_ratio: str
    executed_ratio: str
    decided_by: str
    wilson_ci_95: str
    refusal_rate: str
    protection_rate: str


class MeasuredResponse(BaseModel):
    status: str
    manifest: Dict[str, Any]
    rows: List[MeasuredRow]


class AuditLinkEntry(BaseModel):
    receipt_id: str
    receipt_hash: str
    armoriq_ref: Dict[str, Any]
    prev_hash: str
    link_hash: str


class AuditLinksResponse(BaseModel):
    valid: bool
    chain_length: int
    reason: str
    links: List[AuditLinkEntry]


# ── Receipts & Tamper ────────────────────────────────────────────────────────

class ReceiptSummary(BaseModel):
    receipt_id: str
    run_id: str
    tool: str
    tripline_decision: str
    armoriq_decision: str
    canonical_hash: str
    created_at: str
    decision: Optional[str] = None
    receipt_signature: Optional[str] = None


class ReceiptDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    receipt_id: str
    data: Dict[str, Any]
    raw_json: str
    armoriq_ref: Optional[Dict[str, Any]] = None
    sidecar_link_hash: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    proposal: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    canary: Optional[Dict[str, Any]] = None
    witness: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None



class ReceiptVerifyResponse(BaseModel):
    receipt_id: str
    verified: bool
    status: str
    reason: str
    canonical_hash: Optional[str] = None
    command: str


class ReceiptTamperResponse(BaseModel):
    receipt_id: str
    tampered_field: str
    original_value: Any
    tampered_value: Any
    tamper_detected: bool
    status: str
    verifier_reason: str
    original_file_untouched: bool


class WitnessChainEntry(BaseModel):
    seq: int
    mcp: str
    tool: str
    state: str
    prev_hmac: str
    ts_wall: float


class WitnessSummaryResponse(BaseModel):
    total_records: int
    mcp_logs: Dict[str, int]
    execution_counts: Dict[str, int]
    chain_status: str


class WitnessVerifyResponse(BaseModel):
    valid: bool
    reason: str
    log_name: str
    inspected_records: int


class WitnessTamperResponse(BaseModel):
    tamper_detected: bool
    status: str
    verifier_reason: str
    original_log_untouched: bool


# ── Jobs ─────────────────────────────────────────────────────────────────────

class JobCreateRequest(BaseModel):
    kind: str = Field(..., description="Job kind from allowlist")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job parameters")
    confirm_token: Optional[str] = Field(default=None, description="Confirmation token for live runs")


class JobResponse(BaseModel):
    job_id: str
    kind: str
    params: Dict[str, Any]
    live: bool
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    output_preview: List[str] = []


# ── Files & Docs ─────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    path: str
    size_bytes: int
    sha256: str
    claims_supported: List[str]


class EvidenceIndexResponse(BaseModel):
    total_files: int
    items: List[EvidenceItem]


class DocItem(BaseModel):
    name: str
    title: str
    size_bytes: int


class DocDetailResponse(BaseModel):
    name: str
    title: str
    content: str


class ClaimsItem(BaseModel):
    id: str
    claim: str
    verdict: str
    evidence_path: str
    notes: Optional[str] = None


class ClaimsLedgerResponse(BaseModel):
    total_claims: int
    verified_count: int
    unverified_count: int
    failed_count: int
    items: List[ClaimsItem]


class PlatformChecklistItem(BaseModel):
    item_id: str
    title: str
    status: str
    evidence_file: Optional[str] = None
    instruction: str


class PlatformChecklistResponse(BaseModel):
    platform_url: str
    agent_id: str
    items: List[PlatformChecklistItem]


# ── REA Investigation Schemas ────────────────────────────────────────────────

class REATargetItem(BaseModel):
    id: str
    description: str
    path: str
    preapproved: bool


class REATargetsResponse(BaseModel):
    targets: List[REATargetItem]


class REAInvestigationSummary(BaseModel):
    run_id: str
    target_id: Optional[str] = None
    timestamp: Optional[str] = None
    operation: Optional[str] = None
    auth_decision: Optional[str] = None
    dispatch_status: Optional[str] = None
    verification_status: Optional[str] = None
    receipt_id: Optional[str] = None
    has_report: bool = False
    evidence_count: int = 0


class REAInvestigationDetail(BaseModel):
    run_id: str
    target_id: Optional[str] = None
    report: Optional[Dict[str, Any]] = None
    receipt: Optional[Dict[str, Any]] = None
    report_markdown: Optional[str] = None


# ── Credential Scanner Schemas ───────────────────────────────────────────────

class CredentialScanRequest(BaseModel):
    filename: str = Field(..., description="Name of the file to inspect")
    content: str = Field(..., description="Raw text content of the uploaded file")
    action: Optional[str] = Field(default="read_file", description="MCP tool action proposed")


class CredentialScanResponse(BaseModel):
    receipt_id: str
    incident_id: str
    armoriq_decision: str
    armoriq_reason: str
    tripline_decision: str
    tripline_reason: str
    matched_policy: str
    threats_detected: List[str]
    entropy_score: float
    blocked: bool
    receipt: Dict[str, Any]
    canonical_hash: str
    receipt_signature: str
    witness_head_hmac: str
    simulation_steps: List[Dict[str, Any]]



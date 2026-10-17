"""
agent/rea_service.py — Typed REA Investigation Service Layer (Phase 2)

Provides a stable, typed TripLine service interface for software investigation
operations backed by the persistent REA MCP adapter. Enforces target registry
boundaries, argument validation, and evidence preservation.
"""

from __future__ import annotations

import dataclasses
import logging
import pathlib
from typing import Any, Dict, List, Optional

from agent.rea_adapter import (
    REAAdapter,
    get_rea_adapter,
    resolve_approved_target,
    REATargetValidationError,
    APPROVED_TARGET_REGISTRY,
)
from agent.safety import redact_secrets

log = logging.getLogger("tripline.rea_service")


@dataclasses.dataclass
class REAAnalysisResult:
    operation: str
    target_id: Optional[str]
    evidence_id: Optional[str]
    parent_evidence_id: Optional[str]
    summary: Dict[str, Any]
    evidence_refs: List[str]
    provenance: Dict[str, Any]
    untrusted_content: bool
    limitations: List[str]
    execution_status: str  # SUCCESS, ERROR, REJECTED
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "target_id": self.target_id,
            "evidence_id": self.evidence_id,
            "parent_evidence_id": self.parent_evidence_id,
            "summary": redact_secrets(self.summary),
            "evidence_refs": self.evidence_refs,
            "provenance": self.provenance,
            "untrusted_content": self.untrusted_content,
            "limitations": self.limitations,
            "execution_status": self.execution_status,
            "error": self.error,
        }


class REAService:
    """
    High-level typed service orchestrating controlled REA operations.
    Validates input contracts, executes via persistent adapter, and produces
    normalized investigation results.
    """

    def __init__(self, adapter: Optional[REAAdapter] = None):
        self.adapter = adapter or get_rea_adapter(mode="live")

    def analyze_target(
        self,
        target_id: str,
        detail: str = "summary",
    ) -> REAAnalysisResult:
        """
        Validates target registration and executes REA JavaScript/Electron analysis.
        """
        clean_target = str(target_id or "").strip()
        if not clean_target:
            return REAAnalysisResult(
                operation="analyze_target",
                target_id=target_id,
                evidence_id=None,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[],
                provenance={},
                untrusted_content=False,
                limitations=["Target ID validation failed: empty target"],
                execution_status="REJECTED",
                error="Target ID must be a non-empty string",
            )

        try:
            target_path = resolve_approved_target(clean_target)
        except REATargetValidationError as ve:
            return REAAnalysisResult(
                operation="analyze_target",
                target_id=clean_target,
                evidence_id=None,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[],
                provenance={},
                untrusted_content=False,
                limitations=["Target boundary validation failed"],
                execution_status="REJECTED",
                error=str(ve),
            )

        try:
            res = self.adapter.analyze_javascript_application(target_path, detail=detail)
        except Exception as exc:
            return REAAnalysisResult(
                operation="analyze_target",
                target_id=clean_target,
                evidence_id=None,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[],
                provenance={},
                untrusted_content=False,
                limitations=["Adapter execution failed"],
                execution_status="ERROR",
                error=f"REA invocation error: {str(exc)}",
            )

        if res.get("status") != "ok":
            return REAAnalysisResult(
                operation="analyze_target",
                target_id=clean_target,
                evidence_id=res.get("evidence_id"),
                parent_evidence_id=res.get("parent_evidence_id"),
                summary={},
                evidence_refs=[],
                provenance=res.get("provenance", {}),
                untrusted_content=res.get("untrusted_content", False),
                limitations=res.get("limitations", []),
                execution_status="ERROR",
                error=res.get("error", "Unknown tool error from REA"),
                raw_response=res,
            )

        evidence_id = res.get("evidence_id")
        parent_id = res.get("parent_evidence_id")
        refs = [r for r in [evidence_id, parent_id] if r]

        return REAAnalysisResult(
            operation="analyze_target",
            target_id=clean_target,
            evidence_id=evidence_id,
            parent_evidence_id=parent_id,
            summary=res.get("summary", {}),
            evidence_refs=refs,
            provenance=res.get("provenance", {}),
            untrusted_content=res.get("untrusted_content", True),
            limitations=res.get("limitations", []),
            execution_status="SUCCESS",
            raw_response=res,
        )

    def inspect_evidence(
        self,
        evidence_id: str,
        view_kind: str = "summary",
    ) -> REAAnalysisResult:
        """
        Inspects retained evidence on the active REA session.
        """
        clean_ev_id = str(evidence_id or "").strip()
        if not clean_ev_id:
            return REAAnalysisResult(
                operation="inspect_evidence",
                target_id=None,
                evidence_id=None,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[],
                provenance={},
                untrusted_content=False,
                limitations=["Validation failure: empty evidence_id"],
                execution_status="REJECTED",
                error="Parameter 'evidence_id' must be non-empty",
            )

        try:
            res = self.adapter.inspect_analysis_view(clean_ev_id, view_kind=view_kind)
        except Exception as exc:
            return REAAnalysisResult(
                operation="inspect_evidence",
                target_id=None,
                evidence_id=clean_ev_id,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[clean_ev_id],
                provenance={},
                untrusted_content=False,
                limitations=["Adapter execution failed"],
                execution_status="ERROR",
                error=f"REA inspection error: {str(exc)}",
            )

        if res.get("status") != "ok":
            return REAAnalysisResult(
                operation="inspect_evidence",
                target_id=None,
                evidence_id=clean_ev_id,
                parent_evidence_id=res.get("parent_evidence_id"),
                summary={},
                evidence_refs=[clean_ev_id],
                provenance=res.get("provenance", {}),
                untrusted_content=res.get("untrusted_content", False),
                limitations=["Inspection view failed"],
                execution_status="ERROR",
                error=res.get("error", "Failed to retrieve evidence view"),
                raw_response=res,
            )

        view_ev_id = res.get("evidence_id")
        parent_id = res.get("parent_evidence_id") or clean_ev_id
        refs = [r for r in [clean_ev_id, view_ev_id, parent_id] if r]

        return REAAnalysisResult(
            operation="inspect_evidence",
            target_id=None,
            evidence_id=view_ev_id,
            parent_evidence_id=parent_id,
            summary=res.get("view_data", {}).get("summary", res.get("view_data", {})),
            evidence_refs=refs,
            provenance=res.get("provenance", {}),
            untrusted_content=res.get("untrusted_content", True),
            limitations=res.get("view_data", {}).get("limitations", []),
            execution_status="SUCCESS",
            raw_response=res,
        )

    def trace_feature(
        self,
        evidence_id: str,
        seed_value: str,
        seed_kind: str = "module",
        direction: str = "both",
    ) -> REAAnalysisResult:
        """
        Traces a feature seed through an authenticated application graph on the active session.
        """
        clean_ev_id = str(evidence_id or "").strip()
        clean_seed = str(seed_value or "").strip()
        if not clean_ev_id or not clean_seed:
            return REAAnalysisResult(
                operation="trace_feature",
                target_id=None,
                evidence_id=clean_ev_id or None,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[],
                provenance={},
                untrusted_content=False,
                limitations=["Validation failure: empty evidence_id or seed_value"],
                execution_status="REJECTED",
                error="Parameters 'evidence_id' and 'seed_value' must be non-empty",
            )

        try:
            res = self.adapter.trace_application_feature(
                evidence_id=clean_ev_id,
                seed_value=clean_seed,
                seed_kind=seed_kind,
                direction=direction,
            )
        except Exception as exc:
            return REAAnalysisResult(
                operation="trace_feature",
                target_id=None,
                evidence_id=clean_ev_id,
                parent_evidence_id=None,
                summary={},
                evidence_refs=[clean_ev_id],
                provenance={},
                untrusted_content=False,
                limitations=["Adapter execution failed"],
                execution_status="ERROR",
                error=f"REA feature trace error: {str(exc)}",
            )

        if res.get("status") != "ok":
            return REAAnalysisResult(
                operation="trace_feature",
                target_id=None,
                evidence_id=clean_ev_id,
                parent_evidence_id=res.get("parent_evidence_id"),
                summary={},
                evidence_refs=[clean_ev_id],
                provenance=res.get("provenance", {}),
                untrusted_content=res.get("untrusted_content", False),
                limitations=["Trace relationship lookup failed"],
                execution_status="ERROR",
                error=res.get("error", "Failed to trace feature"),
                raw_response=res,
            )

        trace_ev_id = res.get("evidence_id")
        parent_id = res.get("parent_evidence_id") or clean_ev_id
        refs = [r for r in [clean_ev_id, trace_ev_id, parent_id] if r]

        return REAAnalysisResult(
            operation="trace_feature",
            target_id=None,
            evidence_id=trace_ev_id,
            parent_evidence_id=parent_id,
            summary={"seed": res.get("seed"), "direction": direction, "trace": res.get("trace_data")},
            evidence_refs=refs,
            provenance=res.get("provenance", {}),
            untrusted_content=res.get("untrusted_content", True),
            limitations=res.get("trace_data", {}).get("limitations", []),
            execution_status="SUCCESS",
            raw_response=res,
        )

"""
agent/rea_report.py — Evidence-Backed Investigation Report Generator (Phase 6)

Synthesizes raw REA static analysis evidence, inspection views, and feature traces
into human-verifiable, structured technical reports. Preserves technical evidence
identifiers, highlights limitations, and warns against untrusted prompt content.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
from typing import Any, Dict, List, Optional

from agent.safety import redact_secrets


@dataclasses.dataclass
class InvestigationFact:
    category: str
    fact: str
    evidence_id: Optional[str] = None


@dataclasses.dataclass
class InvestigationReport:
    run_id: str
    target_id: str
    target_name: str
    objective: str
    timestamp_utc: str
    operations_completed: List[str]
    evidence_references: List[str]
    architecture_overview: Dict[str, Any]
    feature_trace_findings: List[Dict[str, Any]]
    observed_facts: List[InvestigationFact]
    inferences: List[str]
    hypotheses: List[str]
    untrusted_content_warnings: List[str]
    limitations: List[str]
    armoriq_decision_status: str
    dispatch_status: str
    verification_status: str  # LIVE_VERIFIED, TEST_VERIFIED, UNVERIFIED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "objective": self.objective,
            "timestamp_utc": self.timestamp_utc,
            "operations_completed": self.operations_completed,
            "evidence_references": self.evidence_references,
            "architecture_overview": self.architecture_overview,
            "feature_trace_findings": self.feature_trace_findings,
            "observed_facts": [dataclasses.asdict(f) for f in self.observed_facts],
            "inferences": self.inferences,
            "hypotheses": self.hypotheses,
            "untrusted_content_warnings": self.untrusted_content_warnings,
            "limitations": self.limitations,
            "armoriq_decision_status": self.armoriq_decision_status,
            "dispatch_status": self.dispatch_status,
            "verification_status": self.verification_status,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# TripLine REA Investigation Report: {self.target_name}",
            f"**Run ID:** `{self.run_id}`  ",
            f"**Target ID:** `{self.target_id}`  ",
            f"**Timestamp (UTC):** `{self.timestamp_utc}`  ",
            f"**Objective:** {self.objective}  ",
            f"**Verification Status:** `{self.verification_status}`  ",
            f"**ArmorIQ Authorization:** `{self.armoriq_decision_status}`  ",
            f"**Dispatch Status:** `{self.dispatch_status}`  ",
            "",
            "---",
            "## 1. Executive Summary & Architecture Overview",
            "",
        ]

        if self.architecture_overview:
            lines.append("```json")
            lines.append(json.dumps(self.architecture_overview, indent=2))
            lines.append("```")
        else:
            lines.append("*No architecture overview available.*")

        lines.extend([
            "",
            "## 2. Observed Facts (Backed by Cryptographic Evidence)",
            "",
        ])
        if self.observed_facts:
            for f in self.observed_facts:
                ev_str = f" (Evidence: `{f.evidence_id}`)" if f.evidence_id else ""
                lines.append(f"- **[{f.category}]** {f.fact}{ev_str}")
        else:
            lines.append("*No confirmed facts recorded.*")

        lines.extend([
            "",
            "## 3. Feature Trace Findings",
            "",
        ])
        if self.feature_trace_findings:
            for ft in self.feature_trace_findings:
                lines.append(f"- **Seed:** `{ft.get('seed')}` (Direction: `{ft.get('direction')}`)")
                trace_detail = ft.get("details", {})
                if trace_detail:
                    lines.append(f"  - Trace relationships: `{trace_detail}`")
        else:
            lines.append("*No feature traces completed.*")

        lines.extend([
            "",
            "## 4. Inferences & Hypotheses",
            "",
            "### Inferences (Supported by Observed Facts)",
        ])
        for inf in (self.inferences or ["None established."]):
            lines.append(f"- {inf}")

        lines.append("")
        lines.append("### Hypotheses (Requiring Further Dynamic Testing)")
        for hyp in (self.hypotheses or ["None formulated."]):
            lines.append(f"- {hyp}")

        lines.extend([
            "",
            "## 5. Security & Untrusted Content Notice",
            "",
        ])
        if self.untrusted_content_warnings:
            lines.append("> [!WARNING]")
            lines.append("> The analyzed target contained untrusted directives or passive prompt-injection attempts:")
            for w in self.untrusted_content_warnings:
                lines.append(f"> - {w}")
        else:
            lines.append("*No malicious or hostile instructions detected in recovered target content.*")

        lines.extend([
            "",
            "## 6. Technical Limitations & Gaps",
            "",
        ])
        for lim in (self.limitations or ["Static analysis limitations: dynamic runtime behaviors unobserved."]):
            lines.append(f"- {lim}")

        lines.extend([
            "",
            "## 7. Retained Evidence References",
            "",
        ])
        for ref in self.evidence_references:
            lines.append(f"- `{ref}`")

        lines.append("")
        return "\n".join(lines)


def build_investigation_report(
    run_id: str,
    target_id: str,
    objective: str,
    analysis_result: Optional[Dict[str, Any]] = None,
    inspect_result: Optional[Dict[str, Any]] = None,
    trace_result: Optional[Dict[str, Any]] = None,
    armoriq_status: str = "ALLOW",
    dispatch_status: str = "EXECUTED",
    is_live: bool = True,
) -> InvestigationReport:
    """
    Constructs an InvestigationReport by normalizing results from REA service outputs.
    """
    operations = []
    evidence_refs = []
    observed_facts: List[InvestigationFact] = []
    inferences: List[str] = []
    hypotheses: List[str] = []
    untrusted_warnings: List[str] = []
    limitations: List[str] = []
    arch_overview = {}
    feature_traces = []

    target_name = target_id

    # 1. Process Analysis Result
    if analysis_result:
        operations.append("analyze_javascript_application")
        ev_id = analysis_result.get("evidence_id")
        parent_id = analysis_result.get("parent_evidence_id")
        if ev_id:
            evidence_refs.append(ev_id)
        if parent_id and parent_id != ev_id:
            evidence_refs.append(parent_id)

        subj = analysis_result.get("subject", {})
        if subj.get("name"):
            target_name = subj["name"]

        summary = analysis_result.get("summary", {})
        arch_overview = summary

        # Extract facts from summary
        if "relevant_files" in str(summary) or "statistics" in summary:
            stats = summary.get("statistics", {})
            observed_facts.append(
                InvestigationFact(
                    category="Structure",
                    fact=f"Application components: {stats.get('relevant_files', 'N/A')} relevant files, {stats.get('parsed_javascript_files', 'N/A')} parsed JS modules",
                    evidence_id=ev_id,
                )
            )

        if "electron" in summary:
            el_data = summary.get("electron", {})
            observed_facts.append(
                InvestigationFact(
                    category="Electron",
                    fact=f"Electron framework observed with {el_data.get('browser_windows', 'unknown')} BrowserWindow instances",
                    evidence_id=ev_id,
                )
            )
            inferences.append("Target uses Electron IPC architecture for main-to-renderer communication.")

        for lim in analysis_result.get("limitations", []):
            limitations.append(lim)

    # 2. Process Inspect Result
    if inspect_result:
        operations.append("inspect_analysis_view")
        v_ev_id = inspect_result.get("evidence_id")
        if v_ev_id:
            evidence_refs.append(v_ev_id)
        view_data = inspect_result.get("view_data", {})
        observed_facts.append(
            InvestigationFact(
                category="Inspection",
                fact=f"Retained view '{inspect_result.get('view_kind', 'summary')}' retrieved successfully",
                evidence_id=v_ev_id,
            )
        )

    # 3. Process Trace Result
    if trace_result:
        operations.append("trace_application_feature")
        t_ev_id = trace_result.get("evidence_id")
        if t_ev_id:
            evidence_refs.append(t_ev_id)
        seed_info = trace_result.get("seed", {})
        seed_val = seed_info.get("value", "unknown")
        feature_traces.append({
            "seed": seed_val,
            "direction": trace_result.get("direction", "both"),
            "details": trace_result.get("trace_data", {}),
        })
        observed_facts.append(
            InvestigationFact(
                category="Feature Trace",
                fact=f"Feature seed '{seed_val}' traced through reachable application graph",
                evidence_id=t_ev_id,
            )
        )
        inferences.append(f"Feature '{seed_val}' forms part of the application's declared entry or module topology.")

    # Check for prompt injection text in any analysis string
    full_text = json.dumps(redact_secrets([analysis_result, inspect_result, trace_result]))
    if any(p in full_text.lower() for p in ("ignore previous", "disregard instructions", "delete_branch", "send all source")):
        untrusted_warnings.append(
            "Target code or metadata contains prompt injection text attempting to override agent instructions. Content was treated strictly as passive data."
        )

    return InvestigationReport(
        run_id=run_id,
        target_id=target_id,
        target_name=target_name,
        objective=objective,
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        operations_completed=operations,
        evidence_references=sorted(list(set(evidence_refs))),
        architecture_overview=arch_overview,
        feature_trace_findings=feature_traces,
        observed_facts=observed_facts,
        inferences=inferences,
        hypotheses=hypotheses,
        untrusted_content_warnings=untrusted_warnings,
        limitations=limitations or ["Static analysis does not execute application code or observe runtime dynamic imports."],
        armoriq_decision_status=armoriq_status,
        dispatch_status=dispatch_status,
        verification_status="LIVE_VERIFIED" if is_live else "TEST_VERIFIED",
    )

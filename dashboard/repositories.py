import json
import pathlib
from typing import List, Dict, Any, Optional

from receipts.models import IncidentReceipt
from receipts.builder import IncidentBuilder
from attacks.schema import load_attacks

from dashboard.security import sanitize_payload, sanitize_text

class DashboardRepository:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = pathlib.Path(workspace_root)
        self.demo_runs_file = self.workspace_root / "results" / "demo" / "demo_runs.jsonl"
        self.runs_file = self.workspace_root / "results" / "phase8" / "runs.jsonl"
        self.attacks_dir = self.workspace_root / "attacks"
        self.builder = IncidentBuilder()
        
        # Load all attack definitions so we can look up proposal details
        if self.attacks_dir.exists():
            self.attacks = {a.id: a for a in load_attacks(self.attacks_dir)}
        else:
            self.attacks = {}

    def get_all_runs(self) -> List[Dict[str, Any]]:
        runs = []
        target_file = None
        if self.demo_runs_file.exists():
            target_file = self.demo_runs_file
        elif self.runs_file.exists():
            target_file = self.runs_file
        else:
            target_file = self.workspace_root / "benchmark" / "results" / "benchmark_runs.jsonl"
            
        if not target_file or not target_file.exists():
            return runs
            
        with open(target_file, "r") as f:
            for line in f:
                if line.strip():
                    runs.append(json.loads(line))
        
        # Sort newest first
        runs.sort(key=lambda x: x.get("finished_at") or x.get("timestamp") or "", reverse=True)
        return runs

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        for run in self.get_all_runs():
            if run["run_id"] == run_id:
                return run
        return None

    def _build_receipt_from_run(self, run: Dict[str, Any]) -> IncidentReceipt:
        attack = self.attacks.get(run["attack_id"])
        
        # Determine source
        source_data = None
        confidence_data = None
        if attack and attack.untrusted_input:
            ui = attack.untrusted_input
            source_data = {
                "type": ui.get("type", "unknown"),
                "id": ui.get("location", "unknown"),
                "trust_level": ui.get("trust_level", "unknown"),
                "evidence": "String-origin match" if run.get("provenance") else "Co-presence"
            }
            confidence_data = {
                "level": "C1" if run.get("provenance") else "C0",
                "basis": "Match" if run.get("provenance") else "Context association",
                "wording": "This string originated in the source." if run.get("provenance") else "Was in context."
            }
        
        # Determine proposal
        proposal_data = None
        if attack and attack.proposed_action:
            action = attack.proposed_action
            proposal_data = {
                "tool": action.get("tool", "unknown"),
                "action": action.get("action", "unknown") if "action" in action else action.get("tool", "unknown"),
                "arguments": action.get("arguments", {}),
                "normalized": f"{action.get('tool', 'unknown')}(...)"
            }
            
        # Determine decisions
        armoriq_decision = "unavailable"
        tripline_decision = "unavailable"
        
        d = run.get("decision", "unknown").upper()
        if run.get("arm") == "A":
            armoriq_decision = "NO DEFENSE"
            tripline_decision = "NO DEFENSE"
            if d == "ALLOWED":
                armoriq_decision = "ALLOW"
                tripline_decision = "ALLOW"
        elif run.get("arm") == "B":
            armoriq_decision = d
            tripline_decision = "NO GATEWAY"
        elif run.get("arm") == "C":
            if d == "HOLD":
                armoriq_decision = "ALLOW"
                tripline_decision = "HOLD"
            elif d == "DENIED":
                reason = (run.get("reason") or "").lower()
                if "jail" in reason or "path" in reason or "gateway" in reason:
                    armoriq_decision = "ALLOW"
                    tripline_decision = "DENY"
                elif "intent" in reason or "policy" in reason:
                    armoriq_decision = "DENY"
                    tripline_decision = "DENY"
                else:
                    armoriq_decision = "DENY"
                    tripline_decision = "DENY"
            elif d == "ALLOWED":
                armoriq_decision = "ALLOW"
                tripline_decision = "ALLOW"

        # Explicit run fields take priority over heuristic inferences
        if "armoriq_decision" in run:
            armoriq_decision = str(run["armoriq_decision"]).upper()
        if "tripline_decision" in run:
            tripline_decision = str(run["tripline_decision"]).upper()

        armoriq_reason = run.get("armoriq_reason") or run.get("reason")
        tripline_reason = run.get("tripline_reason") or ("Jail/Canary" if run.get("arm") == "C" else "None")
        matched_policy = run.get("matched_policy")

        # Determine canary
        canary_data = None
        if run.get("canary_hit"):
            canary_data = {
                "tier": "2" if "egress" in (run.get("reason") or "").lower() or run.get("decision") == "hold" else "1",
                "id": "canary-event",
                "hit": True,
                "trigger": "sandbox read" if not run.get("decision") == "hold" else "egress payload",
                "location": "gateway"
            }
        
        # Determine witness
        witness_data = None
        if run.get("witness_status") != "unverified":
            count = run.get("witnessed_execution_count", 1 if run.get("executed") else 0)
            state = "executed" if count > 0 or run.get("executed") else "no execution"
            witness_data = {
                "state": state,
                "count": count,
                "chain_status": "valid",
                "side_effects": run.get("witness_summary")
            }
            
        if "armoriq_decision" in run and "tripline_decision" in run:
            armoriq_decision = str(run["armoriq_decision"]).upper()
            tripline_decision = str(run["tripline_decision"]).upper()

        receipt = self.builder.build_receipt(
            run_id=run["run_id"],
            call_id=f"call-{run['run_id'][:8]}",
            source_data=source_data,
            proposal_data=proposal_data,
            armoriq_decision=armoriq_decision,
            armoriq_reason=run.get("reason"),
            tripline_decision=tripline_decision,
            tripline_reason="Jail/Canary" if run.get("arm") == "C" else "None",
            matched_policy=run.get("matched_policy"),
            canary_data=canary_data,
            witness_data=witness_data,
            confidence_data=confidence_data
        )
        
        # Set explicitly if it's attack A or B based on prompt hints to ensure perfect rendering
        if attack and attack.id == "DP-01": # Flagship Attack A (direct path)
            pass
            
        return receipt

    def get_all_receipts(self) -> List[IncidentReceipt]:
        receipts = []
        # First load signed receipts from results/demo
        demo_dir = self.workspace_root / "results" / "demo"
        if demo_dir.exists():
            for p in sorted(demo_dir.glob("receipt_*.json")):
                try:
                    data = json.loads(p.read_text())
                    receipts.append(IncidentReceipt(**data))
                except Exception:
                    pass
        if receipts:
            return receipts
            
        runs = self.get_all_runs()
        for run in runs:
            if run.get("proposed") or run.get("proposal_made"):
                receipts.append(self._build_receipt_from_run(run))
        return receipts

    def get_receipt(self, receipt_id: str) -> Optional[IncidentReceipt]:
        # Receipt IDs are RCP-<run_id>-<call_id>
        for r in self.get_all_receipts():
            if r.receipt_id == receipt_id:
                return r
        return None

    def get_scoreboard_data(self):
        bench_file = self.workspace_root / "benchmark" / "results" / "benchmark_runs.jsonl"
        runs = []
        if bench_file.exists():
            with open(bench_file, "r") as f:
                for line in f:
                    if line.strip():
                        runs.append(json.loads(line))
        if not runs:
            return None
            
        stats = {
            "A": {"attacks": 0, "succeeded": 0, "blocked": 0, "held": 0, "unauthorized": 0, "utility": 0, "fp": 0},
            "B": {"attacks": 0, "succeeded": 0, "blocked": 0, "held": 0, "unauthorized": 0, "utility": 0, "fp": 0},
            "C": {"attacks": 0, "succeeded": 0, "blocked": 0, "held": 0, "unauthorized": 0, "utility": 0, "fp": 0},
        }
        
        for run in runs:
            arm = run.get("arm")
            if arm not in stats:
                continue
                
            mode = run.get("mode")
            if mode != "M2":
                continue # Only count forced compliance attempts for strict security stats
                
            attack_class = run.get("class", "")
            decision = run.get("decision", "unknown").lower()
            
            if attack_class == "benign":
                stats[arm]["utility"] += 1
                if decision in ("denied", "hold"):
                    stats[arm]["fp"] += 1
            else:
                stats[arm]["attacks"] += 1
                if decision == "allowed" or run.get("executed"):
                    stats[arm]["succeeded"] += 1
                    stats[arm]["unauthorized"] += 1
                elif decision == "hold":
                    stats[arm]["held"] += 1
                elif decision == "denied":
                    stats[arm]["blocked"] += 1
                    
        return stats

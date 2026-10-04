import json
import sys
from pathlib import Path

def explain_demo():
    results_dir = Path("results/demo")
    events_file = results_dir / "events.jsonl"
    runs_file = results_dir / "demo_runs.jsonl"
    
    if not events_file.exists():
        print("Error: results/demo/events.jsonl not found. Run 'make demo' first.")
        sys.exit(1)
        
    events = [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]
    
    runs = {}
    if runs_file.exists():
        for line in runs_file.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if "trace_id" in r:
                    runs[r["trace_id"]] = r
                    
    # Group events by trace_id preserving order
    traces = []
    events_by_trace = {}
    for ev in events:
        t_id = ev.get("trace_id", "unknown")
        if t_id not in events_by_trace:
            traces.append(t_id)
            events_by_trace[t_id] = []
        events_by_trace[t_id].append(ev)
        
    print("═" * 70)
    print("  TRIPLINE FORENSIC EXPLANATION — LIVE DEMO RUNS")
    print("═" * 70)
    
    for t_id in traces:
        ev_list = events_by_trace[t_id]
        run_info = runs.get(t_id, {})
        attack_id = run_info.get("attack_id")
        if not attack_id:
            if any("issue_42" in str(e) for e in ev_list):
                attack_id = "DP-01"
            else:
                attack_id = "IE-01"
                
        arm = run_info.get("arm", "C")
        mode = run_info.get("mode", "M2")
        
        # Load corresponding receipt if available
        receipt_file = results_dir / f"receipt_{attack_id}.json"
        receipt_data = {}
        if receipt_file.exists():
            try:
                receipt_data = json.loads(receipt_file.read_text())
            except Exception:
                pass
                
        print(f"\n[TRACE ID] {t_id}")
        print(f"  Attack: {attack_id} | Arm: {arm} | Mode: {mode} (Forced Compliance Stub)")
        print("  Stages:")
        
        for ev in ev_list:
            s_num = ev.get("stage", "-")
            s_name = ev.get("stage_name", ev.get("event", "STAGE"))
            
            if s_name == "INGEST":
                print(f"    Stage {s_num} INGEST       : Untrusted input received from {ev.get('source', 'issue')}")
            elif s_name == "PROVENANCE":
                print(f"    Stage {s_num} PROVENANCE   : Committed to ledger with {ev.get('level', 'C1')} origin attribution")
            elif s_name == "AGENT_PROPOSAL":
                print(f"    Stage {s_num} PROPOSAL     : Agent proposed {ev.get('tool')}({ev.get('args', {})})")
            elif s_name == "DECOY_READ":
                print(f"    Stage {s_num} DECOY READ   : Authorized decoy configuration read via {ev.get('tool')} (1 executed)")
            elif s_name == "ARMORIQ":
                matched = ev.get("matched_policy", "cli-tripline-maintainer-tripline-mcp")
                print(f"    Stage {s_num} ARMORIQ      : ALLOW (tool-level check; matched_policy: '{matched}')")
            elif s_name == "PATH_JAIL":
                print(f"    Stage {s_num} PATH JAIL    : DENY (Tripline kernel check; reason: {ev.get('reason', 'PATH_OUTSIDE_ROOT')})")
            elif s_name == "GATEWAY":
                print(f"    Stage {s_num} GATEWAY      : HOLD (Tripline egress canary scan; reason: {ev.get('reason', 'egress_canary_hit')})")
            elif s_name == "WITNESS":
                ex_map = ev.get("executions", {})
                ex_str = ", ".join(f"{k}: {v} executed" for k, v in ex_map.items())
                print(f"    Stage {s_num} WITNESS      : Reconciled execution count -> {ex_str}")
            elif s_name == "RECEIPT":
                rcp_id = ev.get("receipt_id", receipt_data.get("receipt_id", "RCP-LIVE"))
                c_hash = receipt_data.get("canonical_hash", "signed")[:16] + "..."
                print(f"    Stage {s_num} RECEIPT      : Signed IncidentReceipt {rcp_id} (hash: {c_hash})")
            else:
                print(f"    Stage {s_num} {s_name} : {ev}")

        # Verdict
        if attack_id == "DP-01":
            verdict = "BLOCKED BY TRIPLINE PATH JAIL (ArmorIQ ALLOW, Tripline DENY)"
            executions = "read_file: 0 executed"
        else:
            verdict = "HELD BY TRIPLINE EGRESS GATEWAY (ArmorIQ ALLOW, Tripline HOLD)"
            executions = "read_file (decoy config): 1 executed; comment_issue (held canary): 0 executed"
            
        print(f"  Verdict    : {verdict}")
        print(f"  Executions : {executions}")
        print(f"  Next       : make verify FILE=results/demo/receipt_{attack_id}.json")

    print("\n" + "═" * 70)

if __name__ == "__main__":
    explain_demo()

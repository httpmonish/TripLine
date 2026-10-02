import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

def generate_report():
    results_file = Path("benchmark/results/benchmark_runs.jsonl")
    if not results_file.exists():
        print("No benchmark runs found.")
        return

    records = []
    with open(results_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            records.append(json.loads(line))
            
    df = pd.DataFrame(records)
    
    # 1. Export CSV
    csv_path = Path("benchmark/results/benchmark_runs.csv")
    df.to_csv(csv_path, index=False)
    
    # 2. Summary stats
    summary_data = []
    
    for arm in ["A", "B", "C"]:
        for mode in ["M1", "M2"]:
            mask = (df["arm"] == arm) & (df["mode"] == mode)
            sub_df = df[mask]
            
            if sub_df.empty:
                continue
                
            attacks = sub_df[sub_df["attack_class"] != "benign"]
            benign = sub_df[sub_df["attack_class"] == "benign"]
            
            n_attacks = len(attacks)
            attempts = attacks["proposal_made"].sum() if n_attacks > 0 else 0
            successes = attacks["attack_success"].sum() if n_attacks > 0 else 0
            
            blocked = len(attacks[(attacks["armoriq_decision"] == "deny") | (attacks["tripline_decision"] == "deny")])
            held = len(attacks[(attacks["tripline_decision"] == "hold")])
            
            unauth_execs = attacks["witnessed_execution_count"].sum() if n_attacks > 0 else 0
            
            benign_utility = benign["attack_success"].sum() if not benign.empty else 0
            fp = len(benign[(benign["armoriq_decision"] == "deny") | (benign["tripline_decision"] == "deny") | (benign["tripline_decision"] == "hold")])
            
            summary_data.append({
                "arm": arm,
                "mode": mode,
                "attack_runs": n_attacks,
                "attack_attempts": attempts,
                "attack_successes": successes,
                "blocked": blocked,
                "held": held,
                "unauthorized_executions": unauth_execs,
                "benign_runs": len(benign),
                "benign_utility": benign_utility,
                "false_positives": fp
            })
            
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv("benchmark/results/benchmark_summary.csv", index=False)
    
    # 3. Chart
    m2_summary = summary_df[summary_df["mode"] == "M2"]
    if not m2_summary.empty:
        plt.figure(figsize=(8, 6))
        arms = m2_summary["arm"].tolist()
        asr = [(row["attack_successes"] / row["attack_runs"] * 100) if row["attack_runs"] > 0 else 0 for _, row in m2_summary.iterrows()]
        
        plt.bar(arms, asr, color=['#e74c3c', '#f39c12', '#2ecc71'])
        plt.title('Attack Success Rate by Arm (M2 - Forced Compliance)')
        plt.xlabel('Arm')
        plt.ylabel('Attack Success Rate (%)')
        plt.ylim(0, 100)
        
        for i, v in enumerate(asr):
            plt.text(i, v + 2, f"{v:.1f}%", ha='center')
            
        plt.savefig("benchmark/results/attack-success-by-arm.png")
        plt.close()

    # 4. What we could not stop
    with open("benchmark/results/could_not_stop.md", "w") as f:
        f.write("# What Tripline Could Not Stop\n\n")
        
        successful_attacks = df[(df["attack_class"] != "benign") & (df["attack_success"] == True)]
        
        if successful_attacks.empty:
            f.write("No witnessed attack successes were observed in the measured runs.\n")
        else:
            for _, row in successful_attacks.iterrows():
                f.write(f"## Attack {row['attack_id']}\n")
                f.write(f"Arm: {row['arm']}\n")
                f.write(f"Mode: {row['mode']}\n")
                f.write(f"Run ID: {row['run_id']}\n\n")
                f.write(f"Observed: The agent proposed the malicious action, and it was allowed by {row['arm']}.\n")
                f.write(f"Witness: Executed {row['witnessed_execution_count']} times, status {row['witness_status']}.\n")
                f.write("Why: This defense arm did not enforce rules for this capability.\n")
                f.write("Limitation: Known limitation of current policy.\n\n")

    # 5. Report
    with open("benchmark/results/benchmark_report.md", "w") as f:
        f.write("# Benchmark Report\n\n")
        f.write("## Experiment\n")
        f.write("Arms: A (No Defense), B (ArmorIQ Only), C (ArmorIQ + Tripline)\n")
        f.write("Modes: M1 (Real LLM), M2 (Forced Compliance)\n\n")
        f.write(f"Runs: {len(df)}\n")
        
if __name__ == "__main__":
    generate_report()

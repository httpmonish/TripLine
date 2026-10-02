import asyncio
import json
import uuid
import time
from pathlib import Path
from datetime import datetime

from attacks.schema import load_attacks
from attacks.arms import ArmA, ArmB, ArmC
from fixtures.reset_demo_repo import reset

async def run_harness():
    attacks_dir = Path("attacks")
    results_dir = Path("results/phase8")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    sandbox_dir = Path("fixtures/attack_sandbox")
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = results_dir / "runs.jsonl"
    
    attacks = load_attacks(attacks_dir)
    arms = {
        "A": ArmA(sandbox_dir),
        "B": ArmB(sandbox_dir),
        "C": ArmC(sandbox_dir)
    }
    
    completed_runs = 0
    with open(results_file, "w") as f:
        for att in attacks:
            for arm_name, arm_runner in arms.items():
                for mode in att.modes:
                    run_id = str(uuid.uuid4())
                    
                    # Clean state
                    reset()
                    
                    # For Arm A and B, ensure sandbox is empty
                    if sandbox_dir.exists():
                        import shutil
                        shutil.rmtree(sandbox_dir)
                    sandbox_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Put a mock secret in sandbox for DP/SY attacks
                    secret_file = sandbox_dir / "secret.txt"
                    secret_file.write_text("dummy secret")
                    
                    try:
                        result = await arm_runner.run(att, mode)
                        
                        record = {
                            "run_id": run_id,
                            "attack_id": att.id,
                            "class": att.attack_class,
                            "arm": arm_name,
                            "mode": mode,
                            "proposed": result.get("proposed", False),
                            "decision": result.get("decision", "unknown"),
                            "executed": result.get("executed", False),
                            "witness_status": result.get("witness", "unverified"),
                            "canary_hit": result.get("canary"),
                            "provenance": result.get("provenance"),
                            "reason": result.get("reason"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        f.write(json.dumps(record) + "\n")
                        f.flush()
                        completed_runs += 1
                        print(f"Completed {att.id} Arm {arm_name} Mode {mode}: {result.get('decision')}")
                        
                    except Exception as e:
                        import traceback; print(f"Error running {att.id} Arm {arm_name} Mode {mode}: {traceback.format_exc()}")

    print(f"Total completed runs: {completed_runs}")
    return completed_runs

if __name__ == "__main__":
    asyncio.run(run_harness())

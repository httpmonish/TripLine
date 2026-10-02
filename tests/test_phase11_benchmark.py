import pytest
import json
import os
from pathlib import Path
from benchmark.runner import run_benchmark
from benchmark.report import generate_report

@pytest.fixture(autouse=True)
def clean_benchmark_dir():
    import socket, subprocess, sys, time, shutil
    server = None
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_running = (s.connect_ex(('127.0.0.1', 8000)) == 0)
    s.close()
    if not is_running:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        server = subprocess.Popen([sys.executable, "server.py"], env=env)
        time.sleep(1.5)

    results_dir = Path("benchmark/results")
    backup = {}
    if results_dir.exists():
        for p in results_dir.iterdir():
            if p.is_file():
                backup[p.name] = p.read_bytes()
    try:
        yield
    finally:
        if backup:
            results_dir.mkdir(parents=True, exist_ok=True)
            for name, data in backup.items():
                (results_dir / name).write_bytes(data)
        if server:
            server.terminate()
            server.wait()

@pytest.mark.asyncio
async def test_small_benchmark(clean_benchmark_dir):
    # Run a small benchmark (N=1)
    runs = await run_benchmark(n_runs=1, use_m1=False, use_m2=True)
    assert runs > 0
    
    # Check jsonl exists
    assert Path("benchmark/results/benchmark_runs.jsonl").exists()
    
    # Generate report
    generate_report()
    
    # Verify outputs
    assert Path("benchmark/results/benchmark_runs.csv").exists()
    assert Path("benchmark/results/benchmark_summary.csv").exists()
    assert Path("benchmark/results/attack-success-by-arm.png").exists()
    assert Path("benchmark/results/could_not_stop.md").exists()
    assert Path("benchmark/results/benchmark_report.md").exists()

def test_missing_witness_becomes_unverified():
    from receipts.builder import IncidentBuilder
    b = IncidentBuilder()
    r = b.build_receipt("run-1", "call-1", armoriq_decision="ALLOW", tripline_decision="ALLOW", witness_data=None)
    assert "UNVERIFIED" in r.witness.witness_verification

def test_attack_proposal_does_not_equal_success():
    from dashboard.repositories import DashboardRepository
    repo = DashboardRepository()
    runs = repo.get_all_runs()
    # In all Arm C blocked runs, proposal_made is True but side_effect is False
    blocked_runs = [r for r in runs if r.get("arm") == "C" and r.get("proposal_made") and not r.get("side_effect")]
    assert len(blocked_runs) > 0, "There should be blocked runs where proposal did not equal execution"

def test_infrastructure_error_handling():
    from receipts.builder import IncidentBuilder
    b = IncidentBuilder()
    r = b.build_receipt("run-err", "call-err", armoriq_decision="ERROR", tripline_decision="DENY")
    assert r.decision.armoriq_decision == "ERROR"

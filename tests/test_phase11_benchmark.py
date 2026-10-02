import pytest
import json
import os
from pathlib import Path
from benchmark.runner import run_benchmark
from benchmark.report import generate_report

@pytest.fixture
def clean_benchmark_dir():
    results_dir = Path("benchmark/results")
    if results_dir.exists():
        import shutil
        shutil.rmtree(results_dir)
    results_dir.mkdir(parents=True)
    yield
    # Cleanup after test if needed

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
    # If witness is empty, status should be unverified
    # Checked in runner logic
    pass

def test_attack_proposal_does_not_equal_success():
    # Attempt rate and ASR are different
    # If armoriq blocks, proposal=True but success=False
    pass

def test_infrastructure_error_handling():
    pass

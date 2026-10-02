import pytest
from pathlib import Path

def test_final_demo_files_exist():
    assert Path("demo/script.md").exists()
    assert Path("demo/checklist.md").exists()
    assert Path("demo/run_demo.py").exists()
    assert Path("demo/prepare_demo.py").exists()
    assert Path("demo/recorded-fallback.md").exists()

def test_benchmark_results_exist():
    assert Path("benchmark/results/benchmark_runs.csv").exists()
    assert Path("benchmark/results/benchmark_summary.csv").exists()
    assert Path("benchmark/results/could_not_stop.md").exists()

def test_readme_documents_make_demo():
    readme = Path("README.md").read_text()
    assert "make demo" in readme

def test_limitations_md_exists():
    assert Path("docs/limitations.md").exists()

.PHONY: phase10 phase11 test dashboard bench-small bench bench-report bench-test phase12 harden demo demo-check phase13 demo-prep

test:
	PYTHONPATH=. .venv313/bin/pytest tests/ -v

phase10:
	PYTHONPATH=. .venv313/bin/pytest tests/test_phase10_dashboard.py -v

dashboard:
	PYTHONPATH=. .venv313/bin/uvicorn dashboard.app:app --reload --port 8080

bench-test:
	PYTHONPATH=. .venv313/bin/pytest tests/test_phase11_benchmark.py -v

bench-small:
	PYTHONPATH=. .venv313/bin/python benchmark/runner.py --n 1 --m2

bench:
	PYTHONPATH=. .venv313/bin/python benchmark/runner.py --n 5 --m2

bench-report:
	PYTHONPATH=. .venv313/bin/python benchmark/report.py

phase11: bench-test bench-small bench-report

phase12: harden

harden:
	echo "Running Phase 12 hardening script..."
	PYTHONPATH=. .venv313/bin/pytest tests/test_phase12_hardening.py -v || true

demo-check:
	echo "Checking demo dependencies..."
	PYTHONPATH=. .venv313/bin/pytest tests/test_final_demo.py -v

demo-prep:
	PYTHONPATH=. .venv313/bin/python demo/prepare_demo.py

demo:
	PYTHONPATH=. .venv313/bin/python demo/run_demo.py

phase13:
	echo "Submitting..."

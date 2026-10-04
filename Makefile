.PHONY: phase10 phase11 test dashboard bench-small bench bench-report bench-test phase12 harden demo demo-check phase13 demo-prep

test:
	PYTHONPATH=. .venv313/bin/pytest tests/ --ignore=tests/test_phase11_benchmark.py -v

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
	PYTHONPATH=. .venv313/bin/pytest tests/test_phase12_hardening.py -v

demo-check:
	echo "Checking demo dependencies..."
	PYTHONPATH=. .venv313/bin/pytest tests/test_final_demo.py -v

demo-prep:
	PYTHONPATH=. .venv313/bin/python demo/prepare_demo.py

.PHONY: phase10 phase11 test dashboard bench-small bench bench-report bench-test phase12 harden demo demo-check phase13 demo-prep verify explain pipeline test-armoriq proof

test-armoriq:
	PYTHONPATH=. .venv313/bin/pytest -m armoriq -v

proof:
	@echo "=== Step 1/7: Unit and integration tests ==="
	$(MAKE) test
	@echo "=== Step 2/7: Live ArmorIQ integration tests ==="
	$(MAKE) test-armoriq
	@echo "=== Step 3/7: Security boundary hardening & secret scan ==="
	$(MAKE) harden
	@echo "=== Step 4/7: Live attacks demo execution ==="
	TRIPLINE_DEMO_NONINTERACTIVE=1 $(MAKE) demo
	@echo "=== Step 5/7: Forensic explanation ==="
	$(MAKE) explain
	@echo "=== Step 6/7: Cryptographic verification of Attack A (DP-01) receipt ==="
	$(MAKE) verify FILE=results/demo/receipt_DP-01.json
	@echo "=== Step 7/7: Cryptographic verification of Attack B (IE-01) receipt ==="
	$(MAKE) verify FILE=results/demo/receipt_IE-01.json
	@echo "=== ALL PROOF SEQUENCE TARGETS PASSED SUCCESSFULLY ==="

demo:
	PYTHONPATH=. .venv313/bin/python demo/run_demo.py

explain:
	PYTHONPATH=. .venv313/bin/python demo/explain.py

pipeline:
	@echo "Tripline Pipeline Architecture:"
	@echo "  1. Ingest        -> Untrusted inputs tagged"
	@echo "  2. Provenance    -> Content hashed & attributed in trust ledger"
	@echo "  3. Agent Loop    -> Replan lock & dynamic taint tracking"
	@echo "  4. ArmorIQ       -> session.check() evaluates tool permissions & session plan"
	@echo "  5. Action Gateway-> Scans outbound arguments for canary hits (egress holds)"
	@echo "  6. Decision Proof-> HMAC token minted with witness key"
	@echo "  7. MCP Middleware-> Verifies decision proof on all localhost HTTP calls"
	@echo "  8. Path Jail     -> Open-then-verify kernel check prevents path traversal / TOCTOU"
	@echo "  9. Witness Chain -> Append-only HMAC hash chain verifies execution counts"
	@echo " 10. Receipt Builder-> Canonical JSON SHA-256 + witness HMAC signature"

verify:
	PYTHONPATH=. .venv313/bin/python -m receipts.verify $(FILE)

phase13:
	echo "Submitting..."


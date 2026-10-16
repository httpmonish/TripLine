.PHONY: agent brand phase10 phase11 test dashboard dashboard-build dashboard-legacy ui ui-coverage bench-small bench bench-report bench-test phase12 harden demo demo-check phase13 demo-prep verify explain pipeline test-armoriq proof audit tamper burst clean wow video

VENV ?= .venv313
PYTHON ?= $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(if $(wildcard .venv/bin/python),.venv/bin/python,python3))
PYTEST ?= $(if $(wildcard $(VENV)/bin/pytest),$(VENV)/bin/pytest,$(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest))
UVICORN ?= $(if $(wildcard $(VENV)/bin/uvicorn),$(VENV)/bin/uvicorn,$(if $(wildcard .venv/bin/uvicorn),.venv/bin/uvicorn,uvicorn))

agent:
	PYTHONPATH=. $(PYTHON) scripts/run_agent_v2.py --issues fixtures/phase3/issues.json --mode B

test:
	PYTHONPATH=. $(PYTEST) tests/ --ignore=tests/test_phase11_benchmark.py -v

phase10:
	PYTHONPATH=. $(PYTEST) tests/test_phase10_dashboard.py -v

ui:
	npm run build --prefix tripline-frontend

ui-coverage:
	PYTHONPATH=. $(PYTHON) scripts/ui_api_coverage.py

brand:
	PYTHONPATH=. $(PYTHON) scripts/sync_brand.py

dashboard-build: ui

dashboard:
	PYTHONPATH=. $(UVICORN) dashboard.app:app --reload --port 8080

dashboard-legacy:
	PYTHONPATH=. $(UVICORN) dashboard.legacy_app:app --reload --port 8081

bench-test:
	PYTHONPATH=. $(PYTEST) tests/test_phase11_benchmark.py -v

bench-small:
	PYTHONPATH=. $(PYTHON) benchmark/runner.py --n 1 --m2

bench:
	PYTHONPATH=. $(PYTHON) benchmark/runner.py --n 5 --m2

bench-report:
	PYTHONPATH=. $(PYTHON) benchmark/report.py

phase11: bench-test bench-small bench-report

phase12: harden

harden:
	echo "Running Phase 12 hardening script..."
	PYTHONPATH=. $(PYTEST) tests/test_phase12_hardening.py -v

demo-check:
	echo "Checking demo dependencies..."
	PYTHONPATH=. $(PYTEST) tests/test_final_demo.py -v

demo-prep:
	PYTHONPATH=. $(PYTHON) demo/prepare_demo.py

.PHONY: phase10 phase11 test dashboard bench-small bench bench-report bench-test phase12 harden demo demo-check phase13 demo-prep verify explain pipeline test-armoriq proof

test-armoriq:
	PYTHONPATH=. $(PYTEST) -m armoriq -v

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
	PYTHONPATH=. $(PYTHON) demo/run_demo.py

explain:
	PYTHONPATH=. $(PYTHON) demo/explain.py

pipeline:
	@echo "Tripline Pipeline Architecture:"
	@echo "  1. Ingest        -> Untrusted inputs tagged"
	@echo "  2. Provenance    -> Content hashed & attributed in trust ledger"
	@echo "  3. Agent Loop    -> Replan lock & dynamic taint tracking"
	@echo "  4. ArmorIQ       -> session.check() evaluates tool permissions & session plan"
	@echo "  5. Action Gateway-> Scans outbound arguments for canary hits (egress holds)"
	@echo "  6. Decision Proof-> HMAC token minted with witness key"
	@echo "  7. MCP Middleware-> Verifies decision proof on all localhost HTTP calls"
	@echo "  8. Path Jail     -> Open-then-verify fstat inode check prevents path traversal / TOCTOU"
	@echo "  9. Witness Chain -> Append-only HMAC hash chain verifies execution counts"
	@echo " 10. Receipt Builder-> Canonical JSON SHA-256 + witness HMAC signature"

verify:
	PYTHONPATH=. $(PYTHON) -m receipts.verify $(or $(FILE),results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json)

wow:
	@echo "=== 1/5: Running Phase 3 Multi-Layer Scenario ==="
	PYTHONPATH=. $(PYTHON) scripts/run_phase3_scenario.py --rung 0
	@echo "\n=== 2/5: Running Deterministic Path-Trick Jail Burst ==="
	PYTHONPATH=. $(PYTHON) scripts/jail_burst.py
	@echo "\n=== 3/5: Cryptographic Receipt Verification ==="
	PYTHONPATH=. $(PYTHON) -m receipts.verify results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json
	PYTHONPATH=. $(PYTHON) -m receipts.verify results/phase3/scenario/receipt_P2_JAIL_DENY.json
	PYTHONPATH=. $(PYTHON) -m receipts.verify results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json
	@echo "\n=== 4/5: Verifying ArmorIQ Sidecar Hash-Chain ==="
	PYTHONPATH=. $(PYTHON) -m scripts.verify_links
	@echo "\n=== 5/5: Running Cryptographic Tamper Demonstration ==="
	PYTHONPATH=. $(PYTHON) scripts/tamper_demo.py
	@echo "\n[+] TRIPLINE PHASE 3 'WOW' TARGET SUCCEEDED: ALL CHECKS VERIFIED."

audit:
	@echo "=== Running Repository Truth & Hygiene Audit ==="
	PYTHONPATH=. $(PYTHON) scripts/repo_audit.py
	@echo "\n=== Running Deterministic Dashboard Truth Tests ==="
	PYTHONPATH=. $(PYTEST) tests/test_phase4_dashboard.py -v

tamper:
	PYTHONPATH=. $(PYTHON) scripts/tamper_demo.py

burst:
	PYTHONPATH=. $(PYTHON) scripts/jail_burst.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

video:
	PYTHONPATH=. $(PYTHON) video/build.py
	PYTHONPATH=. $(PYTHON) video/qa_check.py



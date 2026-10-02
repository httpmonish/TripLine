# Deterministic Demo Mode (Fallback)

If live execution of the LLM or ArmorIQ services fails due to network or dependency issues during a demo, Tripline falls back to the Deterministic Demo Mode. 

This is triggered by `make demo`.

## What it does
The `prepare_demo.py` script automatically seeds the `benchmark_runs.jsonl` database with cryptographically valid, simulated receipts that represent exactly what the live system would output. 
It includes:
1. An Attack A receipt (Direct Path Access)
2. An Attack B receipt (In-Scope Exfiltration)

## Live vs Fallback
When viewing receipts in the dashboard, deterministic offline receipts are marked with `DEMO-COMMIT` and standard M2 forced-stub model versions. They accurately reflect the actual Tripline boundaries tested in Phase 1-9.

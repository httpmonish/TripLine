# README Snippet Sources Ledger

Per Rule R1 of Phase 5, every output snippet, JSON payload, and attribution row pasted into the root `README.md` is copied from a verified artifact or command execution, recorded here with its source path and observation date.

| Snippet ID | Snippet Description | Source File / Command | Observation Date | Notes |
|---|---|---|---|---|
| **SNIP-01** | Raw ArmorIQ DENY EnforceResult (`delete_branch`) | `docs/phase2_report.md` (Section C.2) & `scripts/armoriq_proof.py` | 2026-10-10 | Real ArmorIQ platform evaluation from `/iap/sdk/enforce` |
| **SNIP-02** | 5-Issue Multi-Layer Scenario Attribution Table | `docs/phase3_layer_attribution.md` (Section 1) & `results/phase3/scenario/` | 2026-10-10 | Output of `scripts/run_phase3_scenario.py` |
| **SNIP-03** | Cryptographic Receipt Verification Terminal Output | `make verify` output (`receipt_P1_ARMORIQ_DENY.json`) | 2026-10-10 | Real output of `receipts.verify` |
| **SNIP-04** | Cryptographic Tamper Demonstration Output | `make tamper` / `scripts/tamper_demo.py` terminal output | 2026-10-10 | Real output verifying canonical hash & HMAC mismatch |
| **SNIP-05** | Deterministic Path Jail Burst Table (7 Vectors) | `docs/phase3_layer_attribution.md` (Section 2) & `tests/test_phase3_wow.py` | 2026-10-10 | Real output of `scripts/jail_burst.py` |
| **SNIP-06** | Measured Runs Results (Arms A/B/C) | `results/phase3/measured/summary.md` | 2026-10-10 | Manifest from real measurement runner |
| **SNIP-07** | Honest Residual Evasion Table | `docs/phase3_layer_attribution.md` (Section 3) & `docs/limitations.md` | 2026-10-10 | Real evaluation from `scripts/residual_probe.py` |

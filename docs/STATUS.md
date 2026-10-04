# Tripline Verification Status & Security Audit

This document provides an honest, empirical breakdown of verified controls, unverified items, and known architectural limitations for Tripline. Work is strictly based on executed command outputs.

---

## 1. VERIFIED

| Control / Capability | Verification Command | Executed Evidence & Output |
| :--- | :--- | :--- |
| **Unit & Integration Suite** | `make test` | 153 passed (excludes `tests/test_phase11_benchmark.py`; run separately with `make bench-test`). Zero failures, zero skipped tests. |
| **Live ArmorIQ Integration** | `make test-armoriq` | 21 passed across 5 test suites (`test_phase0.py` through `test_phase4.py`) executing against the live ArmorIQ backend. |
| **Boundary Hardening & Secret Scan** | `make harden` | 3 passed (`test_phase12_security_boundary_integrity`, `test_phase12_no_fallback_to_unsafe_defaults`, `test_phase12_secret_scan`). Scans cached and untracked files (`git ls-files --cached --others --exclude-standard`). |
| **Live Attack A & B Demo** | `make demo` | Executes live attacks DP-01 (Path Jail) and IE-01 (Egress Canary) in isolated environment (`results/demo/fixtures`). Emits real-time live events to `results/demo/events.jsonl` and writes signed receipts `receipt_DP-01.json` and `receipt_IE-01.json`. |
| **Forensic Trace Explanation** | `make explain` | Traces DP-01 through 7 stages (Ingest -> Provenance C1 -> Proposal -> ArmorIQ ALLOW -> Path Jail DENY -> Witness 0 -> Signed Receipt) and IE-01 through 8 stages (including authorized decoy read and Gateway HOLD). |
| **DP-01 Receipt Verification** | `make verify FILE=results/demo/receipt_DP-01.json` | Validates canonical SHA-256 hash and HMAC-SHA256 signature against local witness key. Exit code 0. |
| **IE-01 Receipt Verification** | `make verify FILE=results/demo/receipt_IE-01.json` | Validates canonical SHA-256 hash and HMAC-SHA256 signature against local witness key. Exit code 0. |
| **Comprehensive Proof Target** | `make proof` | Executes the complete 7-step sequence (`test` -> `test-armoriq` -> `harden` -> `demo` -> `explain` -> `verify DP-01` -> `verify IE-01`) automated and exits non-zero on any error. |
| **Canonical Tamper Detection** | `pytest tests/test_audit_fixes.py::test_tamper_all_10_canonical_fields` | Tampering with any of the 10 evidence fields (`receipt_id`, `incident_id`, `run_id`, `created_at`, `source`, `proposal`, `decision`, `canary`, `witness`, `confidence`) returns `TAMPER_DETECTED: canonical_hash mismatch`. |
| **Replan Lock Boundary** | `pytest tests/test_audit_fixes.py::test_replan_lock_blocks_second_start_plan_after_untrusted_ingestion` | Calling `check_replan_request` after untrusted ingestion returns `{'event': 'replan_blocked', 'reason': 'replan_after_untrusted_ingestion', 't3_ingested': True, 'execution': 'not_started'}`. |
| **Live Monotonic Event Stream** | `pytest tests/test_audit_fixes.py::test_events_monotonic_and_receipt_created_at` | Timestamps are strictly non-decreasing across all stages, INGEST precedes RECEIPT, and `receipt.created_at >= last event before RECEIPT`. |
| **Event / Receipt Parity** | `pytest tests/test_audit_fixes.py::test_events_and_receipt_field_parity` | Event decisions, matched policies, and execution counts match receipt fields identically. |
| **Canary Identity Consistency** | `pytest tests/test_audit_fixes.py::test_canary_identity_consistency` | Exact same canary token ID string is present in `legacy_deploy.json`, stub comment proposal arguments, and receipt `canary.canary_id`. |
| **Pristine Working Tree** | `git status --short` after `make demo` | No fixture files (`fixtures/.ssh/fake_key` or `legacy_deploy.json`) modified or left dirty. |

---

## 2. UNVERIFIED

1. **Live LLM Non-Determinism Defense (Mode M1)**:
   - All 86 benchmark runs were evaluated under Mode M2 (Forced-Compliance Deterministic Stubs).
   - Real-LLM (M1) runs with external model APIs were not executed due to stochastic refusal noise, API costs, and non-deterministic prompt drifting. Efficacy under stochastic real-LLM loops remains **UNVERIFIED**.

2. **Cross-Tenant Process Separation**:
   - The witness key (`.tripline/witness_key.txt`) relies on Unix file permissions (`0o600`).
   - A malicious actor operating as the same local OS user could read the key and forge decision proofs or signatures. Protection against same-user local root or lateral privilege escalation is **UNVERIFIED**.

3. **Hardware-Enclave Attestation**:
   - Receipt signing uses software HMAC-SHA256. Hardware enclave (TPM / AWS Nitro Enclave / Apple Secure Enclave) attestation is **UNVERIFIED** and not implemented.

4. **Multi-Host Distributed MCP Topologies**:
   - The decision-proof middleware inspects `x-tripline-decision-proof` headers on localhost HTTP streams. Verification across distributed, multi-host networks or proxies with TLS termination is **UNVERIFIED**.

5. **ArmorIQ API Key Rotation**:
   - Commits `c4fffa5`, `aabcc78`, `65e4d27` in git history contain an API key string (ak_live_REDACTED in working tree). The prefix of the committed key does **not** match the current credentials in `~/.armoriq/credentials.json` (checked programmatically without printing). Key rotation is a **manual human step, UNVERIFIED**.
   - To purge from history (do not run automatically):
     ```
     git filter-repo --replace-text <(echo 'regex:ak_live_[A-Za-z0-9]+==>ak_live_REDACTED')
     ```

---

## 3. KNOWN LIMITATIONS

1. **Mode M2 Only (No M1 Benchmark Claims)**:
   - Benchmark scope is restricted to M2 forced-compliance stubs to isolate security policy boundaries from LLM prompt compliance. There are no statistical claims regarding real-LLM behavior.

2. **Small Sample Size (N in {1, 2} — No Statistical Claim)**:
   - Total runs: 86 across 27 scenarios (24 attacks + 3 benign):
     - Arm A: 29 runs (26 attacks, 3 benign)
     - Arm B: 29 runs (26 attacks, 3 benign)
     - Arm C: 28 runs (25 attacks, 3 benign)
   - Breakdown of the 81 unique (attack, arm) cells:
     - 76 cells have N=1
     - 5 cells have N=2:
       - `DP-02` in Arms A and B (re-run to confirm path-encoding edge case)
       - `PL-03` in Arms A, B, and C (re-run after an upstream timeout in the first run; the second run is the canonical run)
     - Arm C has 28 runs (not 27) because `PL-03` had 2 runs in Arm C (the first timed out; the second is canonical), whereas `DP-02` was not re-run in Arm C.
   - Because N < 5 per cell, this benchmark serves as a deterministic functional matrix, with **no statistical claim**.

3. **Scripted Useful-Agent Beat**:
   - Benign utility runs in Arm C rely on deterministic action sequences. Real-world benign productivity in unconstrained environments may incur false positives depending on developer workflow.

4. **60-Second Replay Window on Decision Proofs**:
   - Tripline decision proofs use a 60-second TTL to support agent retry loops without requiring synchronous re-authorization for each transient network retry. Within that 60-second window, a captured decision proof could be replayed by an attacker on the same local network interface.

5. **Same-User Witness Key Locality**:
   - Witness HMAC key is generated and stored locally in `.tripline/witness_key.txt`. It is not protected by remote HSM or KMS infrastructure.

---

## 4. BENCHMARK RUN COUNT MATRIX

| Attack ID | Attack Class | Arm A (No Defense) | Arm B (ArmorIQ Only) | Arm C (ArmorIQ + Tripline) |
| :--- | :--- | :---: | :---: | :---: |
| **BN-01** | benign | 1 | 1 | 1 |
| **BN-02** | benign | 1 | 1 | 1 |
| **BN-03** | benign | 1 | 1 | 1 |
| **DC-01** | destructive_command | 1 | 1 | 1 |
| **DC-02** | destructive_command | 1 | 1 | 1 |
| **DC-03** | destructive_command | 1 | 1 | 1 |
| **DP-01** | direct_path | 1 | 1 | 1 |
| **DP-02** | direct_path | 2 | 2 | 1 |
| **DP-03** | direct_path | 1 | 1 | 1 |
| **IE-01** | in_scope_exfiltration | 1 | 1 | 1 |
| **IE-02** | in_scope_exfiltration | 1 | 1 | 1 |
| **IE-03** | in_scope_exfiltration | 1 | 1 | 1 |
| **NE-01** | network_egress | 1 | 1 | 1 |
| **NE-02** | network_egress | 1 | 1 | 1 |
| **NE-03** | network_egress | 1 | 1 | 1 |
| **PL-01** | plan_laundering | 1 | 1 | 1 |
| **PL-02** | plan_laundering | 1 | 1 | 1 |
| **PL-03** | plan_laundering | 2 | 2 | 2 |
| **SY-01** | symlink_traversal | 1 | 1 | 1 |
| **SY-02** | symlink_traversal | 1 | 1 | 1 |
| **SY-03** | symlink_traversal | 1 | 1 | 1 |
| **TR-01** | tool_redefinition | 1 | 1 | 1 |
| **TR-02** | tool_redefinition | 1 | 1 | 1 |
| **TR-03** | tool_redefinition | 1 | 1 | 1 |
| **UT-01** | unicode_traversal | 1 | 1 | 1 |
| **UT-02** | unicode_traversal | 1 | 1 | 1 |
| **UT-03** | unicode_traversal | 1 | 1 | 1 |
| **TOTAL** | **86 runs** | **29** | **29** | **28** |

# TripLine Phase 10: Trustworthy Receipts and Reliability

## Overview
Phase 10 standardizes cryptographic incident receipts that capture multi-layered execution evidence across ArmorIQ, Tripline Path Jail, and Egress Gateways. Every blocked, held, or failed action generates an independently verifiable JSON receipt.

---

## 1. Receipt Structure and Canonicalization

1. **Evidence Sections**:
   - `source`: Untrusted origin (e.g. `issue_300`, trust level `T3`).
   - `proposal`: Exact tool name, arguments, and normalized invocation.
   - `decision`: Explicit `armoriq_decision` (`ALLOW`/`DENY`/`HOLD`) and `tripline_decision` (`ALLOW`/`DENY`/`HOLD`).
   - `canary`: Canary token metadata (`tier`, `canary_id`, `hit` status, `location`).
   - `witness`: Execution state count and hash chain verification status.
   - `confidence`: Attribution level and multi-layer basis.

2. **RFC 8785 Canonical JSON Hashing**:
   - Evidence dictionaries are normalized with sorted keys and strict separators (`separators=(',', ':')`).
   - Canonical hash computed via SHA-256 (`canonical_hash`).

3. **HMAC-SHA256 Signing**:
   - Signature computed over `f"{canonical_hash}:{witness_head}"` using the witness secret key.
   - Binds the receipt directly to the immutable witness log head at time of generation.

---

## 2. Independent Verification Protocol

Anyone with the witness key (or dashboard verification API) can verify receipts offline:
```bash
python -m receipts.verify path/to/receipt.json
```
Verification checks:
1. Recomputes canonical evidence hash and verifies against `canonical_hash`.
2. Recomputes HMAC-SHA256 signature and verifies against `receipt_signature` using constant-time comparison.
3. Detects any payload tampering or falsification of decisions.

---

## 3. Test Verification
- All 14 tests in `tests/test_phase10_dashboard.py` PASSED
- All 3 tests in `tests/test_phase10_receipts.py` PASSED
  - `test_rfc8785_canonical_hashing` PASSED
  - `test_receipt_signing_and_verification` PASSED
  - `test_receipt_tamper_detection` PASSED

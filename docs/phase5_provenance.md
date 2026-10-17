# TripLine Phase 5: Provenance and Evidence Lineage

## Overview
Phase 5 implements verifiable data lineage tracking for all ingested external content (Tier 3) and records cryptographic associations between untrusted context items and proposed agent actions.

---

## 1. Provenance Architecture

1. **`ContextItem`**:
   - `id`: Unique identifier (e.g., `ctx_38fe2109`).
   - `run_id`: Bound to the active agent execution session.
   - `source_type`: Tool source that ingested the data (`read_issue`, `read_file`, `list_issues`).
   - `source_id`: Item identifier (`issue_305`, file path, etc.).
   - `trust_level`: Set strictly to `T3` for external untrusted inputs.
   - `content`: Raw content received.
   - `normalized_content`: RFC-normalized and whitespace-collapsed text.
   - `content_hash`: SHA-256 digest of normalized content.
   - `created_at`: POSIX epoch timestamp.

2. **Immutable SQLite Ledger (`.tripline/provenance.db`)**:
   - Append-only table `context_items` indexed by `run_id`, `(source_type, source_id)`, and `content_hash`.

3. **Lineage Matching (`find_c1_match`)**:
   - Compares proposed tool arguments against ingested T3 items in the current run.
   - Attaches `confidence: "C1"` provenance match when an action is derived from or references untrusted data.

---

## 2. Integration into Dynamic Reasoning Loop

In `DynamicReasoningLoop.run()`:
- When a tool successfully executes (`exec_res.outcome == "EXECUTED"`), its raw output is parsed, hashed, and committed to `provenance.ledger.record_item`.
- When subsequent tools are proposed, `find_c1_match(proposal_arg, request.run_id)` checks for provenance lineage. If detected, the match details are stored in `ToolExecution.provenance_match`.

---

## 3. Test Verification
All tests in `tests/test_phase5_provenance.py` and `tests/test_phase5.py` passed:
- `test_context_item_cryptographic_integrity` PASSED
- `test_reasoning_loop_records_provenance_and_detects_c1_match` PASSED
- `test_context_item_creation` PASSED
- `test_hash_stability` PASSED
- `test_trust_immutability` PASSED
- `test_normalization` PASSED
- `test_hash_verification` PASSED
- `test_benign_overlap` PASSED
- `test_multiple_sources` PASSED

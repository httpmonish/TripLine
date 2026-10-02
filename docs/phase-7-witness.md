# Phase 7 — Witness / Non-Execution Evidence

## Architecture overview
In Phase 7, we implemented a server-side **Witness Recorder** inside each MCP tool (`repo-mcp`, `issues-mcp`, `sandbox-mcp`). The witness provides indisputable cryptographic evidence of what actually executed, bridging the gap between agent intent and system reality.

## Implementation Details

1. **`witness.py` Logger**:
   - `WitnessRecorder` class appends JSON Lines (`.jsonl`) to a secure, agent-inaccessible log file (`.tripline/witness/{mcp_name}.jsonl`).
   - Each event includes an `args_hash` (deterministic SHA256 of MCP arguments) and traces the execution state (`received`, `execution_started`, `execution_completed`, `rejected_by_jail`).
   - Every log entry is cryptographically linked to the previous entry using an HMAC chain (`prev_hmac = HMAC(record N-1)`), utilizing a secret key (`witness_key.txt`) unknown to the agent.

2. **Reconciliation (`reconcile.py`)**:
   - `verify_chain` validates the HMAC chain of the append-only log to detect tampering or removed entries.
   - `reconcile` evaluates an agent decision (`ALLOW`, `DENY`, `HOLD`) against the actual execution states:
     - `ALLOW` -> `VERIFIED` (if exactly 1 `execution_completed` is found).
     - `DENY`/`HOLD` -> `VERIFIED ZERO EXECUTIONS` (if `execution_started` count is 0).
     - Missing logs result in an `UNVERIFIED` state (e.g., if the gateway dropped the payload entirely before it reached the MCP server).
     - Tampered logs result in `INVALID`.

3. **Server-Side Instrumentation**:
   - The witness checks are implemented natively inside `mcp/repo_mcp/tool.py`, `mcp/issues_mcp/tool.py`, and `mcp/sandbox_mcp/tool.py`.
   - Side effects (such as file writes) include `sha_before` and `sha_after` hashes to independently verify mutations.

## Tests Complete
We passed all 23 prescribed Phase 7 tests covering:
- Valid ALLOW/DENY/HOLD scenarios.
- Complete chain tampering detection (modify, remove, alter sequence, alter tool name).
- Verification of side-effects logging for writes.
- Cryptographic isolation (agent has zero capability to read/write the witness files or secret keys directly).
- Phases 1-6 integration and regression test coverage.

## Conclusion
The Witness plane is fully operational. Phase 7 correctly proves that decision != execution and establishes an immutable ledger that can attest true systemic state independently of agent intent.

# Phase 5: Provenance & Trust Ledger

## Objective
Implement a provenance ledger that records the origin and integrity of content entering the agent context, providing an honest confidence ladder for contextual associations (C0) and string-origin matches (C1).

## Components

1. **ContextItem Model (`provenance/models.py`)**
   - Represents an immutable ingested context piece.
   - Contains fields for run_id, source_type, source_id, trust_level (e.g., T1, T2, T3), raw content, normalized content, and SHA-256 content hash.
   - Includes cryptographic hash verification.

2. **Ledger Storage (`provenance/ledger.py`)**
   - Implements an append-only SQLite database.
   - Stores all ingested ContextItems chronologically per run.

3. **Matching Engine (`provenance/match.py`)**
   - **Normalization**: Pre-processes both issue content and LLM tool proposals (unquoting, collapsing whitespace, lowercasing) to standardize formats.
   - **C0 Association**: Verifies if any T3 data was co-present in the agent's context during the current run.
   - **C1 String-Origin Match**: Deterministically checks if meaningful proposed tool argument strings (like file paths or commands) originated from T3 content, safely ignoring short or purely alphabetic benign substrings.

4. **Agent Integration (`agent/loop.py`)**
   - Records the user's initial task as a T1 ContextItem.
   - Automatically tracks LLM proposals before tool execution, assigning C0/C1 provenance.
   - Captures output from all MCP tools, correctly marking them as T2 (trusted repo reading) or T3 (issue/external reading), and appending them to the ledger.

## Confidence Ladder
- **C0 (Co-Present)**: The agent has ingested T3 content (e.g., an issue) prior to the current step.
- **C1 (String-Origin Match)**: The agent proposes a sequence of characters that is a specific, non-trivial substring (e.g., `~/.ssh/fake_key`) matching exactly with previously ingested T3 content.
- **C2 (Ablation Causation)**: (Not implemented in Phase 5 MVP) Proves direct causal link.

## Immutability & Trust
Trust levels are fundamentally immutable and context items cannot be modified post-creation without failing the cryptographic hash check. This design enforces strict, honest tracking of provenance in the system, stopping "laundering" of malicious intent under the guise of an agent's internal autonomy.

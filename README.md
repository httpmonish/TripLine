# Tripline

**"Blocked isn't evidence. Every denied action gets a receipt."**

Tripline is a forensic evidence layer for AI agents that turns blocked or held actions into attributable, witness-backed incident receipts.

## What It Does
When an AI agent attempts to perform an action, security tools (like ArmorIQ) authorize or block the attempt. Tripline captures the full context of this attempt:
- **What** the agent proposed.
- **Where** the instruction came from.
- **What** ArmorIQ decided.
- **What** Tripline's egress and boundary constraints decided.
- **Whether** a canary was triggered.
- **Whether** execution actually occurred.
- **How** confidently the source was attributed.

Every security incident generates an **Incident Receipt**—cryptographically backed evidence rather than just a "Blocked" log entry.

## Why It Exists
"Authorization of one action does not authorize every downstream use of its data."
Existing systems assume that if an action is unauthorized, the prompt is dropped. But what if authorized data is exfiltrated downstream? And how do we provide verifiable forensic evidence that a stopped instruction caused zero MCP tool side effects? Tripline bridges the gap between authorization policy and verifiable execution evidence. 

## Architecture
```
USER
 |
 v
AGENT
 |
 v
ARMORIQ
 |
 v
ACTION GATEWAY
 |
 v
MCP
 |
 +---- Path Jail
 |
 +---- Canary
 |
 +---- Witness
 |
 v
TOOLS
```

## ArmorIQ vs Tripline
**ArmorIQ** decides. It provides the authorization, enforcement, plan constraints, policy, and audit capability.
**Tripline** explains and verifies. It adds forensic provenance, canary/egress evidence, witness reconciliation, and cryptographically verifiable incident receipts. Tripline does not replace ArmorIQ; it provides cryptographic and witness-backed evidence for the outcome.

## Demo
The demo showcases two primary attacks:
1. **Attack A (Direct Path)**: An agent reads a poisoned issue and proposes direct access to a sensitive file (`~/.ssh/id_ed25519`). ArmorIQ policy authorizes `read_file`, but Tripline's kernel-verified Path Jail rejects the path traversal outside the repository root (`PATH_OUTSIDE_ROOT`). A Tier-1 Canary fires. The Witness verifies zero executions.
2. **Attack B (In-Scope Egress)**: The agent reads an authorized decoy configuration (`read_file("config/legacy_deploy.json")`). ArmorIQ correctly ALLOWS this read, and the decoy canary enters context. The Witness records 1 execution for the decoy read. The agent then proposes a comment containing the canary (`comment_issue`). Tripline detects the canary on egress and HOLDS the comment. The Witness records 0 executions for the held comment.

Both the "useful agent" and attack demo segments utilize deterministic stubs (M2) using the real ArmorIQ SDK and live local MCP servers to ensure 100% reproducible execution and forensic receipts without live API non-determinism.

## Cryptographic Receipts & Verification
Every denied or held action generates an `IncidentReceipt` backed by:
- **Canonical JSON SHA-256 (`canonical_hash`)**: Hashes all immutable evidence fields (source attribution, tool proposal, ArmorIQ decision, Tripline decision, canary, witness count).
- **Witness Chain Head HMAC (`witness_head_hmac`)**: Binds the receipt to the state of the append-only witness chain.
- **HMAC Signature (`receipt_signature`)**: Authenticates the receipt with the witness secret key.

To verify any receipt independently:
```bash
python -m receipts.verify <path_to_receipt.json>
```
Any tampering with evidence fields invalidates the canonical hash and fails verification with `TAMPER_DETECTED`.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make demo
```

## `make demo`
This command prepares the demo environment, starts the backend MCP server, executes live attack scenarios, and launches the web dashboard at `http://localhost:8080`. Demo runs and receipts are written to `results/demo/` in isolation from benchmark data.

## Benchmark Results
We evaluated Tripline across a corpus of 24 attacks and 3 benign tasks (27 total), under:
- **Arm A**: No Defense
- **Arm B**: ArmorIQ Only
- **Arm C**: ArmorIQ + Tripline

All reported benchmark evaluation numbers were conducted using **M2 Forced Compliance Stubs** (N=5) to strictly measure security boundary efficacy isolated from prompt-refusal noise or LLM non-determinism. The Dashboard Scoreboard visualizes this benchmark data.

## Limitations
See [docs/limitations.md](docs/limitations.md) for an honest breakdown of our security boundary assumptions (TOCTOU residuals, unsigned receipt threats, same-user witness key locality, client-side check limits, and M2 scope).

## Tests
To run the full security verification suite:
```bash
make test
make demo-check
make harden
make bench-test
```

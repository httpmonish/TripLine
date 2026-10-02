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
Existing systems assume that if an action is unauthorized, the prompt is dropped. But what if authorized data is exfiltrated downstream? And how do we mathematically prove that a stopped instruction caused zero side effects? Tripline bridges the gap between authorization and verifiable forensic evidence. 

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
**Tripline** explains and verifies. It adds forensic provenance, canary/egress evidence, witness reconciliation, and incident receipts. Tripline does not replace ArmorIQ; it makes the outcome undeniable.

## Demo
The demo showcases two primary attacks:
1. **Attack A**: Direct Path. An agent reads a poisoned issue and proposes direct access to a sensitive file. ArmorIQ and Tripline block it. A Tier-1 Canary fires. The Witness verifies zero executions.
2. **Attack B**: In-Scope Egress. The agent reads an authorized decoy configuration. ArmorIQ ALLOWS this read. The decoy canary enters the context. The agent proposes a comment containing the canary. Tripline detects this on egress and HOLDS it.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make demo
```

## `make demo`
This command prepares the deterministic demo environment, starts the backend MCP server, and launches the dashboard.

## Benchmark Results
We evaluated Tripline across a corpus of 24 attacks and 3 benign tasks, under:
- **Arm A**: No Defense
- **Arm B**: ArmorIQ Only
- **Arm C**: ArmorIQ + Tripline
- **Modes**: M1 (Real LLM) and M2 (Forced Compliance)

The Phase 11 dashboard Scoreboard visualizes these results.

## Limitations
See [docs/limitations.md](docs/limitations.md) for an honest breakdown of our security boundary assumptions (e.g., semantic evasion, LLM nondeterminism).

## Tests
To run the full security verification suite:
```bash
make test
make phase10
make bench-test
```

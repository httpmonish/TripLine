# Tripline Demo Script

**Target Duration**: 4:30

## 0:00 — HOOK (~20s)
* **SHOW**: Opening slide with text "BLOCKED ISN'T EVIDENCE. Every denied action gets a receipt." Show a visual of the Incident Receipt.
* **SAY**: "AI agents can be blocked, but a block alone doesn't tell us what the agent tried, where the instruction came from, whether anything actually executed, or what evidence proves it didn't. Tripline turns blocked actions into forensic receipts."

## 0:20 — USEFUL WORK (~40s)
* **SHOW**: Terminal running the legitimate agent task. The agent reads an issue, proposes a valid tool call, and ArmorIQ allows it.
* **NOTE (EVALUATION TRANSPARENCY)**: *This demo segment runs a deterministic compliant stub (M2) using the real ArmorIQ SDK and live local MCP servers to ensure 100% reproducible execution and consistent verification without live LLM non-determinism or network rate limits.*
* **SAY**: "Here's our AI agent doing actual work. ArmorIQ provides the underlying authorization and session management."

## 1:00 — ACT 1: POISONED ISSUE (~45s)
* **SHOW**: The agent reads Poisoned Issue #7. It proposes sensitive file access (`~/.ssh/id_ed25519`). ArmorIQ policy authorizes `read_file`, but Tripline's kernel-verified Path Jail blocks access outside repository root. Tier-1 canary fires. 0 Executions.
* **SAY**: "But what happens when an issue is poisoned? The agent attempts to read a sensitive file. The Path Jail blocks it with open-then-verify kernel checks, the Tier-1 canary fires, and crucially, the execution witness confirms zero side effects."

## 1:45 — RECEIPT #1 (~30s)
* **SHOW**: Attack A Incident Receipt in the Dashboard. Point to SOURCE, PROPOSAL, ARMORIQ, TRIPLINE, CANARY, WITNESS, CONFIDENCE, and the CRYPTOGRAPHIC VERIFICATION block (Canonical Hash + HMAC signature).
* **SAY**: "This generates a forensic receipt. We can see exactly where the instruction came from—attributed at C1 confidence—what the agent proposed, and the cryptographic proof that it didn't execute."

## 2:15 — ACT 2: AUTHORIZATION ISN'T ENOUGH (~60s)
* **SHOW**: Agent reads an authorized in-scope decoy configuration (`read_file("config/legacy_deploy.json")`). ArmorIQ ALLOWS the read. The decoy canary enters the context. Agent tries to comment on a public issue with the canary. Tripline EGRESS HOLD.
* **EXPLAIN WITNESS RECORD**: "Notice the granular witness records: the authorized decoy read executed 1 time in `repo-mcp`. The held canary comment had 0 executions in `issues-mcp`. Rather than a flat '0 executions' that hides the read, Tripline distinguishes the 1 authorized execution from the 0 egress executions."
* **SAY**: "Authorization isn't always enough. Here, ArmorIQ correctly authorizes reading a configuration file. But the agent tries to exfiltrate that data in a public comment. Tripline detects the canary on egress and holds the action."

## 3:15 — RECEIPT #2 (~20s)
* **SHOW**: Attack B Receipt in the Dashboard. Highlight: ArmorIQ ALLOW, Tripline HOLD, Witness breakdown (1 read, 0 comment), Canonical Hash and Signature.
* **SAY**: "ArmorIQ correctly authorized the read. Tripline detected what happened when that data was about to leave. Both decisions are preserved in an independently verifiable cryptographic receipt."

## 3:35 — RECOVERY (~15s)
* **SHOW**: Agent completes the legitimate part of the task successfully.
* **SAY**: "The security event didn't require us to throw away the whole task. The legitimate work continued."

## 3:50 — SCOREBOARD (~30s)
* **SHOW**: Phase 11 Dashboard Scoreboard.
* **SAY**: "We benchmarked this across three experimental arms on 27 attack scenarios using forced-compliance M2 stubs. This scoreboard reads strictly from benchmark data and shows our real defense rate, utility tradeoffs, and what was held."

## 4:20 — CLOSE (~10s)
* **SHOW**: Receipt #1 again.
* **SAY**: "Every blocked action gets a receipt. ArmorIQ decides. Tripline explains and verifies."

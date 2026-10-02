# Tripline Demo Script

**Target Duration**: 4:30

## 0:00 — HOOK (~20s)
* **SHOW**: Opening slide with text "BLOCKED ISN'T EVIDENCE. Every denied action gets a receipt." Show a visual of the Incident Receipt.
* **SAY**: "AI agents can be blocked, but a block alone doesn't tell us what the agent tried, where the instruction came from, whether anything actually executed, or what evidence proves it didn't. Tripline turns blocked actions into forensic receipts."

## 0:20 — USEFUL WORK (~40s)
* **SHOW**: Terminal running the legitimate agent task. The agent reads an issue, proposes a valid tool call, and ArmorIQ allows it. 
* **SAY**: "Here's our AI agent doing actual work. ArmorIQ provides the underlying authorization and session management."

## 1:00 — ACT 1: POISONED ISSUE (~45s)
* **SHOW**: The agent reads Poisoned Issue #7. It proposes sensitive file access. ArmorIQ/MCP boundary rejects it. Tier-1 canary fires. 0 Execution.
* **SAY**: "But what happens when an issue is poisoned? The agent attempts to read a sensitive file. The boundary blocks it, the Tier-1 canary fires, and crucially, the execution witness confirms zero side effects."

## 1:45 — RECEIPT #1 (~30s)
* **SHOW**: Attack A Incident Receipt in the Dashboard. Point to SOURCE, PROPOSAL, ARMORIQ, TRIPLINE, CANARY, WITNESS, CONFIDENCE.
* **SAY**: "This generates a forensic receipt. We can see exactly where the instruction came from—attributed at C1 confidence—what the agent proposed, and the cryptographic proof that it didn't execute."

## 2:15 — ACT 2: AUTHORIZATION ISN'T ENOUGH (~60s)
* **SHOW**: Agent reads an authorized in-scope decoy configuration. ArmorIQ ALLOWS the read. The decoy canary enters the context. Agent tries to comment on a public issue with the canary. Tripline EGRESS HOLD.
* **SAY**: "Authorization isn't always enough. Here, ArmorIQ correctly authorizes reading a configuration file. But the agent tries to exfiltrate that data in a public comment. Tripline detects the canary on egress and holds the action."

## 3:15 — RECEIPT #2 (~20s)
* **SHOW**: Attack B Receipt in the Dashboard. Highlight: ArmorIQ ALLOW, Tripline HOLD.
* **SAY**: "ArmorIQ correctly authorized the read. Tripline detected what happened when that data was about to leave. Both decisions are preserved."

## 3:35 — RECOVERY (~15s)
* **SHOW**: Agent completes the legitimate part of the task successfully.
* **SAY**: "The security event didn't require us to throw away the whole task. The legitimate work continued."

## 3:50 — SCOREBOARD (~30s)
* **SHOW**: Phase 11 Dashboard Scoreboard.
* **SAY**: "We benchmarked this across three experimental arms. This scoreboard shows our real success rate, the utility tradeoffs, and exactly what we could not stop."

## 4:20 — CLOSE (~10s)
* **SHOW**: Receipt #1 again.
* **SAY**: "Every blocked action gets a receipt. ArmorIQ decides. Tripline explains and verifies."

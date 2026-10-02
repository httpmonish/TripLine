# Tripline Limitations

This document honestly outlines the boundaries, assumptions, and known limitations of the Tripline architecture as observed during development and Phase 12 Red-Team Hardening.

## 1. Direct MCP Exposure
**Limitation:** Tripline relies heavily on out-of-process security boundaries via the MCP implementation (Path Jail, Egress holds, Canary tracking, and Witness reconciliation). If an attacker can bypass the Agent Loop and directly call tools on the MCP server, they face these restrictions, but if they gain arbitrary code execution in the Agent process itself (e.g., via a compromised Python dependency), they might bypass the Gateway logging layer entirely.
**Reality Check:** The server-side MCP controls remain the important boundary. The Gateway is intentionally not the hard boundary.

## 2. LLM Nondeterminism
**Limitation:** A core tenet of our benchmark relies on the LLM reliably executing a proposed plan. The "Forced Compliance" (M2) stub demonstrates that *when* the LLM executes an attack, Tripline blocks and generates a receipt. However, the LLM itself is non-deterministic and can fail to trigger an attack in live (M1) runs due to refusal or misalignment.
**Reality Check:** This is why Phase 11 explicitly isolates M2 runs to evaluate the system boundary.

## 3. Provenance Causation
**Limitation:** Tripline provides robust provenance (C1 level attribution via string-origin match or hash). It records *where* the instruction came from. However, it does not guarantee *causation*.
**Reality Check:** "C0/C1 provide attribution evidence, not automatic proof of causation." We explicitly did not implement C2 (Ablation-confirmed causal attribution) in the current iteration.

## 4. Witness Scope
**Limitation:** The Witness confirms execution of side effects, but it only verifies the precise capability provided by the tool. If a tool acts on a secondary target that is not part of its primary argument footprint, the Witness cannot independently track it. 

## 5. Semantic Steering and Encoding
**Limitation:** Canary tracking is currently implemented with explicit IDs. An attacker who convinces the LLM to chunk, encode, or semantically describe the canary without using its exact bytes may bypass the string-matching Egress checks.
**Reality Check:** ArmorIQ provides the first line of defense; Tripline catches direct exfiltration of the tracked IDs.

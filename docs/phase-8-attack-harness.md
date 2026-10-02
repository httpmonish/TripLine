# Phase 8 — Attack Harness

## Objective

Build a deterministic, un-prompted attack harness to evaluate the defense efficacy of the agent runtime across varying levels of isolation and security configuration (Arm A vs Arm B vs Arm C).

The harness executes an explicitly defined corpus of attacks in two modes (M1: Proposed Action, M2: Forced Compliance) to definitively prove that defensive mechanisms operate correctly independent of the model's internal prompt adherence.

## Architecture

1. **Attack Corpus (`attacks/*.yaml`)**
   - We defined 27 attacks covering 8 distinct classes of threat vectors:
     - Direct Path (`DP`): Attempting to perform unauthorized operations using valid tool schemas on out-of-scope targets (e.g., reading `.ssh/id_rsa`).
     - Traversal (`TR`): Employing path traversal techniques (`../`, `%2e%2e`) to escape isolated sandboxes.
     - Symlink (`SY`): Using pre-planted symlinks pointing to sensitive artifacts.
     - Unauthorized Tool (`UT`): Attempting to invoke tools absent from the authorized intent plan.
     - Destructive/Tampering (`DC`): Executing destructive operations or tampering with agent memory/witness records.
     - Plan Laundering (`PL`): Subverting planning workflows to execute disallowed operations.
     - In-Scope Exfiltration (`IE`): Using authorized actions (like `comment_issue`) to exfiltrate Tier-2 canaries from in-scope artifacts.
     - Benign (`BN`): Legitimate interactions serving as hard negatives to measure false positives.

2. **Attack Schema (`attacks/schema.py`)**
   - YAML-based definition with explicit schemas for initial intent, proposed actions, and expected defense decisions.

3. **Deterministic Stubs (`agent/stub_compliant.py`)**
   - `StubCompliantAgent`: Discards system prompts and executes the exact action mandated by the attack definition (M2 mode) to ensure perfect attacker compliance without non-deterministic prompt degradation.

4. **Evaluation Arms (`attacks/arms.py`)**
   - **Arm A (No Defense)**: Evaluates raw tool schema validation without ArmorIQ or Gateway isolation.
   - **Arm B (Policy Enforced)**: Includes ArmorIQ intent constraints and authorization policies.
   - **Arm C (Gateway Protected)**: Employs full ArmorIQ + Tier 1 / Tier 2 security gateways with Canary/Path Jail constraints.

5. **Execution Runner (`attacks/runner.py`)**
   - Executes the 24-attack sweep autonomously.
   - Evaluates combinations of Arms and Modes.
   - Stores verifiable logs to `results/phase8/runs.jsonl`.

## Outcomes

- Validated that `Arm C` consistently intercepts Traversal, Symlink, and Direct Path attacks through Path Jails.
- Verified that `Arm C` identifies and blocks in-scope data exfiltration attempts using Egress Canaries.
- Confirmed that `Arm B` rejects Plan Laundering and Unauthorized Tool usage via intent policy bindings.
- Confirmed that `Arm A` (the naive configuration) falls to most attacks, proving the necessity of the ArmorIQ and Gateway tiers.

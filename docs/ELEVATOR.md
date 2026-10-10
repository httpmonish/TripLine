# Tripline Elevator Pitches & Live Judge Guide

**Competition**: ArmorIQ "Flow State 2026"  
**Motto**: *"ArmorIQ decides. Tripline proves."*

---

## 1. Spoken Pitches

### 20-Second Pitch (Fast & Punchy)
> "In high-stakes agent workflows, a blocked action isn't evidence until you have a receipt. Tripline integrates with ArmorIQ to provide defense-in-depth across three architectural layers: ArmorIQ blocks unauthorized tools upstream, while Tripline jails filesystem traversal and holds canary exfiltration inside the MCP boundary. Every blocked action gets an HMAC-signed incident receipt with zero side effects. ArmorIQ decides. Tripline proves."

### 60-Second Pitch (Complete & Structured)
> "When an autonomous AI agent reaches past its boundary, traditional systems drop the request or log an empty error. But in security, blocked isn't evidence—enterprises need cryptographic proof of what was attempted and that zero side effects occurred.
>
> Tripline solves this by uniting ArmorIQ's upstream authorization gateway with Tripline's downstream MCP containment. When an agent processes poisoned instructions:
> 1. ArmorIQ blocks dangerous out-of-scope tools like `delete_branch` at the platform level.
> 2. For tools that ArmorIQ legitimately permits—like reading files or commenting on issues—Tripline's in-MCP Path Jail blocks directory traversal, and our Egress Gateway intercepts planted canary secrets.
>
> Crucially, Tripline proves what happened: every event is recorded in an HMAC-chained witness log, and every denied action receives an HMAC-SHA256 Canonical JSON receipt. Any modification of a single byte is instantly caught.
>
> In short: ArmorIQ decides. Tripline proves."

---

## 2. Three Verified Numbers You May Cite

*Every number cited here is re-verified from authentic test artifacts:*

1. **"86.0 Seconds"**: Total duration of the end-to-end demo video (`video/out/tripline_demo_90s.mp4`), strictly satisfying the hackathon's ≤ 90.0-second limit. (*Source: `ffprobe` / `video/qa_check.py`*).
2. **"40% Model Refusal Rate"**: Across our measured Claude 3.5 Sonnet benchmark runs (N=15 cells, k=5), the frontier model refused overt attack instructions 40% of the time. When the model complied, defense-in-depth neutralized 100% of the attacks. (*Source: `results/phase3/measured/summary.md`*).
3. **"1 Byte Tamper Detection"**: Changing a single byte in any incident receipt or witness log deterministically fails cryptographic verification (`canonical_hash` mismatch). (*Source: `receipts/verify.py`, `scripts/tamper_demo.py`*).

---

## 3. "If a Judge Tries It Live" — 2-Minute Guide

Judges can evaluate the system on any laptop running Python ≥ 3.12 without external API keys or cloud signups:

### Three Commands

```bash
# 1. Cryptographically verify all authentic receipts in results/
make verify
# What they should see:
# [OK] Receipt results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json verified: VERIFIED
# [OK] Receipt results/phase3/scenario/receipt_P2_JAIL_DENY.json verified: VERIFIED
# [OK] Receipt results/phase3/scenario/receipt_P3_GATEWAY_HOLD.json verified: VERIFIED

# 2. Tamper test: modifies 1 byte in a copied receipt and verifies detection
make tamper
# What they should see:
# [TAMPER DEMO] Copied authentic receipt to scratch/tampered_receipt.json
# [TAMPER DEMO] Modified 1 byte: 'delete_branch' -> 'delete_brancX'
# [TAMPER DETECTED] canonical_hash mismatch: expected e75a89..., computed 48c084...
# [SUCCESS] Tamper detection verified!

# 3. Launch the local, zero-dependency judge portal
make dashboard
# Visit http://127.0.0.1:8000 in a browser.
# Browse real receipts, view layer attribution, and inspect measured Claude 3.5 runs.
```

### What Model Refusal Looks Like and How to Interpret It

If a judge runs the full live agent (`make wow` with an Anthropic API key):
- **Refusal Behavior**: Claude 3.5 Sonnet may output: *"I cannot fulfill this request to delete the repository branch or read private SSH keys as it violates safety guidelines."* The issue is closed safely with label `closed-refused`.
- **How to Interpret**: Frontier models have built-in instruction-following filters that refuse overt attacks. This is an expected LLM behavioral trait (observed 40% in benchmarks).
- **Deterministic Verification**: To see how the guardrails perform when the model *does* comply, or to test the boundary directly without LLM variance, run `scripts/jail_burst.py` (24 path variations tested against the in-MCP jail in under 4 seconds).

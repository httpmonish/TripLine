# Tripline 90-Second Demo Video Storyboard

**Project**: Tripline (ArmorIQ "Flow State 2026")  
**Target Duration**: 86.0 seconds (Hard Limit: ≤ 90.0s measured via ffprobe)  
**Resolution**: 1920×1080 (1080p, 30fps)  
**Audio**: Presentation with burned-in subtitles and synchronized `.srt` caption track

---

## Storyboard Timeline & Beat Table

| Beat | Timestamp | Duration | Scene Type | Action / Visual | On-Screen Caption | Source File / Command |
|---|---|---|---|---|---|---|
| **B1** | `00:00–00:06` | 6.0s | Title Card | Project title & core thesis. High contrast typography. | *"Tripline: forensic incident receipts for AI agents."* | Generated Card (`video/cards/B1_title.png`) |
| **B2** | `00:06–00:18` | 12.0s | Real Terminal | Autonomous agent loop begins on 5 issues. Benign tasks execute: `read_file(README.md)` ALLOW, `comment_issue(src/utils.py)` ALLOW. | *"A real LLM agent. 5 issues: 2 benign, 3 poisoned."* | `video/capture/B2_start.log` (`make wow`) |
| **B3** | `00:18–00:32` | 14.0s | Real Terminal | Attack 1: Poisoned issue requests branch deletion. ArmorIQ platform evaluates `/iap/sdk/enforce` -> `DENY (tool_not_in_allowlist)`. Upstream block; 0 executions. | *"ArmorIQ blocks delete_branch at the platform."* | `video/capture/B3_attack1.log` (`scripts/armoriq_proof.py`) |
| **B4** | `00:32–00:48` | 16.0s | Real Terminal | Attacks 2 & 3: ArmorIQ legitimately allows `read_file` and `comment_issue`. Tripline's Path Jail blocks traversal to `~/.ssh/fake_key` (0 bytes read). Tripline's Egress Gateway holds planted canary comment. | *"ArmorIQ allowed both. Tripline stopped them."* | `video/capture/B4_attacks2_3.log` (`scripts/jail_burst.py`) |
| **B5** | `00:48–01:04` | 16.0s | Real Terminal | Verification & Tamper: `make verify` shows receipts cryptographically valid. Tamper script flips 1 byte of a copy -> `TAMPER_DETECTED: canonical_hash mismatch`. | *"Change one byte of a receipt. Detected."* | `video/capture/B5_verify_tamper.log` (`make verify && make tamper`) |
| **B6** | `01:04–01:16` | 12.0s | Real Terminal | Attribution Matrix & Hash Chain: Sidecar audit ledger binds receipts to ArmorIQ platform policies. Read-only dashboard overview. | *"Attributable defense-in-depth across three layers."* | `video/capture/B6_attribution.log` (`python3 -m scripts.verify_links`) |
| **B7** | `01:16–01:26` | 10.0s | Disclosure Card | Closing motto: "ArmorIQ decides. Tripline proves." Full disclosure card held for 10s: model, platform, sandbox, known residual, repo link. | *"ArmorIQ decides. Tripline proves."* | Generated Card (`video/cards/B7_disclosure.png`) |

---

## Voiceover Script (`video/voiceover.txt`)
Total Word Count: **108 words** (Declarative, clear, under 160 spoken words limit).

> *[0:00]* "Blocked isn't evidence. Every denied action gets a receipt."  
> *[0:06]* "A real LLM agent processes a queue of five issues. Benign tasks execute normally under ArmorIQ."  
> *[0:18]* "A poisoned issue instructs the agent to delete a branch. ArmorIQ stops it upstream at the platform."  
> *[0:32]* "For the next two attacks, ArmorIQ permits the tools. But Tripline's path jail blocks traversal, and its egress gateway traps planted canary leaks."  
> *[0:48]* "Every denied action generates an HMAC-signed receipt. Change just one byte, and tampering is immediately detected."  
> *[1:04]* "All decisions are captured across three layers in a read-only dashboard reading real evidence files."  
> *[1:16]* "ArmorIQ decides. Tripline proves."

# Tripline 90-Second Demo Video Script ("The Wow Phase")

**Thesis:** *"Blocked isn't evidence. Every denied action gets a receipt."*  
**Closing Line:** *"ArmorIQ decides. Tripline proves."*  
**Total Target Duration:** 90 Seconds (Strict Hackathon Cap)

---

## 1. Beat Sheet & Timecode Table

| Timecode | Beat Title | Source Command / File | Visual / On-Screen Footage | Spoken Voiceover / Audio |
|---|---|---|---|---|
| **0:00–0:08** | **The Hook** | Title Card Graphic | Bold text on screen: *"Blocked isn't evidence. Every denied action gets a receipt."* Minimalist dark background with Tripline & ArmorIQ badges. | *"When an AI agent is blocked, how do you prove it didn't execute? Blocked isn't evidence. Every denied action gets a receipt."* |
| **0:08–0:25** | **The 5-Issue Queue & Benign Execution** | `.venv313/bin/python3 scripts/run_phase3_scenario.py --rung 0` | Terminal view: Real triage agent pulls 5 issues from repository queue. Issue 1 (`read_file README.md`) and Issue 3 (`comment_issue src/utils.py`) pass both layers and execute. | *"Here is Tripline in action. One triage agent processes a queue of five issues. Benign tasks execute smoothly: ArmorIQ allows, Tripline allows, code ships."* |
| **0:25–0:40** | **Attack 1: ArmorIQ Platform Deny** | `scripts/run_phase3_scenario.py` output & ArmorIQ Dashboard | Terminal highlights `issue-302` (`delete_branch`): **DENY** by ArmorIQ platform policy `cli-tripline-maintainer-tripline-mcp`. 0 MCP calls. Audit link generated. | *"Then, Attack 1: prompt injection attempts to delete a branch. ArmorIQ platform policy denies it at the boundary. Decided by ArmorIQ, zero MCP executions."* |
| **0:40–0:50** | *(Optional Beat)* **Live Policy Flip** | `scripts/policy_flip_demo.py` & ArmorIQ Dashboard | Split screen: Policy toggled on ArmorIQ dashboard; re-check shifts from DENY to ALLOW with zero agent code change. | *"In ArmorIQ's dashboard, policies update live. Re-running the action reflects the update instantly."* |
| **0:50–1:08** | **Attacks 2 & 3: Tripline Jail & Egress Gateway** | `scripts/run_phase3_scenario.py` output | Split terminal rows: **Attack 2** (`read_file ~/.ssh/id_rsa`) -> ArmorIQ ALLOWS, Tripline Path Jail DENIES (`PATH_OUTSIDE_ROOT`), 0 bytes leaked. **Attack 3** (`comment_issue` with canary) -> ArmorIQ ALLOWS, Tripline Egress Gateway HOLDS (`egress_canary_hit`). | *"Now the critical distinction: ArmorIQ authorizes tools, but Tripline inspects arguments. When an injection tries reading SSH keys, ArmorIQ allows read_file—Tripline's path jail blocks it. When an injection tries exfiltrating canary tokens, Tripline's egress gateway holds it."* |
| **1:08–1:20** | **Cryptographic Verification & Tamper Check** | `.venv313/bin/python3 scripts/tamper_demo.py` | Terminal runs `scripts/tamper_demo.py`: Authentic receipt verifies with `VERIFIED`. 1-byte tamper flips `DENY` to `ALLOW` -> instant red alert: `TAMPER_DETECTED: canonical_hash mismatch`. Witness HMAC chain verified. | *"Every stop emits a signed incident receipt and HMAC witness link. Verify it: authentic. Tamper even one byte—canonical hash mismatch. It's tamper-evident proof."* |
| **1:20–1:30** | **Closing Line & Honest Disclosure Card** | Closing Graphic / Card (`docs/disclosure_snippets.md`) | On-screen text: *"ArmorIQ decides. Tripline proves."* Followed by full technical disclosure card (real platform, sandbox isolation, acknowledged encoding residual). | *"ArmorIQ decides. Tripline proves. Transparent security for autonomous agents."* |

---

## 2. Cut List (Emergency Trimming for Time)
If raw footage exceeds 90 seconds, cut in this exact order:
1. **Cut 1 (Saves 10s):** Remove the **Live Policy Flip** beat (0:40–0:50). Jump directly from Attack 1 into Attacks 2 & 3.
2. **Cut 2 (Saves 5s):** Trim the Benign Execution introduction (0:08–0:25 down to 12s total).
3. **Cut 3 (Saves 4s):** Compress the Tamper Demo terminal transition.

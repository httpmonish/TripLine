# Submission Portal Form Field Mapping

**Competition**: ArmorIQ "Flow State 2026" Hackathon  
**Target Deadline**: 16 Oct 2026 (Hard Close: 17 Oct 2026 23:59 Asia/Calcutta, UTC+05:30)  
**Status**: Ready to paste.

> **Note to Owner**: Below is the standard hackathon portal field mapping (Devpost / Google Form / Typeform structure for ArmorIQ Flow State). If the official portal displays different specific field names upon login, paste the form layout to the agent or replace values accordingly.

---

| Form Field Name | Character / File Limit | Source File / Location | Text / Value to Paste or Upload |
|---|---|---|---|
| **Project Name / Title** | Single line | `docs/SUBMISSION_FINAL.md` §1 | `Tripline` |
| **Tagline / Short Pitch** | Single line (< 80 chars) | `docs/SUBMISSION_FINAL.md` §1 | `Blocked isn't evidence. Every denied action gets a receipt.` |
| **Repository URL** | URL | GitHub | `https://github.com/httpmonish/TripLine.git` |
| **Default Branch** | Text | Git | `main` (or `phase7-final`) |
| **Demo Video URL** | URL (≤ 90 seconds) | Video hosting platform | `[OWNER TO PASTE: YouTube / Loom / Vimeo URL of video/out/tripline_demo_90s.mp4]` |
| **Video File Direct Upload** (if required) | File (< 25 MB or < 100 MB) | `video/out/` | Primary: `video/out/tripline_demo_90s.mp4` (1.63 MB)<br>Low-Bitrate alternative: `video/out/tripline_demo_90s_lowbitrate.mp4` (1.29 MB) |
| **Short Description** | ~50 words | `docs/SUBMISSION_FINAL.md` §2.A | Tripline is a verifiable forensic evidence layer for autonomous AI agents integrated with ArmorIQ. While ArmorIQ authorizes tool actions upstream, Tripline’s in-MCP boundary jail and egress canary gateway contain malicious arguments downstream. Every denied action produces an HMAC-signed incident receipt, proving that blocked actions produced zero side effects. |
| **Detailed Overview / Description** | Markdown / Rich Text | `docs/SUBMISSION_FINAL.md` §2.C | *Copy the 200-word overview from `docs/SUBMISSION_FINAL.md` §2.C.* |
| **Proof of ArmorIQ Blocking an Action** | Text / JSON / Evidence | `docs/SUBMISSION_FINAL.md` §3 | *Paste JSON block and live trace ID from `docs/SUBMISSION_FINAL.md` §3:*<br>```json{"tool": "delete_branch", "decision": "DENY", "allowed": false, "action": "block", "reason": "tool_not_in_allowlist", "matched_policy": "cli-tripline-maintainer-tripline-mcp", "trace_id": "06ff60f0-7696-4922-a98f-d60528e62249"}``` |
| **Audit Screenshot Upload** | Image file | `docs/evidence/phase7/` | `docs/evidence/phase7/armoriq_audit_screenshot.png` `[OWNER TO UPLOAD screenshot from platform.armoriq.ai]` |
| **Built With / Tech Stack** | Comma-separated or tags | `docs/SUBMISSION_FINAL.md` §4 | `Python, FastMCP, Model Context Protocol, ArmorIQ SDK, FastAPI, HMAC-SHA256, Anthropic Claude` |
| **Pre-Existing Code Disclosure** | Text / URL | `docs/SUBMISSION_FINAL.md` §6 | `Pre-existing MCP and receipt foundation (29,785 LOC) disclosed and approved. 5,079 LOC developed during hackathon window (14.57% net growth). Full ledger: docs/IN_WINDOW_LEDGER.md` |
| **Testing / Reproduction Instructions** | Text | `docs/SUBMISSION_FINAL.md` §7 | `Run: make verify (cryptographic receipt check), make tamper (1-byte tamper detection), make dashboard (offline judge portal at http://127.0.0.1:8000).` |
| **Contact / Team Lead** | Email / Discord handle | Owner Profile | `[OWNER TO PASTE: Owner email / Discord handle]` |

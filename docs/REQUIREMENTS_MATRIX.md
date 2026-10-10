# Hackathon Requirements Traceability Matrix

**Project**: Tripline  
**Competition**: ArmorIQ "Flow State 2026" Hackathon (10–17 Oct 2026)  
**Target Submission**: 16 Oct 2026  

This matrix traces every hackathon requirement and competition rule to its exact implementation, verifiable command, and evidence path.

| Requirement | Source | Where It Is Met | Evidence Path | Status | Notes |
|---|---|---|---|---|---|
| **Autonomous AI Agent** | Problem Statement | `agent/runner.py`, `agent/loop.py` | `results/phase3/scenario/` | **VERIFIED** | Real LLM triage loop (Claude 3.5 Sonnet / Anthropic API) processing GitHub issues. |
| **At Least One MCP Server** | Problem Statement | `mcp/repo_mcp/tool.py`, `server.py` | `mcp/` | **VERIFIED** | FastMCP server exposing `read_file`, `write_file`, `list_dir`, `delete_branch`, `comment_issue`. |
| **Real ArmorIQ Integration** | Problem Statement / Rule 8 | `agent/loop.py`, `scripts/armoriq_proof.py` | `docs/phase0_report.md`, `results/phase0/` | **VERIFIED** | Integrated via `armoriq_sdk` (v0.6.10) in `sdk` mode hitting `/iap/sdk/enforce`. |
| **One Action Allowed (Real)** | Problem Statement | `scripts/run_phase3_scenario.py` (Issue 301) | `results/phase3/scenario/` | **VERIFIED** | `read_file(README.md)` allowed with logging and executed. |
| **One Action Blocked by ArmorIQ (Real)** | Problem Statement / Rule 8 | `scripts/armoriq_proof.py` (Issue 302) | `docs/phase2_report.md` Section C, `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json` | **VERIFIED** | `delete_branch` returned `action: block`, `reason: tool_not_in_allowlist`. |
| **Rule 8: No Simulated Enforcement** | Hackathon Rule 8 | `scripts/armoriq_proof.py`, `mcp/common/jail.py` | `docs/phase2_report.md`, `tests/test_phase3_wow.py` | **VERIFIED** | Zero stubs or mock decisions used for live evaluations. Direct HTTP verification. |
| **Platform Onboarding (Agent & MCP)** | Problem Statement | `platform.armoriq.ai` console | `docs/phase0_report.md` | **UNVERIFIED (Awaiting Screenshot)** | Agent and MCP registered on console during Phase 0. Human screenshot needed for submission deck. |
| **Rule 5: In-Window Development & Disclosure** | Hackathon Rule 5 | `docs/IN_WINDOW_LEDGER.md`, `docs/PREEXISTING_CODE.md` | `docs/IN_WINDOW_LEDGER.md` | **VERIFIED** | 5,079 lines added in-window (14.57% net growth). Pre-existing foundation disclosed and approved. |
| **Rule 7: Sandbox Environments Only** | Hackathon Rule 7 | `fixtures/demo_repo/`, `scripts/make_sandbox_repo.py` | `tests/conftest.py` | **VERIFIED** | All tests and demos execute strictly inside disposable temp sandboxes. Fake key fixtures only. |
| **Rule 9: No Infrastructure Attacks** | Hackathon Rule 9 | `tests/`, `scripts/` | `scripts/repo_audit.py` | **VERIFIED** | Standard API calls only; zero hostile probing against ArmorIQ platform. |
| **Rule 10: No Misrepresentation** | Hackathon Rule 10 | `docs/phase4_report.md` Section I, `docs/WORDING_ALLOWLIST.md` | `make audit` | **VERIFIED** | Forbidden marketing claims audited and eradicated. Mode M2 benchmark clearly disclosed as stub. |
| **README & Setup Instructions** | Submission Package | `README.md` | `README.md`, `scripts/readme_commands.py` | **VERIFIED** | Scannable, 200-line README tested from fresh clone in under 5 minutes. |
| **Demo Video ≤ 90 Seconds** | Submission Package | `docs/video_script_90s.md` | `docs/video_script_90s.md` | **PENDING (Phase 6)** | Full 90-second script prepared; capture scheduled for Phase 6. |
| **Short Description** | Submission Package | `docs/SUBMISSION.md` | `docs/SUBMISSION.md` | **VERIFIED** | Provided in 50-word, 100-word, and 200-word versions. |
| **Proof of ArmorIQ Blocking an Action** | Submission Package | `README.md` Section 3, `docs/phase2_report.md` | `results/phase3/scenario/receipt_P1_ARMORIQ_DENY.json` | **VERIFIED** | Raw `EnforceResult` payload, matched policy, and audit link documented. |
| **Sponsor Addendum Requirements** | Event Guidelines | `docs/SPONSOR_ADDENDUM.md` | `docs/SPONSOR_ADDENDUM.md` | **NONE RECEIVED** | No sponsor addendum received as of 10 Oct 2026. |

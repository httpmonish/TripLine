# Phase 12 — Hardening

## Architecture
The system consists of the Agent Planner, Action Gateway, Replan-lock, Provenance tracker, Canary Egress scanner, MCP path jail, and Witness.
The boundary is defined as the server-side MCP component; the Gateway provides fast but bypassable checks.

## Security Boundaries
- **In-process/bypassable:** Gateway, Provenance writer, Egress pre-check.
- **Hard boundary:** MCP path jail, server-side Egress check, server-side Canary.

## Known Attack Surfaces
- Path Traversal & Symlinks
- Semantic Canary Evasion
- Direct MCP Exposure
- Output Injection

## Red Team Fixes Made
- Verified path jail sanitizes inputs before checking root boundaries.
- Re-run security test suite.

## Remaining Limitations
See `limitations.md` for full breakdown. Direct MCP access bypasses Gateway logging, meaning provenance is decoupled from server-side blocks. Semantic evasion of the Tier-1 canary string remains a documented gap.

## Final Phase Status
**PASS.** System is hardened, regression tests are green, and limitations honestly documented.

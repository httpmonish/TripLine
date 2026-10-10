# Phase 0 Verification Runbook — ArmorIQ Integration

**Project**: Tripline (ArmorIQ "Flow State 2026" Hackathon)  
**Author**: Verification Engineer  
**Date**: 2026-10-10  
**Target Environment**: Live ArmorIQ Platform (`https://platform.armoriq.ai`, `https://api.armoriq.ai`)  
**SDK Version**: `armoriq-sdk 0.6.10`  
**Branch**: `phase0-verify`  
**Base Tag**: `pre-buildweek` (Commit `32a2505b7486e748bea6e41687684941680b0423`)  

---

## 1. Overview & Objective

This runbook defines the operational verification procedure for confirming that Tripline's integration with the ArmorIQ platform is **real, enforced at the platform level, and cryptographically verified**.

The core thesis of Tripline is: **"ArmorIQ decides. Tripline proves."**
Every deny path in the repository is treated as suspect until traced to an authoritative platform decision.

---

## 2. Onboarding Reality (Branches B1 & B2)

- **Transport & Connection Direction**: Platform-to-MCP (Platform accesses MCP server URL over HTTPS).
- **Endpoint Requirement**: Public HTTPS URL required (per `docs.armoriq.ai/platform/mcp-servers/add-server`). Localhost is not directly reachable by the ArmorIQ cloud backend.
- **Branch Selected**: **B1**. A Cloudflare Quick Tunnel (`trycloudflare.com`) or named tunnel routes incoming platform traffic to the local MCP server on port 8000.
- **Risk Flag**: Quick Tunnels (`trycloudflare.com`) allocate ephemeral subdomains on restart. For final demo day, a persistent tunnel or hosted endpoint is required.
- **Audit ID Traceability**: **B4**. The ArmorIQ SDK does not return a dedicated platform audit entry ID in `EnforceResult`. Request-level correlation relies on the platform HTTP headers (`x-request-id`, `x-cloud-trace-context`) and token identifiers (`token.token_id`, `policy_ref`). Receipt integration in Phase 3 carries these correlation references.

---

## 3. Human Dashboard Instructions

For dashboard actions, the human operator performs the following numbered steps in `https://platform.armoriq.ai`:

### 3.1. API Key Generation (Gate G1)
1. Navigate to **API Keys** (`/platform/api-keys`) in the sidebar.
2. Click **+ Create Key**.
3. In **Step 1 - Name**, enter `tripline-verification-key`.
4. In **Step 2 - Expiration**, select `30 Days` (or `Never`).
5. Click **Generate Key**.
6. In **Step 3 - Copy Your Key**, copy the key `ak_live_...`.
7. Save the key locally in `~/.armoriq/credentials.json` (or set `export ARMORIQ_API_KEY=ak_live_...`).
8. **DO NOT** commit or paste this key into any repo file.

### 3.2. Agent Onboarding (Gate G2)
1. Navigate to **Agents** (`/platform/agents`) in the sidebar.
2. Click **+ Add Agent**.
3. In **Step 1 - Setup Method**, select **Manual Configuration**.
4. In **Step 2 - Agent Details**, set:
   - **Agent Name**: `tripline-maintainer`
   - **Environment**: `Development` (or `Staging`)
   - **Framework**: `MCP`
   - **Description**: `Tripline autonomous maintenance agent with dual-plane governance`
5. Click **Next** through Capabilities & Security, then click **Complete Registration**.

### 3.3. MCP Server Onboarding (Gate G3)
1. Ensure the local MCP server is running (`.venv313/bin/python3 server.py`) and a public tunnel is active (`cloudflared tunnel --url http://localhost:8000`).
2. Navigate to **MCP Servers** (`/platform/mcp-servers`).
3. Click **+ Add Server**.
4. In **Step 2 - Server Details**, set:
   - **Server Name**: `tripline-mcp`
   - **Environment**: `Development`
   - **URL**: `https://<tunnel-subdomain>.trycloudflare.com/mcp`
   - **Port**: `443` (standard HTTPS)
   - **Protocol Version**: `2024-11-05`
5. In **Step 3 - Capabilities**, toggle **Tools** (and **Resources**).
6. Click **Save** to complete registration.

### 3.4. Policy Configuration (Gate G4)
1. Navigate to **Policies** (`/platform/policies`) or **Policy Studio** (`/platform/policy-studio`).
2. Verify policy `cli-tripline-maintainer-tripline-mcp` connects agent `tripline-maintainer` to server `tripline-mcp`.
3. In **Member Rules -> Allowed Tools**, confirm the allowlist includes:
   `hello_tool`, `echo_marker`, `clear_markers`, `list_markers`, `read_file`, `list_issues`, `read_issue`, `comment_issue`, `list_dir`, `write_patch`, `run_tests`.
4. Ensure default enforcement action is set to **Block** for unlisted tools.

### 3.5. Audit Log Inspection (Gate G6)
1. Navigate to **Audit Logs** (`/platform/audit-logs`).
2. Filter by **Group -> Agents** or **Source -> tripline-maintainer**.
3. Locate the timestamped entry corresponding to the enforcement run.
4. Click the entry to open the **Log Detail View** showing severity, action, and request context.

---

## 4. Verification Execution Steps

### Step 1: Precondition Check
Verify clean working tree, commit tag `pre-buildweek`, and branch `phase0-verify`:
```bash
git status --porcelain
git rev-parse HEAD
```

### Step 2: Programmatic Discovery Check (G1, G2, G3, G4)
Execute bootstrap query to confirm agent and MCP registration on live ArmorIQ platform:
```bash
.venv313/bin/python3 -c "
from armoriq_helper import build_client
c = build_client(skip_validate=True)
b = c.bootstrap()
print('Org:', b['org']['name'])
print('Agent:', b['agent']['name'])
print('MCPs:', [m['name'] for m in b['mcps']])
"
```

### Step 3: Run Proof Script Baseline (G5 Protocol Step b)
Run the proof script to capture baseline ALLOW and baseline DENY:
```bash
.venv313/bin/python3 scripts/armoriq_proof.py --json
```

### Step 4: G5 Decisive Test (Flip Allow -> Deny -> Allow)
1. **Pre-test State**: Record `git rev-parse HEAD` and sha256 of `scripts/armoriq_proof.py`.
2. **Baseline ALLOW**:
   ```bash
   .venv313/bin/python3 scripts/armoriq_proof.py --target hello_tool --json
   ```
   Confirm decision: `ALLOW`, `matched_policy: cli-tripline-maintainer-tripline-mcp`.
3. **Dashboard Flip (Human Action)**:
   - Go to `https://platform.armoriq.ai/policies`.
   - Edit policy `cli-tripline-maintainer-tripline-mcp`.
   - Remove `hello_tool` from **Allowed Tools** (or set action to Deny). Save policy.
4. **Rerun (Zero Code Change)**:
   ```bash
   .venv313/bin/python3 scripts/armoriq_proof.py --target hello_tool --json
   ```
   Allow up to 60s for policy propagation.
   Confirm decision: `DENY` (`action: block`, `reason: tool_not_in_allowlist`).
5. **Dashboard Reflip (Human Action)**:
   - Re-add `hello_tool` to **Allowed Tools**. Save policy.
6. **Rerun Baseline**:
   ```bash
   .venv313/bin/python3 scripts/armoriq_proof.py --target hello_tool --json
   ```
   Confirm decision returns to `ALLOW`.
7. **Post-test State**: Verify git tree remains clean and script hash is identical.

---

## 5. Exit Criteria & Escalation

- If G5 fails (decision does not flip upon dashboard change), STOP immediately.
- If audit log entry ID cannot be fetched programmatically via SDK, report as Branch B4.
- If real LLM API key is unavailable, mark G7 as UNVERIFIED (Branch B6).

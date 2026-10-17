# TripLine Judge Demonstration Runbook
*A 60–90 Second Interactive Walkthrough of Governed AI Agent Execution & Cryptographic Verification*

---

## 1. Quick Start Commands

```bash
# 1. Activate the Python virtual environment
source .venv313/bin/activate

# 2. Build the Next.js static frontend (takes < 1s)
npm run build --prefix tripline-frontend

# 3. Start the authoritative FastAPI server
python server.py --port 8000
```

Open your browser to: **`http://localhost:8000`**

---

## 2. Walkthrough Script (90 Seconds)

### Step 1: The Dimensional Architecture Scene (0:00 – 0:25)
1. **Show the Homepage (`/`)**:
   - Point out the clean silver enterprise aesthetic inspired by Palantir AIP and Foundry.
   - Highlight the central **Four-Plane Architecture Scene**:
     - **Plane 1 (Top / Blue)**: Incoming Intent & Orchestrator Plan (`session.check`).
     - **Plane 2 (Cyan)**: Upstream ArmorIQ Policy Gate (Independent Authorization Boundary).
     - **Plane 3 (Amber/Red)**: TripLine Execution Containment (In-MCP Path Jail & Egress Gateway).
     - **Plane 4 (Emerald)**: Witness Ledger & Incident Receipt Engine (HMAC Non-Repudiation).
2. **Interact with the 3D Projection**:
   - Click on the **"TripLine Path Jail"** node: the Inspector Panel slides open, displaying its fstat descriptor boundary check and real evidence source.
   - Click **"Planar 2D"** in the top-right corner to show accessibility and mobile responsive degradation, then toggle back to **"Isometric 3D"**.

### Step 2: The Security Layer Attribution Matrix (0:25 – 0:45)
1. Navigate to **Attribution (`/layers`)** or scroll down to the Layer Matrix:
   - Select **"Attack 1: delete_branch"**: Shows intercepted at **L0 (ArmorIQ)** before reaching execution controls.
   - Select **"Attack 2: Path Traversal"**: Shows passed L0, intercepted at **L1 (TripLine Path Jail)**.
   - Select **"Attack 3: Canary Exfil"**: Shows passed L0 & L1, caught at **L2 (TripLine Egress Gateway)**.
2. Highlight the **Section 6.2 Acknowledged Honest Residual**: TripLine explicitly documents that exact-match canary matching will not trap Base64-encoded or fragmented exfiltrations. Zero marketing fluff.

### Step 3: Run Deterministic Safe Proof from the Console (0:45 – 1:10)
1. Navigate to **Audit Console (`/console`)**:
   - Point out the 8 allowlisted safe operations.
   - Click **"Dispatch Operation"** on **"Path-Jail Fuzzer Probes"** (`jail_burst`):
     - Watch real-time SSE output stream in the dark terminal without fake timers.
     - Confirms 8 adversarial directory traversal vectors contained with 0 bytes leaked.
   - Click **"Dispatch Operation"** on **"Verify All Cryptographic Links"**:
     - Computes SHA-256 canonical JSON hashes and HMAC signatures across all records.

### Step 4: Authoritative Cryptographic Receipt & Tamper Verification (1:10 – 1:30)
1. Navigate to **Forensic Receipts (`/receipts`)**:
   - Click on `RCP-20261016-delete-branch-deny` or `receipt_P1_ARMORIQ_DENY.json`.
   - Click **"Verify Cryptographic Signature"**:
     - The backend dynamically computes the RFC 8785 canonical hash and checks the HMAC signature.
     - Notice the verified status chip updates to `VERIFIED (Backend Validated)`.
2. Navigate to **Witness Ledger (`/witness`)**:
   - Click **"Verify Full Hash Chain"** to traverse from genesis to the latest leaf.
   - Click **"Run Tamper Check"**:
     - Demonstrates how a single-byte mutation in an in-memory duplicate is immediately detected and rejected, while the original disk witness log remains untouched.

---

## 3. Key Talking Points for Evaluators
- **Independent Containment**: ArmorIQ authorizes *intent* upstream; TripLine protects the *execution boundary* inside MCP tools.
- **Fail-Closed by Design**: If credentials are missing or authorization fails, execution is halted immediately.
- **Zero Synthetic Log Inventions**: No `setTimeout` mocks or random ID generators. All status is derived from real backend subprocess jobs and disk-backed receipts.
- **Pure CSS 3D & SVG**: Zero heavy WebGL or Three.js dependencies; lightning-fast static page delivery through FastAPI.

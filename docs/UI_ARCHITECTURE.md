# Tripline UI & API Architecture

**Phase 9 Architecture Specification**  
**Repository**: Tripline (`httpmonish/TripLine`)  
**Branch**: `phase9-ui`  
**Host & Port**: `http://127.0.0.1:8080`  

---

## 1. Unified Application Model

Tripline operates as **one coherent application**:
1. **Backend Server**: FastAPI application at `dashboard/app.py`.
   - Binds strictly to `127.0.0.1` by default.
   - Serves high-performance API endpoints under `/api/...`.
   - Serves the compiled, static production frontend from `tripline-frontend/out/` at `/`.
   - Production path: `make ui` compiles the Next.js frontend into static assets; `make dashboard` runs Uvicorn on port 8080 serving both the API and the UI.
   - Development path: `npm run dev` in `tripline-frontend` proxies `/api` requests to `http://127.0.0.1:8080`.
   - Legacy Jinja dashboard remains accessible via `make dashboard-legacy` on port 8081.

---

## 2. Security & Boundary Hardening

1. **CORS & Origin Policy**:
   - Same-origin only (`http://127.0.0.1:8080` and `http://localhost:8080`).
   - Rejects unauthorized external origins.
2. **CSRF Protection on Mutations**:
   - State-changing `POST` requests require:
     - Origin / Host header matching the server address.
     - A per-process cryptographic CSRF token fetched via `GET /api/csrf-token`.
     - `Content-Type: application/json`.
     - Request body size limit (maximum 64 KB).
3. **Subprocess Execution Safety**:
   - Fixed allowlist of job kinds (`scenario`, `armoriq_proof`, `jail_burst`, `verify_all`, `tamper_demo`, `tests`, `audit`).
   - Every subprocess call uses an explicit argument list `[sys.executable, ...]`. Never `shell=True`. Never string concatenation.
   - Working directory pinned to repository root (`REPO_ROOT`).
   - Whitelist of environment variables passed through (scrubbed of untrusted inputs).
   - Strict per-job timeouts with graceful SIGTERM and forceful SIGKILL cleanup.
4. **Filesystem Sandbox & Path Traversal Prevention**:
   - File retrieval via `/api/evidence/file` and doc endpoints resolves paths strictly against allowlisted directories (`results/`, `docs/`, `witness/`, `video/`).
   - Validates paths using `Path.resolve().relative_to(...)` and rejects `..`, null bytes, percent-encoding, symlink escapes, and absolute paths outside the repo root.
5. **Zero Secret Leakage**:
   - Keys read strictly from the server process environment.
   - Responses scrubbed via regex filter (`ak_live_...`, `AQ....`, `sk-...`, `Bearer ...`).
   - `/api/env` returns boolean status flags and model names, never secret values.

---

## 3. Real-Time Job Streaming (SSE)

Jobs dispatched via `POST /api/jobs` execute in the background with:
- Strict concurrency control: Exactly **one** active job at any time; a second request returns `409 Conflict`.
- Output streaming via Server-Sent Events (`GET /api/jobs/{id}/events`).
- Redaction pipeline applied line-by-line before yielding chunks to the client.
- Job execution logs persisted under `results/ui_jobs/<job_id>/`.

---

## 4. Frontend Component Hierarchy & Design System

The frontend adopts the brutalist forensic aesthetic established by the hackathon submission:
- **Palette**: Pitch dark (`#0a0a0a`), carbon surface (`#101010`), crisp gray border (`#232323`), high-contrast text (`#ededed`).
- **Semantic Badges**:
  - `ALLOW` (Green `#46a758`)
  - `DENY` (Red `#e5484d`)
  - `HOLD` (Amber `#f5a524`)
  - `TAMPER_DETECTED` (Distinct red badge with exclamation mark)
- **Data Integrity**: Every counter, badge, table cell, and log line is bound directly to an API endpoint. No Math.random, no setTimeout fake progress, no hardcoded counts.

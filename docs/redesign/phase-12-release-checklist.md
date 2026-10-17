# Phase 12: Production Release Checklist & Verification Audit

## 1. Release Identification
- **Project**: TripLine (Governed AI Agent Execution & Cryptographic Verification)
- **Branch**: `agent-v2`
- **Base Commit**: `9b51028`
- **Target Topology**: FastAPI Server (`server.py` / `dashboard/app.py`) serving Next.js Static Export (`tripline-frontend/out/`).
- **Date**: 2026-10-17

## 2. Gate Verification & Test Matrix

| Validation Stage | Target / Command | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Frontend Static Build** | `npm run build --prefix tripline-frontend` | **PASS (14/14 pages)** | Turbopack generated 14 routes in ~620ms to `tripline-frontend/out/` |
| **TypeScript Typecheck** | `tsc --noEmit` (in `tripline-frontend`) | **PASS (0 errors)** | Full strict typing across all React components, APIs, and models |
| **Backend Integration Tests**| `pytest tests/test_phase4_dashboard.py tests/test_phase10_dashboard.py tests/test_dashboard_api.py tests/test_phase9_api.py` | **PASS (54/54 passed)** | Zero regressions across router routing, receipts, and API endpoints |
| **Complete Pytest Suite** | `pytest tests/` | **PASS (294 passed, 22 skipped)** | 22 live ArmorIQ tests skipped safely due to missing cloud API key |
| **Secret & Test Hygiene** | `pytest tests/test_test_hygiene.py` | **PASS (3/3 passed)** | Zero secrets or dirty evidence files committed |
| **Two-Way UI/API Coverage**| `python scripts/ui_api_coverage.py` | **PASS (100% matched)** | Every API endpoint maps to tested UI elements; all compliance anchors intact |

## 3. Router Collision Resolution (Phase 4)
- Fixed FastAPI dual-router precedence in `dashboard/app.py`.
- Next.js static exports (`/receipts`, `/witness`, `/measured`, `/claims`, `/layers`, `/console`, `/agent`, `/jail-burst`) now take precedence over legacy views.
- Retained legacy compatibility redirects and fallbacks for `/boundary`, `/scoreboard`, and `/about`.

## 4. Four-Plane Isometric Architecture Scene (Phase 5 & 6)
- Pure layered SVG + hardware-accelerated CSS 3D perspective (`perspective: 1400px`, `transform-style: preserve-3d`).
- No heavy WebGL or Three.js dependencies.
- Planar 2D projection toggle for mobile and reduced-motion environments.
- Zero synthetic mock IDs; bound to real disk receipts.

## 5. Security & Truth Invariants (Rule 10 Audit)
- **No Fabricated Data**: Removed synthetic `RCP-20261016-*` mock cards from `/agent`; replaced with verified empty state and honest backend job history.
- **Fail-Closed Mode B**: Mode B remains active; unauthorized operations are denied at the boundary.
- **Cryptographic Verification**: Backend verifiers (`/api/receipts/{id}/verify` and `/api/witness/verify`) act as the sole authority. Tamper checks execute against temporary in-memory copies without mutating original artifacts.
- **Live vs Offline Clarity**: Offline deterministic proof jobs (Path Jail Fuzzer, Cryptographic Link Verification, Multi-Layer Scenario) are clearly labelled and distinct from live remote ArmorIQ runs.

## 6. Deployment & Demonstration Status
- **FastAPI Production Server**: Verified serving on `http://127.0.0.1:8000/`.
- **Live ArmorIQ Credentials**: Documented as unavailable in current local environment. Fail-closed Mode B protects execution; deterministic local proof jobs run flawlessly.

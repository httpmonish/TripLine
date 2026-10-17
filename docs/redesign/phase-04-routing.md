# Phase 4 — Shared Shell, Serving Path & Route Consolidation Specification

**Project:** TripLine  
**Branch:** `agent-v2` (`9b51028`)  
**Components:** `dashboard/app.py`, `dashboard/routes.py`, `tripline-frontend/out/`  
**Author:** Staff Full-Stack Engineer & Application Security Architect  
**Status:** Approved & Implemented  

---

## 1. Route Serving Architecture & Problem Resolution

### 1.1 The Pre-Phase 4 Dual-Router Collision
In Phase 1, an architectural mismatch was identified:
In `dashboard/app.py`, `app.include_router(legacy_router)` was mounted **before** `@app.get("/{slug}")`. Because `legacy_router` defined server-rendered Jinja handlers for `/receipts`, `/attribution`, and `/measured`, requests to those endpoints served legacy HTML templates, shadowing modern Next.js exported pages (`out/receipts.html`, `out/attribution.html`, `out/measured.html`).

### 1.2 Implemented Resolution Policy
The routing precedence in `dashboard/app.py` has been re-architected into a strict 7-tier hierarchy:

```
[Incoming Request]
       |
       v
1. API Router (/api/...)
       | (No match)
       v
2. Root Single-Page Application (GET /) -> tripline-frontend/out/index.html
       | (No match)
       v
3. Next.js Exported Pages (GET /{slug}) -> tripline-frontend/out/{slug}.html
       |-- Serves /receipts, /attribution, /measured, /agent, /witness, /claims, etc.
       +-- If no static file, delegates to legacy handlers for backward compatibility:
           - /boundary -> boundary_view
           - /scoreboard -> scoreboard_view
           - /about -> about_view
       | (No match)
       v
4. Legacy Router -> Deep detail routes:
       - /receipts/{identifier} (Receipt inspection detail)
       - /runs/{run_id} (Historical run detail)
       | (No match)
       v
5. Static Assets Chunk Mount (/_next/...)
       | (No match)
       v
6. Local Static Asset Mount (/static/...)
       | (No match)
       v
7. Fallback Root Assets (/favicon.ico, /tripline-lockup.svg, etc.)
```

---

## 2. Security Middleware & Header Preservation

All responses—whether served from Next.js static exports, dynamic API endpoints, or legacy Jinja views—strictly pass through `SecurityHeadersMiddleware`:
* `Content-Security-Policy`: Restricts scripts, styles, fonts, and forbids unsafe inline execution.
* `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
* `X-Frame-Options: DENY`: Prevents clickjacking and framing.
* `Strict-Transport-Security`: Enforces TLS on production origins.

---

## 3. Verification & Regression Matrix

| Route | Handler / Target | Served Content | Test Contract |
| :--- | :--- | :--- | :--- |
| `GET /` | `serve_root` | `tripline-frontend/out/index.html` | `test_routes_status_200`, `test_1_dashboard_root_loads` |
| `GET /receipts` | `serve_frontend_page` | `tripline-frontend/out/receipts.html` | `test_2_receipt_list_loads` (`Incident Receipts`) |
| `GET /attribution` | `serve_frontend_page` | `tripline-frontend/out/attribution.html` | `test_routes_status_200` (`TRIPLINE`) |
| `GET /measured` | `serve_frontend_page` | `tripline-frontend/out/measured.html` | `test_routes_status_200` (`TRIPLINE`) |
| `GET /about` | `serve_frontend_page` | `dashboard.routes.about_view` | `test_routes_status_200` (`TRIPLINE`) |
| `GET /boundary` | `serve_frontend_page` | `dashboard.routes.boundary_view` | `test_7_boundary_page_loads` (HTTP 200) |
| `GET /scoreboard` | `serve_frontend_page` | `dashboard.routes.scoreboard_view` | `test_8_scoreboard_loads` (HTTP 200) |
| `GET /receipts/{id}`| `legacy_router` | Jinja `templates/receipt_detail.html` | `test_3_attack_a_receipt_renders`, `test_receipt_detail_and_verify` |
| `POST /api/receipts/{id}/verify` | `api_router` | JSON verification response | `test_receipt_detail_and_verify` (VERIFIED) |

---

## 4. Phase Gate Acceptance Criteria Check

- [x] **Next.js Static Export Precedence:** Modern exported pages served on `/receipts`, `/measured`, `/attribution`.
- [x] **No Legacy Collisions:** Old Jinja pages do not shadow modern frontend routes.
- [x] **Compatibility Preserved:** Detailed forensic views (`/receipts/{id}`, `/runs/{id}`) and legacy tests pass (37/37 passed).
- [x] **UI/API Coverage:** `scripts/ui_api_coverage.py` confirms 100% two-way match.

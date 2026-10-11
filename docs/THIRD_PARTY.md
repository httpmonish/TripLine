# Third-Party Dependencies and Licenses

Generated via `pip freeze` and `pip list` in `.venv313` (Python 3.13.16).

---

## 1. Core Runtime Dependencies

| Package | Version | License | Primary Architectural Purpose |
|---|---|---|---|
| `armoriq-sdk` | 0.6.10 | Proprietary (ArmorIQ AI Inc.) | Platform SDK for policy checking & enforcement via `/iap/sdk/enforce` |
| `mcp` | 2.2.0 | MIT | Model Context Protocol server implementation |
| `mcp-types` | 2.2.0 | MIT | MCP schema dataclasses and protocol definitions |
| `fastapi` | 0.142.2 | MIT | Read-only judge-facing dashboard web framework |
| `starlette` | 1.7.0 | BSD-3-Clause | Underlying ASGI toolkit for FastAPI |
| `uvicorn` | 0.54.0 | BSD-3-Clause | ASGI server worker |
| `pydantic` | 2.13.5 | MIT | Receipt and attack schema data modeling and validation |
| `Jinja2` | 3.1.6 | BSD-3-Clause | Server-side template engine for truthful dashboard |
| `httpx` / `httpx2` | 0.28.1 / 2.13.1 | BSD-3-Clause | Async and sync HTTP transport for client checks |
| `cryptography` | 50.0.2 | Apache-2.0 / BSD | Low-level cryptographic primitives |
| `PyJWT` | 2.15.1 | MIT | Token serialization and signing |
| `python-dotenv` | 1.2.4 | BSD-3-Clause | Optional `.env` configuration loader |
| `PyYAML` | 6.0.3 | MIT | Scenario YAML parsing |

---

## 2. Test & Verification Dependencies

| Package | Version | License | Primary Architectural Purpose |
|---|---|---|---|
| `pytest` | 9.1.1 | MIT | Automated testing framework |
| `pytest-asyncio` | 1.4.0 | Apache-2.0 | Async test runner |
| `anyio` | 4.15.1 | MIT | Async compatibility layer |
| `imageio-ffmpeg` | 0.6.0 | BSD-2-Clause | Standalone binary wrapper for ffmpeg video encoding |
| `pillow` | 12.3.0 | HPND / MIT-like | Keyframe and terminal frame image rendering |

---

## 3. UI Assets & Fonts
- **Dashboard Fonts:** System native font stacks only (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `ui-monospace`, `Menlo`). Zero external font files or CDN calls.
- **Brand Wordmark:** Outlined Inter Display SemiBold (designed by Rasmus Andersson). Licensed under the SIL Open Font License, Version 1.1 (SIL OFL 1.1). Stored as vector paths (outlines) directly inside SVG assets (`assets/brand/`) — zero font downloads or remote calls required. Full license preserved in [`assets/brand/OFL.txt`](file:///Users/themonishnawaz/tripline/assets/brand/OFL.txt).
- **Video Fonts:** Standard system monospace (`Courier New`) and sans-serif (`Arial`) bundled locally under `video/fonts/`.
- **Icons:** Inline SVG and local vector brand assets (`assets/brand/`). Zero external icon libraries or CDN requests.

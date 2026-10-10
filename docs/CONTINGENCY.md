# Tripline Contingency & Incident Playbook

**Hackathon**: ArmorIQ "Flow State 2026"  
**Submission Window**: 15–17 Oct 2026  
**Core Principle**: *Never simulate, mock, or fake a live run. If a live dependency fails, fallback to recorded evidence and label it with date and commit hash.*

---

## Contingency Matrix

| # | Failure Scenario | Symptom | Detection | Immediate Action | What May Be Said Publicly / In Demo |
|---|---|---|---|---|---|
| **1** | **ArmorIQ Platform Unreachable** | `scripts/armoriq_proof.py` or agent raises `httpx.ConnectError` / HTTP 5xx. | Trace ID missing; non-200 HTTP status code from `api.armoriq.ai`. | 1. Check network connectivity.<br>2. Run `scripts/armoriq_proof.py` once to confirm endpoint status.<br>3. Switch to offline evidence: `make verify && make dashboard`. | *"The live ArmorIQ gateway is unreachable; demonstrating enforcement using our recorded run from 10 Oct 2026, commit 2333590."* |
| **2** | **ArmorIQ Rate Limited** | HTTP 429 response from `https://api.armoriq.ai/iap/sdk/enforce`. | Response body contains `rate_limit_exceeded` or HTTP 429. | 1. Back off 30 seconds.<br>2. If still limited, use `results/phase3/scenario/` authentic evidence files.<br>3. Do NOT spam requests. | *"Platform rate limit encountered; displaying verified scenario receipts recorded at commit 2333590."* |
| **3** | **LLM API Down or Rate-Limited** | `make wow` hangs or Anthropic API throws HTTP 429 / 500 / Overloaded. | Agent stderr prints `anthropic.RateLimitError` or `APIConnectionError`. | 1. Switch immediately to deterministic probe sweep `scripts/jail_burst.py` (requires zero LLM calls).<br>2. Or launch `make dashboard` showing real recorded Claude 3.5 run. | *"Anthropic API is currently overloaded; running the deterministic probe harness and displaying recorded Claude 3.5 Sonnet run from 10 Oct 2026."* |
| **4** | **Model Refuses Adversarial Instructions** | Real LLM politely declines to execute poisoned issue instructions ("I cannot assist with deleting branches..."). | Agent logs show issue closed with refusal text; tool call not proposed. | 1. Explain model refusal variance (observed 40% in our benchmarks).<br>2. Run `scripts/jail_burst.py` to exercise the path jail and egress gateway deterministically.<br>3. Run `make verify && make tamper`. | *"The model refused the adversarial prompt—a common occurrence in frontier LLMs (observed 40% refusal). We run our deterministic probe harness to verify the guardrail boundaries."* |
| **5** | **API Key Expired or Revoked** | HTTP 401 / 403 `Unauthorized` from `api.armoriq.ai` or Anthropic. | `armoriq_sdk` raises AuthException; invalid token error. | 1. Rotate key in platform dashboard.<br>2. Update local `.env` (never commit keys).<br>3. Verify with `scripts/armoriq_proof.py`. | *"Key rotation in progress; displaying offline verified receipts."* |
| **6** | **`make wow` Slower Than Expected (> 45s)** | Agent takes > 45s to complete the 5-issue queue. | Wall clock time exceeds threshold due to Claude token streaming latency. | 1. Allow run to finish if under 60s.<br>2. For quick live judging, demonstrate single-issue or use `scripts/jail_burst.py` (< 4s total). | *"Live agent processing includes multi-turn reasoning latency; for immediate verification, run make verify and scripts/jail_burst.py."* |
| **7** | **Dashboard Port In Use (8000)** | `OSError: [Errno 48] Address already in use: ('127.0.0.1', 8000)`. | Uvicorn crashes on startup. | 1. Launch dashboard on alternative port: `.venv/bin/uvicorn dashboard.app:app --port 8099`.<br>2. Or find and kill conflicting process: `lsof -ti:8000 \| xargs kill -9`. | *"Dashboard started on alternative port http://127.0.0.1:8099."* |
| **8** | **Judge On Non-Pinned Python Version (< 3.12)** | `SyntaxError` or missing stdlib features on Python 3.10/3.11. | `python --version` outputs < 3.12. | 1. Pinned virtualenv instructions in README specify Python ≥ 3.12.<br>2. If judge cannot install 3.12, direct them to inspect static Canonical JSON receipts in `results/` or run `make verify` via uv/pyenv. | *"Tripline targets Python 3.12/3.13 standard type syntax; please use a Python ≥ 3.12 virtualenv or uv."* |
| **9** | **Video Upload Size or Format Rejected** | Portal rejects video file (> 25MB or encoding issue). | Upload dialog displays error message. | 1. Submit `video/out/tripline_demo_90s_lowbitrate.mp4` (1.29 MB, 1080p).<br>2. Upload `video/out/tripline_demo_90s.mp4` to YouTube (Unlisted) or Google Drive, paste link in video URL field. | Provide fallback YouTube / Loom stream URL in submission description. |
| **10** | **GitHub Repository Host Unavailable** | GitHub experiencing service outage or packet drops. | Git push fails with timeout or HTTP 500. | 1. Check `githubstatus.com`.<br>2. Retry after 5 minutes.<br>3. If persistent near deadline, prepare local zip bundle of submission directory (minus `.git/` and `.venv/`) as emergency backup. | Contact hackathon organizers via Discord with timestamped bundle hash if close to deadline. |

---

## Fallback Labeling Standard (Rule R1)

Whenever recorded evidence is presented as a fallback:
> **"Recorded on 10 Oct 2026, commit `2333590` (Phase 3 measured run). Real execution logs with authentic ArmorIQ trace `06ff60f0-7696-4922-a98f-d60528e62249`."**

Never present pre-recorded output as a real-time live execution.

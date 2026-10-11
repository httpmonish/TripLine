"""
conftest.py — pytest configuration for Tripline test suite.

Key design decisions:
- MCP server is started in pytest_configure (before collection) so module-level
  `needs_mcp` skipif guards see the server as running. This fixes the 20-skip
  regression where skipif fired before the session fixture could start the server.
- Any stale server on port 8000 is killed first for determinism.
- Telemetry is disabled before any ArmorIQ SDK import.
- ArmorIQ tests are marked @pytest.mark.armoriq and run by `make test-armoriq`.
- Exit code is always accurate: make test exits 0 only on zero failures.
"""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time

import pytest

# ── 0. Silence ArmorIQ telemetry BEFORE any SDK import ─────────────────────
# The SDK checks os.getenv("ARMORIQ_OBSERVABILITY") in session.py:
# if env_flag in ("false", "0", "no", "off"): enabled = False.
# This prevents ObservabilityShipper background thread from ever starting.
os.environ["ARMORIQ_OBSERVABILITY"] = "0"

# ── 1. Project root on sys.path ─────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── 2. Marker registration ───────────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "armoriq: tests that require a live ArmorIQ API key (run via make test-armoriq)",
    )


# ── 3. Port helpers ──────────────────────────────────────────────────────────
def _port_open(port: int, timeout: float = 0.3) -> bool:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.close()
        return True
    except OSError:
        return False


def _kill_occupant(port: int) -> None:
    """Best-effort kill of any process listening on port."""
    try:
        r = subprocess.run(
            ["lsof", "-nP", "-i", f":{port}", "-t"],
            capture_output=True, text=True, timeout=5,
        )
        for pid in r.stdout.splitlines():
            pid = pid.strip()
            if pid:
                try:
                    subprocess.run(["kill", "-9", pid], timeout=3, check=False)
                except Exception:
                    pass
        if r.stdout.strip():
            time.sleep(0.6)  # wait for kernel to reclaim port
    except Exception:
        pass


# ── 4. Start MCP server BEFORE collection so module-level skipif sees it ────
#
# pytest_configure runs before test collection; session fixtures run after.
# Module-level `needs_mcp = pytest.mark.skipif(not _mcp_server_reachable())`
# evaluates at *import time*, which happens during collection.  By starting the
# server here we guarantee it is up when those guards are evaluated.

_SERVER_PROC: subprocess.Popen | None = None
_MCP_PORT: int = 8000


def _ensure_server_running(port: int = 8000) -> None:
    global _SERVER_PROC, _MCP_PORT
    if _SERVER_PROC is not None and _SERVER_PROC.poll() is None and _port_open(port, timeout=0.1):
        return

    if _port_open(port, timeout=0.2):
        _kill_occupant(port)

    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    proc = subprocess.Popen(
        [sys.executable, "server.py", "--port", str(port)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )

    deadline = time.time() + 10.0
    while time.time() < deadline:
        if _port_open(port, timeout=0.2):
            break
        time.sleep(0.1)
    else:
        proc.terminate()
        pytest.exit(f"MCP server failed to start on port {port} within 10 s", returncode=3)

    _SERVER_PROC = proc
    _MCP_PORT = port
    os.environ["MCP_TEST_PORT"] = str(port)


def pytest_sessionstart(session):
    """Start the MCP server before any test runs (and before collection)."""
    _ensure_server_running(8000)
    atexit.register(_stop_server)


@pytest.fixture(autouse=True)
def ensure_mcp_alive():
    _ensure_server_running(8000)
    yield


def _stop_server():
    global _SERVER_PROC
    if _SERVER_PROC is not None:
        _SERVER_PROC.terminate()
        try:
            _SERVER_PROC.wait(timeout=3.0)
        except Exception:
            _SERVER_PROC.kill()
        _SERVER_PROC = None
    os.environ.pop("MCP_TEST_PORT", None)


def pytest_sessionfinish(session, exitstatus):
    _stop_server()


# ── 5. Fixture for tests that want the MCP URL ───────────────────────────────
@pytest.fixture(scope="session")
def mcp_server_session():
    """Yield the port the session MCP server is on."""
    yield _MCP_PORT


@pytest.fixture
def mcp_port(mcp_server_session):
    return mcp_server_session


# ── 6. Skip helper for tests requiring ArmorIQ key ───────────────────────────
@pytest.fixture
def skip_if_no_armoriq_key():
    """Skip test if no ArmorIQ API key is available."""
    import json, pathlib
    key = os.environ.get("ARMORIQ_API_KEY", "")
    if not key:
        try:
            cred = pathlib.Path.home() / ".armoriq" / "credentials.json"
            if cred.exists():
                data = json.loads(cred.read_text())
                key = data.get("apiKey", "")
        except Exception:
            pass
    if not key or not key.startswith("ak_"):
        pytest.skip(
            "ARMORIQ_API_KEY not set — use make test-armoriq for ArmorIQ integration tests"
        )


# ── 7. Warn about skip counts after the session ──────────────────────────────
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    skipped = terminalreporter.stats.get("skipped", [])
    if skipped:
        by_reason: dict[str, int] = {}
        for rep in skipped:
            reason = getattr(rep, "wasxfail", None) or ""
            if not reason:
                longrepr = str(getattr(rep, "longrepr", ""))
                reason = longrepr.split("Skipped: ")[-1].split("\n")[0].strip()
            by_reason[reason] = by_reason.get(reason, 0) + 1

        terminalreporter.write_sep("=", "SKIP SUMMARY")
        for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
            tag = "[armoriq]" if "ARMORIQ" in reason.upper() or "armoriq" in reason.lower() else "[other]"
            terminalreporter.write_line(f"  {tag} x{count}: {reason}")
        armoriq_skips = sum(v for k, v in by_reason.items()
                           if "armoriq" in k.lower() or "ARMORIQ" in k.upper())
        if armoriq_skips:
            terminalreporter.write_line(
                f"\n  NOTE: {armoriq_skips} ArmorIQ integration test(s) skipped."
                " Run: make test-armoriq"
            )


# ── 8. Test hygiene: Isolate events.jsonl to temporary file ─────────────────
@pytest.fixture(autouse=True, scope="session")
def isolate_events_file(tmp_path_factory):
    tmp_events = tmp_path_factory.mktemp("events") / "events.jsonl"
    old = os.environ.get("TRIPLINE_EVENTS_FILE")
    os.environ["TRIPLINE_EVENTS_FILE"] = str(tmp_events)
    yield
    if old:
        os.environ["TRIPLINE_EVENTS_FILE"] = old
    else:
        os.environ.pop("TRIPLINE_EVENTS_FILE", None)


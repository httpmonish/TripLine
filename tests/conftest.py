"""
conftest.py — pytest configuration for Tripline Phase 0 tests.

Adds the project root to sys.path so that armoriq_helper, server, etc.
can be imported from tests/test_phase0.py without packaging.
"""

import sys
import os

# Ensure the project root is first on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import socket
import subprocess
import time
import pytest

@pytest.fixture(scope="session", autouse=True)
def ensure_mcp_server():
    server = None
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_running = (s.connect_ex(('127.0.0.1', 8000)) == 0)
    s.close()
    if not is_running:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        server = subprocess.Popen([sys.executable, "server.py"], env=env)
        for _ in range(50):
            time.sleep(0.1)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if s.connect_ex(('127.0.0.1', 8000)) == 0:
                s.close()
                break
            s.close()

    try:
        yield
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=2.0)
            except Exception:
                server.kill()


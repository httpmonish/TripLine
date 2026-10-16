"""
agent/safety.py — Safety Rails, Caps, Kill Switch, and Secret Redaction for Tripline Agent v2
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import re
import time
from typing import Any, Dict, List, Optional, Union

# Regex patterns matching key-shaped strings
RE_SECRETS = [
    re.compile(r"ak_live_[a-zA-Z0-9_\-]+"),
    re.compile(r"AQ\.[a-zA-Z0-9_\-\.]+"),
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
]

KILL_SWITCH_FILE = pathlib.Path(".tripline_kill_switch")


def redact_secrets(val: Any) -> Any:
    """
    Recursively scans strings, dicts, lists and replaces key-shaped secrets with [REDACTED].
    """
    if isinstance(val, str):
        redacted = val
        for pat in RE_SECRETS:
            redacted = pat.sub("[REDACTED]", redacted)
        return redacted
    elif isinstance(val, dict):
        return {k: redact_secrets(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [redact_secrets(v) for v in val]
    elif isinstance(val, tuple):
        return tuple(redact_secrets(v) for v in val)
    return val


@dataclasses.dataclass
class SafetyBudget:
    max_tool_calls_per_run: int = 25
    max_wall_clock_seconds: float = 180.0
    max_sessions: int = 40
    current_tool_calls: int = 0
    start_time: float = dataclasses.field(default_factory=time.time)
    killed: bool = False

    def check_active(self) -> None:
        """
        Raises RuntimeError if any safety budget is exhausted or kill switch is active.
        """
        if self.killed or KILL_SWITCH_FILE.exists():
            raise RuntimeError("Agent execution terminated by kill switch.")

        if self.current_tool_calls > self.max_tool_calls_per_run:
            raise RuntimeError(f"Safety limit reached: max tool calls ({self.max_tool_calls_per_run}) exhausted.")

        elapsed = time.time() - self.start_time
        if elapsed > self.max_wall_clock_seconds:
            raise RuntimeError(f"Safety limit reached: wall-clock timeout ({self.max_wall_clock_seconds}s) exceeded.")

    def record_tool_call(self) -> None:
        self.current_tool_calls += 1
        self.check_active()


def trigger_kill_switch() -> None:
    KILL_SWITCH_FILE.write_text("STOP\n", encoding="utf-8")


def clear_kill_switch() -> None:
    if KILL_SWITCH_FILE.exists():
        KILL_SWITCH_FILE.unlink()

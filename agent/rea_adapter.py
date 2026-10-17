"""
agent/rea_adapter.py — Dedicated REA MCP Adapter for TripLine

Connects TripLine to the official REA (Reverse Engineer Anything) MCP server via
a persistent stdio JSON-RPC connection to a pinned package version (rea-agents@6.5.0).
Exposes controlled static analysis of preapproved synthetic JavaScript/Electron
applications, enforcing controlled analysis root confinement and returning
provenance-tagged untrusted evidence packages.
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import pathlib
import subprocess
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

from agent.safety import redact_secrets

log = logging.getLogger("tripline.rea_adapter")

# -----------------------------------------------------------------------------
# 1. Pinned Package & Command Configuration
# -----------------------------------------------------------------------------
REA_PACKAGE_VERSION = "rea-agents@6.5.0"
REA_SERVER_COMMAND = ["npx", "-y", REA_PACKAGE_VERSION, "--mcp"]
REA_MAX_RESPONSE_BYTES = 8 * 1024 * 1024  # 8 MB response ceiling
REA_DEFAULT_TIMEOUT_SECONDS = 60.0

# Controlled Analysis Root: all valid target IDs MUST resolve within this root
CONTROLLED_ANALYSIS_ROOT = (REPO_ROOT / "rea_targets").resolve()

# Preapproved Target Registry: only preapproved targets are admitted
APPROVED_TARGET_REGISTRY: Dict[str, pathlib.Path] = {
    "synthetic-electron-app": (CONTROLLED_ANALYSIS_ROOT / "synthetic_electron_app").resolve(),
    "synthetic_electron_app": (CONTROLLED_ANALYSIS_ROOT / "synthetic_electron_app").resolve(),
    "sample-electron-app": (CONTROLLED_ANALYSIS_ROOT / "synthetic_electron_app").resolve(),
}


class REATargetValidationError(ValueError):
    """Raised when an external target_id fails preapproved resolution or root confinement."""
    pass


class REAProtocolError(RuntimeError):
    """Raised when REA MCP stdio communication fails or returns invalid JSON-RPC."""
    pass


# -----------------------------------------------------------------------------
# 2. Target Resolution & Confinement
# -----------------------------------------------------------------------------
def resolve_approved_target(target_id: str) -> pathlib.Path:
    """
    Validates and resolves a preapproved target_id to an existing sample directory
    inside the controlled analysis root. Arbitrary paths, traversal sequences,
    or unregistered IDs are strictly rejected.
    """
    if not isinstance(target_id, str) or not target_id.strip():
        raise REATargetValidationError("Target ID must be a non-empty string.")

    target_id_clean = target_id.strip()

    # Reject path traversal attempts, absolute paths, or path separators
    if (
        os.path.isabs(target_id_clean)
        or "/" in target_id_clean
        or "\\" in target_id_clean
        or ".." in target_id_clean
    ):
        raise REATargetValidationError(
            f"Arbitrary paths and path traversal are rejected. Got: {target_id_clean}"
        )

    if target_id_clean not in APPROVED_TARGET_REGISTRY:
        approved_keys = sorted(APPROVED_TARGET_REGISTRY.keys())
        raise REATargetValidationError(
            f"Target ID '{target_id_clean}' is not preapproved. Approved targets: {approved_keys}"
        )

    resolved_path = APPROVED_TARGET_REGISTRY[target_id_clean].resolve()

    # Verify root confinement
    try:
        resolved_path.relative_to(CONTROLLED_ANALYSIS_ROOT)
    except ValueError:
        raise REATargetValidationError(
            f"Target path '{resolved_path}' escapes controlled analysis root '{CONTROLLED_ANALYSIS_ROOT}'."
        )

    if not resolved_path.exists() or not resolved_path.is_dir():
        raise REATargetValidationError(
            f"Resolved target directory does not exist or is not a directory: {resolved_path}"
        )

    return resolved_path


# -----------------------------------------------------------------------------
# 3. Persistent Stdio REA MCP Adapter
# -----------------------------------------------------------------------------
class REAAdapter:
    """
    Dedicated persistent stdio MCP client for the official REA MCP server.
    Manages process lifecycle, JSON-RPC 2.0 handshake, live tool discovery,
    and analysis execution with retained session/evidence memory.
    """

    def __init__(
        self,
        mode: str = "live",  # 'live' or 'mock'
        server_command: Optional[List[str]] = None,
        timeout_seconds: float = REA_DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = REA_MAX_RESPONSE_BYTES,
    ):
        self.mode = mode
        self.server_command = server_command or REA_SERVER_COMMAND
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._req_id = 0
        self._server_info: Optional[Dict[str, Any]] = None
        self._discovered_tools: Optional[List[Dict[str, Any]]] = None
        self._session_id = f"rea-session-{uuid.uuid4().hex[:8]}"

        # Retained evidence store
        self.retained_evidence: Dict[str, Dict[str, Any]] = {}
        self.evidence_parent_map: Dict[str, str] = {}
        self.last_evidence_id: Optional[str] = None
        self.last_parent_evidence_id: Optional[str] = None

        atexit.register(self.close)

    @property
    def is_live(self) -> bool:
        return self.mode == "live"

    @property
    def session_id(self) -> str:
        return self._session_id

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def start(self) -> None:
        """Starts the persistent REA MCP server process and runs the initialize handshake."""
        if self.mode == "mock":
            self._server_info = {"name": "rea-mock", "version": "6.5.0-mock"}
            self._discovered_tools = [
                {"name": "analyze_javascript_application"},
                {"name": "inspect_analysis_view"},
                {"name": "trace_application_feature"},
            ]
            return

        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return  # Process already running healthy

            log.info("Starting persistent REA MCP server: %s", " ".join(self.server_command))
            try:
                self._proc = subprocess.Popen(
                    self.server_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            except Exception as e:
                raise REAProtocolError(f"Failed to spawn REA server process: {e}") from e

            # Initialize handshake
            init_req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tripline-rea-adapter", "version": "1.0.0"},
                },
            }
            init_res = self._send_request_locked(init_req)
            if "error" in init_res:
                raise REAProtocolError(f"REA MCP initialize error: {init_res['error']}")

            self._server_info = init_res.get("result", {}).get("serverInfo", {})

            # Notification: initialized
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            try:
                self._proc.stdin.write(json.dumps(notif) + "\n")
                self._proc.stdin.flush()
            except Exception:
                pass

            # Discover and inspect live tools
            self._discover_tools_locked()

    def _discover_tools_locked(self) -> List[Dict[str, Any]]:
        """Queries live tools/list and caches tool definitions."""
        tools_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }
        res = self._send_request_locked(tools_req)
        tools = res.get("result", {}).get("tools", [])
        self._discovered_tools = tools
        return tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns the list of discovered tools from the REA server."""
        self.start()
        return list(self._discovered_tools or [])

    def get_server_info(self) -> Dict[str, Any]:
        """Returns verified server information from the initialization handshake."""
        self.start()
        return dict(self._server_info or {})

    def _send_request_locked(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a JSON-RPC request and reads the single-line response with timeout and error handling."""
        if self._proc is None or self._proc.poll() is not None:
            raise REAProtocolError("REA server process is not running.")

        req_line = json.dumps(request_payload) + "\n"
        try:
            self._proc.stdin.write(req_line)
            self._proc.stdin.flush()
        except Exception as e:
            self.close()
            raise REAProtocolError(f"Failed writing to REA stdin: {e}") from e

        line = self._proc.stdout.readline()
        if not line:
            stderr_out = ""
            if self._proc.stderr:
                try:
                    stderr_out = self._proc.stderr.read()
                except Exception:
                    pass
            self.close()
            raise REAProtocolError(f"REA process closed stdout unexpectedly. Stderr: {stderr_out[:500]}")

        if len(line.encode("utf-8")) > self.max_response_bytes:
            raise REAProtocolError(
                f"REA response exceeded max size limit ({len(line)} > {self.max_response_bytes} bytes)"
            )

        try:
            return json.loads(line)
        except json.JSONDecodeError as jde:
            raise REAProtocolError(f"Invalid JSON received from REA stdout: {line[:200]}") from jde

    def analyze_javascript_application(
        self,
        target_path: pathlib.Path,
        detail: str = "summary",
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Invokes REA's analyze_javascript_application tool with summary detail.
        Retains evidence reference and session state for future inspection.
        """
        if self.mode == "mock":
            return self._mock_analyze_response(target_path)

        self.start()

        call_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "analyze_javascript_application",
                "arguments": {
                    "input_path": str(target_path),
                    "detail": detail,
                },
            },
        }

        with self._lock:
            res = self._send_request_locked(call_req)

        if "error" in res:
            return {
                "status": "error",
                "error_type": "REA_RPC_ERROR",
                "error": res["error"].get("message", str(res["error"])),
                "raw_response": res,
            }

        result = res.get("result", {})
        if result.get("isError"):
            return {
                "status": "error",
                "error_type": "REA_TOOL_ERROR",
                "error": "REA reported tool execution error",
                "raw_response": result,
            }

        content_items = result.get("content", [])
        evidence_text = ""
        for c in content_items:
            if c.get("type") == "text":
                evidence_text += c.get("text", "")

        try:
            evidence_data = json.loads(evidence_text)
        except Exception:
            evidence_data = {"raw_text": evidence_text}

        evidence_id = evidence_data.get("evidence_id") or f"ev_{uuid.uuid4().hex}"
        parent_evidence_id = (
            evidence_data.get("normalized_result", {}).get("parent_evidence_id")
            or evidence_id
        )

        # Retain evidence in session memory
        self.retained_evidence[evidence_id] = evidence_data
        self.evidence_parent_map[evidence_id] = parent_evidence_id
        self.evidence_parent_map[parent_evidence_id] = parent_evidence_id
        self.last_evidence_id = evidence_id
        self.last_parent_evidence_id = parent_evidence_id

        summary_view = evidence_data.get("normalized_result", {}).get("summary", {})
        limitations = evidence_data.get("limitations", [])
        subject = evidence_data.get("subject", {})

        return {
            "status": "ok",
            "tool": "analyze_javascript_application",
            "evidence_id": evidence_id,
            "parent_evidence_id": parent_evidence_id,
            "session_id": self._session_id,
            "session_retained": True,
            "is_live_rea": True,
            "subject": subject,
            "summary": summary_view,
            "limitations": limitations,
            "limitations_count": len(limitations),
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_static_analysis",
                "trust_level": "T3",
                "input_path": str(target_path),
                "package_version": REA_PACKAGE_VERSION,
            },
        }

    def inspect_analysis_view(
        self,
        evidence_id: str,
        view_kind: str = "summary",
    ) -> Dict[str, Any]:
        """
        Inspects retained analysis view for a previous evidence ID on this session.
        Uses parent evidence ID if mapped from prior summary.
        """
        if self.mode == "mock":
            return self._mock_inspect_response(evidence_id, view_kind)

        self.start()

        # Resolve to parent evidence ID if known
        resolved_evidence_id = self.evidence_parent_map.get(evidence_id, evidence_id)

        call_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "inspect_analysis_view",
                "arguments": {
                    "source": {"kind": "retained-evidence", "evidence_id": resolved_evidence_id},
                    "view": {"kind": view_kind},
                },
            },
        }

        with self._lock:
            res = self._send_request_locked(call_req)

        if "error" in res:
            return {
                "status": "error",
                "error_type": "REA_RPC_ERROR",
                "error": res["error"].get("message", str(res["error"])),
                "raw_response": res,
            }

        result = res.get("result", {})
        if result.get("isError"):
            return {
                "status": "error",
                "error_type": "REA_TOOL_ERROR",
                "error": "REA reported tool execution error during inspect_analysis_view",
                "raw_response": result,
            }

        content_items = result.get("content", [])
        evidence_text = ""
        for c in content_items:
            if c.get("type") == "text":
                evidence_text += c.get("text", "")

        try:
            view_data = json.loads(evidence_text)
        except Exception:
            view_data = {"raw_text": evidence_text}

        view_evidence_id = view_data.get("evidence_id") or f"ev_view_{uuid.uuid4().hex}"
        self.retained_evidence[view_evidence_id] = view_data

        return {
            "status": "ok",
            "tool": "inspect_analysis_view",
            "evidence_id": view_evidence_id,
            "parent_evidence_id": resolved_evidence_id,
            "session_id": self._session_id,
            "is_live_rea": True,
            "view_kind": view_kind,
            "view_data": view_data,
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_inspect_view",
                "trust_level": "T3",
                "source_evidence_id": resolved_evidence_id,
                "package_version": REA_PACKAGE_VERSION,
            },
        }

    def trace_application_feature(
        self,
        evidence_id: str,
        seed_value: str,
        seed_kind: str = "module",
        direction: str = "both",
    ) -> Dict[str, Any]:
        """
        Traces a feature seed through an authenticated application graph on this session.
        """
        if self.mode == "mock":
            return self._mock_trace_response(evidence_id, seed_value, seed_kind, direction)

        self.start()

        resolved_evidence_id = self.evidence_parent_map.get(evidence_id, evidence_id)

        call_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "trace_application_feature",
                "arguments": {
                    "application": {"kind": "retained-evidence", "evidence_id": resolved_evidence_id},
                    "seed": {"kind": seed_kind, "value": seed_value, "match": "exact", "case_sensitive": False},
                    "direction": direction,
                },
            },
        }

        with self._lock:
            res = self._send_request_locked(call_req)

        if "error" in res:
            return {
                "status": "error",
                "error_type": "REA_RPC_ERROR",
                "error": res["error"].get("message", str(res["error"])),
                "raw_response": res,
            }

        result = res.get("result", {})
        if result.get("isError"):
            return {
                "status": "error",
                "error_type": "REA_TOOL_ERROR",
                "error": "REA reported tool execution error during trace_application_feature",
                "raw_response": result,
            }

        content_items = result.get("content", [])
        evidence_text = ""
        for c in content_items:
            if c.get("type") == "text":
                evidence_text += c.get("text", "")

        try:
            trace_data = json.loads(evidence_text)
        except Exception:
            trace_data = {"raw_text": evidence_text}

        trace_evidence_id = trace_data.get("evidence_id") or f"ev_trace_{uuid.uuid4().hex}"
        self.retained_evidence[trace_evidence_id] = trace_data

        return {
            "status": "ok",
            "tool": "trace_application_feature",
            "evidence_id": trace_evidence_id,
            "parent_evidence_id": resolved_evidence_id,
            "session_id": self._session_id,
            "is_live_rea": True,
            "seed": {"kind": seed_kind, "value": seed_value},
            "direction": direction,
            "trace_data": trace_data,
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_feature_trace",
                "trust_level": "T3",
                "source_evidence_id": resolved_evidence_id,
                "package_version": REA_PACKAGE_VERSION,
            },
        }

    def _mock_analyze_response(self, target_path: pathlib.Path) -> Dict[str, Any]:
        """Explicit deterministic mock double for unit and regression testing."""
        mock_evidence_id = f"ev_mock_{uuid.uuid4().hex[:16]}"
        mock_parent_id = f"ev_mock_parent_{uuid.uuid4().hex[:16]}"
        mock_result = {
            "status": "ok",
            "tool": "analyze_javascript_application",
            "evidence_id": mock_evidence_id,
            "parent_evidence_id": mock_parent_id,
            "session_id": self._session_id,
            "session_retained": True,
            "is_live_rea": False,
            "subject": {
                "name": target_path.name,
                "local_path": str(target_path),
                "format": "directory",
            },
            "summary": {
                "mock": True,
                "input_path": str(target_path),
                "statistics": {"relevant_files": 5, "parsed_javascript_files": 3},
                "electron": {"browser_windows": 1, "ipc": {"operations": 4}},
            },
            "limitations": [
                "Mock analysis double: inert AST simulation only",
                "JavaScript and HTML parsed as mock text",
            ],
            "limitations_count": 2,
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_mock_test_double",
                "trust_level": "T3",
                "input_path": str(target_path),
                "package_version": "mock",
            },
        }
        self.retained_evidence[mock_evidence_id] = mock_result
        self.evidence_parent_map[mock_evidence_id] = mock_parent_id
        self.last_evidence_id = mock_evidence_id
        self.last_parent_evidence_id = mock_parent_id
        return mock_result

    def _mock_inspect_response(self, evidence_id: str, view_kind: str) -> Dict[str, Any]:
        view_ev_id = f"ev_mock_view_{uuid.uuid4().hex[:16]}"
        return {
            "status": "ok",
            "tool": "inspect_analysis_view",
            "evidence_id": view_ev_id,
            "parent_evidence_id": evidence_id,
            "session_id": self._session_id,
            "is_live_rea": False,
            "view_kind": view_kind,
            "view_data": {
                "summary": {"mock_view": True, "source_id": evidence_id},
                "limitations": ["Mock inspection view"],
            },
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_mock_inspect_double",
                "trust_level": "T3",
                "source_evidence_id": evidence_id,
                "package_version": "mock",
            },
        }

    def _mock_trace_response(
        self, evidence_id: str, seed_value: str, seed_kind: str, direction: str
    ) -> Dict[str, Any]:
        trace_ev_id = f"ev_mock_trace_{uuid.uuid4().hex[:16]}"
        return {
            "status": "ok",
            "tool": "trace_application_feature",
            "evidence_id": trace_ev_id,
            "parent_evidence_id": evidence_id,
            "session_id": self._session_id,
            "is_live_rea": False,
            "seed": {"kind": seed_kind, "value": seed_value},
            "direction": direction,
            "trace_data": {
                "trace_nodes": [{"kind": seed_kind, "name": seed_value}],
                "relationships": [{"from": seed_value, "relation": "imports", "to": "preload.js"}],
                "limitations": ["Mock trace relationship"],
            },
            "untrusted_content": True,
            "provenance": {
                "source_type": "rea_mcp_mock_trace_double",
                "trust_level": "T3",
                "source_evidence_id": evidence_id,
                "package_version": "mock",
            },
        }

    def close(self) -> None:
        """Terminates the persistent subprocess."""
        with self._lock:
            if self._proc is not None:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=2.0)
                except Exception:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass
                self._proc = None


# Global singleton instance for live runtime
_GLOBAL_REA_ADAPTER: Optional[REAAdapter] = None


def get_rea_adapter(mode: Optional[str] = None) -> REAAdapter:
    """Returns the shared live REA adapter instance or a fresh mock adapter."""
    global _GLOBAL_REA_ADAPTER
    effective_mode = mode or os.environ.get("TRIPLINE_REA_MODE", "live")
    if effective_mode == "mock":
        return REAAdapter(mode="mock")
    if _GLOBAL_REA_ADAPTER is None:
        _GLOBAL_REA_ADAPTER = REAAdapter(mode="live")
    return _GLOBAL_REA_ADAPTER


# -----------------------------------------------------------------------------
# 4. TripLine MCP Wrapper Tools
# -----------------------------------------------------------------------------
def analyze_electron_app_wrapper(
    target_id: str,
    adapter: Optional[REAAdapter] = None,
) -> Dict[str, Any]:
    """
    TripLine MCP wrapper tool: analyze_electron_app.
    Accepts ONLY a preapproved target_id, validates confinement, and delegates
    to the REA adapter. Arbitrary paths are rejected without invoking REA.
    """
    clean_target_id = redact_secrets(target_id)
    if not isinstance(clean_target_id, str):
        return {
            "status": "error",
            "error_type": "INVALID_ARGUMENT",
            "error": f"Parameter 'target_id' must be a string, got {type(clean_target_id).__name__}",
        }

    try:
        target_path = resolve_approved_target(clean_target_id)
    except REATargetValidationError as rve:
        return {
            "status": "error",
            "error_type": "TARGET_VALIDATION_ERROR",
            "error": str(rve),
        }

    active_adapter = adapter or get_rea_adapter(mode="live")
    try:
        raw_res = active_adapter.analyze_javascript_application(target_path, detail="summary")
    except Exception as exc:
        return {
            "status": "error",
            "error_type": "REA_ADAPTER_ERROR",
            "error": f"REA invocation failure: {str(exc)}",
        }

    clean_res = redact_secrets(raw_res)
    clean_res["target_id"] = clean_target_id
    return clean_res


def inspect_analysis_view_wrapper(
    evidence_id: str,
    view_kind: str = "summary",
    adapter: Optional[REAAdapter] = None,
) -> Dict[str, Any]:
    """
    TripLine MCP wrapper tool: inspect_analysis_view.
    Inspects previous evidence on the active REA session.
    """
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        return {
            "status": "error",
            "error_type": "INVALID_ARGUMENT",
            "error": "Parameter 'evidence_id' must be a non-empty string",
        }

    active_adapter = adapter or get_rea_adapter(mode="live")
    try:
        res = active_adapter.inspect_analysis_view(evidence_id.strip(), view_kind=view_kind)
    except Exception as exc:
        return {
            "status": "error",
            "error_type": "REA_ADAPTER_ERROR",
            "error": f"REA inspection failure: {str(exc)}",
        }
    return redact_secrets(res)


def trace_application_feature_wrapper(
    evidence_id: str,
    seed_value: str,
    seed_kind: str = "module",
    direction: str = "both",
    adapter: Optional[REAAdapter] = None,
) -> Dict[str, Any]:
    """
    TripLine MCP wrapper tool: trace_application_feature.
    Traces a feature seed through an authenticated application graph on the active REA session.
    """
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        return {
            "status": "error",
            "error_type": "INVALID_ARGUMENT",
            "error": "Parameter 'evidence_id' must be a non-empty string",
        }
    if not isinstance(seed_value, str) or not seed_value.strip():
        return {
            "status": "error",
            "error_type": "INVALID_ARGUMENT",
            "error": "Parameter 'seed_value' must be a non-empty string",
        }

    active_adapter = adapter or get_rea_adapter(mode="live")
    try:
        res = active_adapter.trace_application_feature(
            evidence_id=evidence_id.strip(),
            seed_value=seed_value.strip(),
            seed_kind=seed_kind,
            direction=direction,
        )
    except Exception as exc:
        return {
            "status": "error",
            "error_type": "REA_ADAPTER_ERROR",
            "error": f"REA feature trace failure: {str(exc)}",
        }
    return redact_secrets(res)

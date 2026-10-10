"""
agent/real_llm.py — Provider-agnostic real LLM client for Tripline Phase 1

Supports OpenAI, Anthropic, and Google Gemini APIs via native httpx calls.
Extracts raw provider response JSON for forensic audit logging.
Never prints or logs API keys.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

# Load local .env if present (gitignored)
load_dotenv()

# Predefined tool definitions matching Tripline MCP schema
TRIAGE_TOOLS_SCHEMA = [
    {
        "name": "list_issues",
        "description": "List all open repository issues to be triaged.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "read_issue",
        "description": "Read the full details, title, and body of a specific issue by its issue_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "string",
                    "description": "The unique identifier of the issue (e.g., 'issue-101')"
                }
            },
            "required": ["issue_id"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the repository (e.g., 'README.md') to verify or investigate issue reports.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path within the repository"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "comment_issue",
        "description": "Post a triage comment or recommended labels/actions to an issue.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "string",
                    "description": "The issue identifier to comment on"
                },
                "text": {
                    "type": "string",
                    "description": "The comment body containing triage assessment, labels, or findings"
                }
            },
            "required": ["issue_id", "text"]
        }
    }
]


def detect_provider() -> Tuple[str, str, str]:
    """
    Detects which LLM provider key is available in environment.
    Returns (provider_name, api_key, default_model).
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        return "gemini", gemini_key, os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return "anthropic", anthropic_key, os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return "openai", openai_key, os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        return "openai_compat", groq_key, os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    return "none", "", ""


class RealLLMClient:
    """Client for making tool-calling requests to the active LLM provider."""

    def __init__(self, provider: str = "", api_key: str = "", model: str = ""):
        if not provider or not api_key:
            detected_p, detected_k, detected_m = detect_provider()
            self.provider = provider or detected_p
            self.api_key = api_key or detected_k
            self.model = model or detected_m
        else:
            self.provider = provider
            self.api_key = api_key
            self.model = model

        if self.provider == "none" or not self.api_key:
            raise EnvironmentError(
                "No live LLM API key found in environment! "
                "Please export GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
            )

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> Tuple[Optional[str], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Sends conversation history to model.
        Returns:
            - text_response: str or None
            - tool_calls: list of dicts [{"id": str, "name": str, "arguments": dict, "raw": dict}]
            - raw_response_json: raw JSON dict from provider
        """
        if self.provider == "openai" or self.provider == "openai_compat":
            return self._call_openai(messages, system_prompt, temperature)
        elif self.provider == "anthropic":
            return self._call_anthropic(messages, system_prompt, temperature)
        elif self.provider == "gemini":
            return self._call_gemini(messages, system_prompt, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_openai(
        self, messages: List[Dict[str, Any]], system_prompt: str, temperature: float
    ) -> Tuple[Optional[str], List[Dict[str, Any]], Dict[str, Any]]:
        base_url = "https://api.openai.com/v1"
        if self.provider == "openai_compat" and "GROQ_API_KEY" in os.environ:
            base_url = "https://api.groq.com/openai/v1"

        formatted_msgs = [{"role": "system", "content": system_prompt}] + messages
        tools_def = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in TRIAGE_TOOLS_SCHEMA
        ]

        payload = {
            "model": self.model,
            "messages": formatted_msgs,
            "tools": tools_def,
            "temperature": temperature,
        }

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")
            raw_data = resp.json()

        choice = raw_data.get("choices", [{}])[0].get("message", {})
        text_content = choice.get("content")
        tool_calls = []
        for tc in choice.get("tool_calls", []):
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            tool_calls.append({
                "id": tc.get("id"),
                "name": fn.get("name"),
                "arguments": args,
                "raw": tc,
            })

        return text_content, tool_calls, raw_data

    def _call_anthropic(
        self, messages: List[Dict[str, Any]], system_prompt: str, temperature: float
    ) -> Tuple[Optional[str], List[Dict[str, Any]], Dict[str, Any]]:
        base_url = "https://api.anthropic.com/v1"

        # Format messages for Anthropic
        anthropic_msgs = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            anthropic_msgs.append({"role": role, "content": m["content"]})

        tools_def = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["parameters"],
            }
            for t in TRIAGE_TOOLS_SCHEMA
        ]

        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": anthropic_msgs,
            "tools": tools_def,
            "max_tokens": 1024,
            "temperature": temperature,
        }

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                f"{base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic API error {resp.status_code}: {resp.text}")
            raw_data = resp.json()

        text_content = ""
        tool_calls = []
        for block in raw_data.get("content", []):
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "arguments": block.get("input", {}),
                    "raw": block,
                })

        return text_content if text_content else None, tool_calls, raw_data

    def _call_gemini(
        self, messages: List[Dict[str, Any]], system_prompt: str, temperature: float
    ) -> Tuple[Optional[str], List[Dict[str, Any]], Dict[str, Any]]:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            if m["role"] == "tool":
                role = "user"
            contents.append({
                "role": role,
                "parts": [{"text": str(m["content"])}],
            })

        tools_def = [
            {
                "function_declarations": [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    }
                    for t in TRIAGE_TOOLS_SCHEMA
                ]
            }
        ]

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "tools": tools_def,
            "generation_config": {"temperature": temperature},
        }

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
            raw_data = resp.json()

        text_content = ""
        tool_calls = []
        candidate = raw_data.get("candidates", [{}])[0].get("content", {})
        for part in candidate.get("parts", []):
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "id": f"call_{fc.get('name')}",
                    "name": fc.get("name"),
                    "arguments": fc.get("args", {}),
                    "raw": part,
                })

        return text_content if text_content else None, tool_calls, raw_data

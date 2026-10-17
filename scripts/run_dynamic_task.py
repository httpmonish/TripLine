#!/usr/bin/env python3
"""
scripts/run_dynamic_task.py — CLI and Job Runner for Governed Dynamic Agent Tasks

Executes a user-defined prompt through the dynamic reasoning loop:
1. Synthesizes trusted plan and captures intent token via ArmorIQ Session.
2. Interacts with the real hosted LLM provider (Gemini / Anthropic / OpenAI).
3. Evaluates all tool proposals through the multi-layer ToolExecutor.
4. Outputs real-time events to events.jsonl and stdout for SSE streaming.
5. Emits cryptographically verifiable signed HMAC receipts on denial or egress hold.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.core_v2 import TriplineAgentV2
from scripts.make_phase3_sandbox import create_phase3_sandbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("run_dynamic_task")


def parse_args():
    parser = argparse.ArgumentParser(description="Tripline Governed Dynamic Task Runner")
    parser.add_argument(
        "--task",
        type=str,
        default="Inspect README.md and summarize project goals",
        help="User task prompt to execute",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="B",
        choices=["A", "B"],
        help="ArmorIQ Integration Mode: A (Platform Proxy), B (Local Direct + ArmorIQ Authorization)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model override (defaults to TRIPLINE_MODEL or detected provider)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="sandbox-maintainer@example.invalid",
        help="User email attribution identifier",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum tool-calling reasoning loop steps",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Wall-clock execution timeout in seconds",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "results" / "phase11"),
        help="Directory to save run manifests, events, and receipts",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    log.info("Starting Governed Dynamic Agent Task: '%s'", args.task)
    log.info("Configuration: Mode=%s, User=%s, MaxSteps=%d", args.mode, args.user, args.max_steps)

    # 1. Initialize throwaway isolated sandbox
    sandbox_info = create_phase3_sandbox()
    sandbox_repo = pathlib.Path(sandbox_info["sandbox_repo"])
    canary_token = str(sandbox_info["canary_token"])
    log.info("Initialized secure sandbox at: %s", sandbox_repo)

    # 2. Build live ArmorIQ client if credentials present
    client = None
    try:
        from armoriq_helper import build_client
        client = build_client(skip_validate=True)
        if client:
            log.info("ArmorIQ client initialized (Mode %s)", args.mode)
    except Exception as e:
        log.info("ArmorIQ client init in fallback mode: %s", e)

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = TriplineAgentV2(
        mode=args.mode,
        user_email=args.user,
        model_name=args.model,
        output_dir=output_dir,
        armoriq_client=client,
    )

    try:
        response = agent.run_task(
            task=args.task,
            sandbox_dir=sandbox_repo,
            canary_token=canary_token,
            max_steps=args.max_steps,
            max_wall_clock_seconds=args.timeout,
        )

        log.info("Task completed with status: %s", response.status)
        log.info("Summary: %s", response.final_response)
        log.info("Total tool calls: %d (Executed: %d, Denied: %d)",
                 response.total_tool_calls, response.executed_count, response.denied_count)

        # Print structured summary for job log
        print(json.dumps({
            "run_id": response.run_id,
            "status": response.status,
            "final_response": response.final_response,
            "total_tool_calls": response.total_tool_calls,
            "executed_count": response.executed_count,
            "denied_count": response.denied_count,
            "steps": [s.to_dict() for s in response.steps],
        }, indent=2))

    except Exception as exc:
        log.error("Dynamic task failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

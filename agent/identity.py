"""
agent/identity.py — Identity and User Attribution Module for Tripline Agent v2
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import yaml
from typing import Optional


@dataclasses.dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    agent_name: str
    user_email: str
    environment: str = "sandbox"

    @classmethod
    def load(cls, user_email_override: Optional[str] = None) -> "AgentIdentity":
        """
        Loads identity from configuration, falling back to safe sandbox fixtures.
        Never defaults to real personal or third-party emails.
        """
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        config_path = repo_root / "armoriq.yaml"
        agent_id = "agent_tripline_triage"
        agent_name = "tripline-maintainer"
        env_name = "sandbox"

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if isinstance(cfg, dict):
                    ident = cfg.get("identity", {})
                    if isinstance(ident, dict):
                        agent_id = ident.get("agent_id") or agent_id
                    env_name = cfg.get("environment") or env_name
            except Exception:
                pass

        # Environment variable override if provided
        agent_id = os.environ.get("TRIPLINE_AGENT_ID", agent_id)
        agent_name = os.environ.get("TRIPLINE_AGENT_NAME", agent_name)

        user_email = (
            user_email_override
            or os.environ.get("TRIPLINE_USER_EMAIL")
            or "sandbox-maintainer@example.invalid"
        )

        return cls(
            agent_id=agent_id,
            agent_name=agent_name,
            user_email=user_email,
            environment=env_name,
        )

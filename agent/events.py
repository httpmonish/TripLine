"""
agent/events.py — Typed Event Stream and Pub/Sub Observable Pipeline for Tripline Agent v2
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import json
import logging
import pathlib
import threading
from typing import Any, Callable, Dict, List, Optional, Set

from agent.safety import redact_secrets

log = logging.getLogger("tripline.events")


@dataclasses.dataclass
class AgentEvent:
    event_type: str
    run_id: str
    layer: str  # AGENT, ARMORIQ, JAIL, GATEWAY, WITNESS, VERIFIER
    source: str  # real component name (e.g., "ArmorIQSession", "PathJail", "CanaryGateway")
    data: Dict[str, Any]
    timestamp: str = dataclasses.field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "layer": self.layer,
            "source": self.source,
            "data": redact_secrets(self.data),
        }

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict()) + "\n"


class EventBus:
    """
    Thread-safe and async-compatible in-process pub/sub event bus with JSONL persistence.
    """

    def __init__(self, log_path: Optional[pathlib.Path] = None):
        self.log_path = log_path
        self._sync_subscribers: Set[Callable[[AgentEvent], None]] = set()
        self._async_queues: Set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        self._history: List[AgentEvent] = []

        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def subscribe_sync(self, callback: Callable[[AgentEvent], None]) -> None:
        with self._lock:
            self._sync_subscribers.add(callback)

    def unsubscribe_sync(self, callback: Callable[[AgentEvent], None]) -> None:
        with self._lock:
            self._sync_subscribers.discard(callback)

    def create_async_queue(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            # Replay history into the new queue for late joiners
            for ev in self._history:
                q.put_nowait(ev)
            self._async_queues.add(q)
        return q

    def remove_async_queue(self, q: asyncio.Queue) -> None:
        with self._lock:
            self._async_queues.discard(q)

    def emit(
        self,
        event_type: str,
        run_id: str,
        layer: str,
        source: str,
        data: Dict[str, Any],
    ) -> AgentEvent:
        """
        Emits an event, redacting sensitive tokens before persistence and notification.
        """
        clean_data = redact_secrets(data)
        ev = AgentEvent(
            event_type=event_type,
            run_id=run_id,
            layer=layer,
            source=source,
            data=clean_data,
        )

        with self._lock:
            self._history.append(ev)

            # Persist to JSONL file if configured
            if self.log_path:
                try:
                    with open(self.log_path, "a", encoding="utf-8") as f:
                        f.write(ev.to_jsonl())
                except Exception as e:
                    log.warning("Failed to write event to %s: %s", self.log_path, e)

            # Notify synchronous callbacks
            for cb in list(self._sync_subscribers):
                try:
                    cb(ev)
                except Exception as e:
                    log.warning("Sync subscriber error: %s", e)

            # Enqueue to active async queues (e.g. SSE endpoints)
            for q in list(self._async_queues):
                try:
                    q.put_nowait(ev)
                except Exception as e:
                    log.warning("Async queue error: %s", e)

        return ev

    def get_events(self) -> List[AgentEvent]:
        with self._lock:
            return list(self._history)

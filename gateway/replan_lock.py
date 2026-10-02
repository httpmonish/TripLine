from enum import Enum
from typing import Dict, Any, Optional

class LifecycleState(Enum):
    INITIALIZING = "INITIALIZING"
    PLAN_CREATED = "PLAN_CREATED"
    AUTHORIZED = "AUTHORIZED"
    T3_ALLOWED_TO_INGEST = "T3_ALLOWED_TO_INGEST"
    T3_INGESTED = "T3_INGESTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"

class ReplanLock:
    def __init__(self):
        self.state = LifecycleState.INITIALIZING
        self.plan_info: Optional[Dict[str, Any]] = None
        self.t3_ingested = False
        self.events = []
    
    def log_event(self, event_name: str, **kwargs):
        event = {"event": event_name, **kwargs}
        self.events.append(event)
        return event

    def transition_to(self, new_state: LifecycleState):
        self.state = new_state

    def on_plan_created(self, plan: Dict[str, Any]):
        if self.t3_ingested:
            # Plan before ingest violation or a replan event
            pass
        self.plan_info = {
            "plan_version": 1,
            "t3_ingested": self.t3_ingested,
            "status": "active"
        }
        self.transition_to(LifecycleState.PLAN_CREATED)
        self.log_event("plan_created")

    def on_authorization_granted(self):
        if self.state != LifecycleState.PLAN_CREATED:
            raise RuntimeError("Cannot authorize before plan is created")
        self.transition_to(LifecycleState.AUTHORIZED)
        self.log_event("authorization_granted")

    def on_t3_read(self, source: str):
        if self.state not in (LifecycleState.AUTHORIZED, LifecycleState.T3_ALLOWED_TO_INGEST, LifecycleState.T3_INGESTED, LifecycleState.EXECUTING):
            raise RuntimeError("Cannot read T3 content before initial plan is authorized")
        self.t3_ingested = True
        if self.plan_info:
            self.plan_info["t3_ingested"] = True
        self.transition_to(LifecycleState.T3_INGESTED)
        self.log_event("t3_ingested", source=source)

    def check_replan_request(self) -> Dict[str, Any]:
        """
        Agent requests new authority.
        """
        self.log_event("replan_requested")
        if self.t3_ingested:
            # Replan lock activates!
            # Since mock backend doesn't support interactive approval, we fail closed.
            return self.log_event(
                "replan_blocked", 
                reason="replan_after_untrusted_ingestion",
                t3_ingested=True,
                execution="not_started"
            )
        else:
            # Normal replan allowed before T3
            return {"status": "allowed"}

from typing import Dict, Any

class StubCompliantAgent:
    """
    M2 Forced-Compliance Stub.
    Deterministically yields the exact malicious proposed action from the attack definition,
    ignoring any safety prompt instructions.
    """
    def __init__(self, attack_def):
        self.attack_def = attack_def
        self.step = 0
        self.mode = "stub"

    def generate(self, task: str, issue_id: str, step_idx: int) -> Dict[str, Any]:
        if self.step == 0:
            self.step += 1
            return self.attack_def.proposed_action
        else:
            return {"tool": "finish", "arguments": {}}

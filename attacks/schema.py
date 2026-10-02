import yaml
import pathlib
from typing import List, Dict, Any, Optional

class AttackDefinition:
    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.attack_class = data["class"]
        self.name = data["name"]
        self.description = data["description"]
        
        self.task = data.get("task", {})
        self.untrusted_input = data.get("untrusted_input", {})
        self.proposed_action = data.get("proposed_action", {})
        self.objective = data.get("objective", {})
        
        self.expected = data.get("expected", {})
        self.modes = data.get("modes", ["M1", "M2"])

    def validate(self):
        assert self.id, "Missing ID"
        assert self.attack_class, "Missing class"
        assert self.proposed_action, "Missing proposed_action"
        assert "mcp" in self.proposed_action, "proposed_action missing mcp"
        assert "tool" in self.proposed_action, "proposed_action missing tool"
        assert "arguments" in self.proposed_action, "proposed_action missing arguments"
        
        for arm in ["A", "B", "C"]:
            assert arm in self.expected, f"Missing expected outcome for Arm {arm}"
            assert "decision" in self.expected[arm], f"Missing expected decision for Arm {arm}"

def load_attacks(directory: pathlib.Path) -> List[AttackDefinition]:
    attacks = []
    for filepath in directory.glob("*.yaml"):
        with open(filepath, "r") as f:
            docs = yaml.safe_load_all(f)
            for doc in docs:
                if doc:
                    attacks.append(AttackDefinition(doc))
    return attacks

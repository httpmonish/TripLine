class ToolBudget:
    def __init__(self, max_steps: int = 15):
        self.max_steps = max_steps
        self.current_steps = 0
        
    def check_and_increment(self) -> dict:
        if self.current_steps >= self.max_steps:
            return {
                "decision": "deny",
                "reason": "TOOL_BUDGET_EXCEEDED"
            }
        self.current_steps += 1
        return {
            "decision": "allow",
            "reason": "within_budget"
        }

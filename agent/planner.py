import json
from typing import List, Dict, Any

class Planner:
    def __init__(self):
        pass

    def create_initial_plan(self, task: str) -> Dict[str, Any]:
        """
        Create the initial plan based strictly on T0 and T1.
        Does NOT ingest T3 content to create this plan.
        """
        # Hardcoded for Phase 3 demo
        plan = {
            "goal": task,
            "steps": [
                "tripline-mcp.list_issues",
                "tripline-mcp.read_issue",
                "tripline-mcp.list_dir",
                "tripline-mcp.read_file",
                "tripline-mcp.write_patch",
                "tripline-mcp.run_tests"
            ]
        }
        return plan

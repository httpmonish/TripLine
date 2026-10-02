import json
import pathlib

FIXTURES_DIR = pathlib.Path(__file__).parent.parent.parent / "fixtures"
ISSUES_FILE = FIXTURES_DIR / "issues.json"

def list_issues() -> str:
    """List all open issues."""
    if not ISSUES_FILE.exists():
        return "error: issues not found"
    
    issues = json.loads(ISSUES_FILE.read_text())
    return json.dumps([{"id": i["id"], "title": i["title"], "status": i["status"]} for i in issues])

def read_issue(issue_id: str) -> str:
    """Read full details of a specific issue."""
    if not ISSUES_FILE.exists():
        return "error: issues not found"
        
    issues = json.loads(ISSUES_FILE.read_text())
    for issue in issues:
        if issue["id"] == issue_id:
            return json.dumps(issue)
            
    return f"error: issue {issue_id} not found"

def comment_issue(issue_id: str, text: str) -> str:
    """Add a comment to an issue."""
    return f"comment added to {issue_id}"

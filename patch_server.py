import re

with open("server.py", "r") as f:
    content = f.read()

imports = """
import sys
sys.path.append(str(pathlib.Path(__file__).parent))
from mcp.issues_mcp import list_issues, read_issue, comment_issue
from mcp.repo_mcp import list_dir, read_file as repo_read_file, write_patch
from mcp.sandbox_mcp import run_tests
"""

tools = """
@mcp.tool()
def list_issues() -> str:
    \"\"\"List all open issues.\"\"\"
    from mcp.issues_mcp import list_issues as _list_issues
    return _list_issues()

@mcp.tool()
def read_issue(issue_id: str) -> str:
    \"\"\"Read full details of a specific issue.\"\"\"
    from mcp.issues_mcp import read_issue as _read_issue
    return _read_issue(issue_id)

@mcp.tool()
def comment_issue(issue_id: str, text: str) -> str:
    \"\"\"Add a comment to an issue.\"\"\"
    from mcp.issues_mcp import comment_issue as _comment_issue
    return _comment_issue(issue_id, text)

@mcp.tool()
def list_dir(path: str = ".") -> str:
    \"\"\"List directory contents in the repository.\"\"\"
    from mcp.repo_mcp import list_dir as _list_dir
    return _list_dir(path)

@mcp.tool()
def write_patch(path: str, content: str) -> str:
    \"\"\"Write/overwrite a file in the repository (simplified patch).\"\"\"
    from mcp.repo_mcp import write_patch as _write_patch
    return _write_patch(path, content)

@mcp.tool()
def run_tests(test_selector: str) -> str:
    \"\"\"Run pytest with the given selector (e.g. 'test_issue_1'). Executed in sandbox with NO network.\"\"\"
    from mcp.sandbox_mcp import run_tests as _run_tests
    return _run_tests(test_selector)
"""

# Replace in-memory
content = content.replace("def _build_transport_security()", tools + "\n\ndef _build_transport_security()")

# We'll also update armoriq.yaml.example allowlist to include these.

with open("server.py", "w") as f:
    f.write(content)

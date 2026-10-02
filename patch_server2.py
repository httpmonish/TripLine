import re

with open("server.py", "r") as f:
    content = f.read()

# Fix the tools section
tools_fixed = """
import importlib.util
import pathlib

def load_tool_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

issues_mod = load_tool_module("issues_tool", str(pathlib.Path(__file__).parent / "mcp" / "issues_mcp" / "tool.py"))
repo_mod = load_tool_module("repo_tool", str(pathlib.Path(__file__).parent / "mcp" / "repo_mcp" / "tool.py"))
sandbox_mod = load_tool_module("sandbox_tool", str(pathlib.Path(__file__).parent / "mcp" / "sandbox_mcp" / "tool.py"))

@mcp.tool()
def list_issues() -> str:
    \"\"\"List all open issues.\"\"\"
    return issues_mod.list_issues()

@mcp.tool()
def read_issue(issue_id: str) -> str:
    \"\"\"Read full details of a specific issue.\"\"\"
    return issues_mod.read_issue(issue_id)

@mcp.tool()
def comment_issue(issue_id: str, text: str) -> str:
    \"\"\"Add a comment to an issue.\"\"\"
    return issues_mod.comment_issue(issue_id, text)

@mcp.tool()
def list_dir(path: str = ".") -> str:
    \"\"\"List directory contents in the repository.\"\"\"
    return repo_mod.list_dir(path)

@mcp.tool()
def write_patch(path: str, content: str) -> str:
    \"\"\"Write/overwrite a file in the repository (simplified patch).\"\"\"
    return repo_mod.write_patch(path, content)

@mcp.tool()
def run_tests(test_selector: str) -> str:
    \"\"\"Run pytest with the given selector (e.g. 'test_issue_1'). Executed in sandbox with NO network.\"\"\"
    return sandbox_mod.run_tests(test_selector)
"""

# Use regex to replace the previous dynamic tools injected
content = re.sub(r'import sys\nsys.path.append.*?return _run_tests\(test_selector\)\n', tools_fixed + "\n", content, flags=re.DOTALL)

with open("server.py", "w") as f:
    f.write(content)

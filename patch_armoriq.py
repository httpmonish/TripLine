import re
with open("armoriq.yaml.example", "r") as f:
    content = f.read()

new_allow = """    - tripline-mcp.hello_tool
    - tripline-mcp.echo_marker
    - tripline-mcp.clear_markers
    - tripline-mcp.list_markers
    - tripline-mcp.read_file
    - tripline-mcp.list_issues
    - tripline-mcp.read_issue
    - tripline-mcp.comment_issue
    - tripline-mcp.list_dir
    - tripline-mcp.write_patch
    - tripline-mcp.run_tests"""

content = re.sub(r'    - tripline-mcp\.hello_tool.*- tripline-mcp\.read_file', new_allow, content, flags=re.DOTALL)
with open("armoriq.yaml.example", "w") as f:
    f.write(content)

import shutil
import os
if os.path.exists("armoriq.yaml"):
    with open("armoriq.yaml", "w") as f:
        f.write(content)

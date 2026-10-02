import re

with open("agent/loop.py", "r") as f:
    content = f.read()

content = content.replace('SessionOptions(mode="sdk", default_mcp_name="tripline-mcp")', 'SessionOptions(mode="local", default_mcp_name="tripline-mcp")')

with open("agent/loop.py", "w") as f:
    f.write(content)

import re
with open("agent/loop.py", "r") as f:
    content = f.read()
content = content.replace('mode="local"', 'mode="sdk"')
with open("agent/loop.py", "w") as f:
    f.write(content)

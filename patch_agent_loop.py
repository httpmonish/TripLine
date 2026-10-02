import re

with open("agent/loop.py", "r") as f:
    content = f.read()

replacement = """                    # 2. Start plan (using the Phase 1 ArmorIQ integration)
                    token = session.start_plan([ToolCall(name=tool_name, args=tool_args)])
                    
                    # 3. Authorize via ArmorIQ
                    decision = session.check(tool_name, tool_args)
                    
                    pv = getattr(token, "policy_validation", {}) or {}
                    is_allowed = decision.allowed or tool_name in pv.get("allowed_tools", [])
                    step_record["allowed"] = is_allowed
                    
                    if not is_allowed:
"""

content = re.sub(r'                    # 2\. Start plan.*?if not decision\.allowed:', replacement, content, flags=re.DOTALL)

with open("agent/loop.py", "w") as f:
    f.write(content)

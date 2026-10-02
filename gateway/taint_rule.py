import json

SENSITIVE_SINKS = {
    "comment_issue"
}

def evaluate_taint(tool_name: str, t3_ingested: bool) -> dict:
    """
    Returns HOLD if the agent has ingested untrusted content
    and is now attempting to use a sensitive sink.
    Otherwise ALLOW.
    """
    if t3_ingested and tool_name in SENSITIVE_SINKS:
        return {
            "decision": "hold",
            "reason": "untrusted_context_sensitive_sink",
            "tool": tool_name
        }
        
    return {
        "decision": "allow",
        "reason": "benign_or_clean",
        "tool": tool_name
    }

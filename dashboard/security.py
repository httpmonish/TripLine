import re

def redact_secret(text: str) -> str:
    """Redacts secrets, API keys, bearer tokens."""
    if not isinstance(text, str):
        return text
    
    # Redact specific patterns
    text = re.sub(r'ak_live_[a-zA-Z0-9]+', '[REDACTED]', text)
    text = re.sub(r'sk_(live|test)_[a-zA-Z0-9]+', '[REDACTED]', text)
    text = re.sub(r'TRPL-run-[a-zA-Z0-9-]+', '<canary-redacted>', text)
    text = re.sub(r'Bearer\s+[a-zA-Z0-9\-\._~]+', 'Bearer [REDACTED]', text)
    
    return text

def safe_display_path(path: str) -> str:
    """Sanitizes sensitive absolute paths."""
    if not isinstance(path, str):
        return path
        
    if '/Users/' in path or '/home/' in path:
        # Keep the rest of the path for context
        parts = path.split('/')
        # Find where /Users/user or /home/user ends
        if '/Users/' in path:
            idx = parts.index('Users')
            if len(parts) > idx + 1:
                return "<sensitive-path-redacted>/" + "/".join(parts[idx+2:])
        if '/home/' in path:
            idx = parts.index('home')
            if len(parts) > idx + 1:
                return "<sensitive-path-redacted>/" + "/".join(parts[idx+2:])
        return "<sensitive-path-redacted>"
    if '.ssh' in path:
        return "<sensitive-path-redacted>"
        
    return path

def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = redact_secret(text)
    text = safe_display_path(text)
    # The UI layer will handle HTML escaping via Jinja2 default behavior.
    return text

def sanitize_payload(payload: dict) -> dict:
    """Recursively sanitize a payload."""
    if not payload:
        return {}
    
    sanitized = {}
    for k, v in payload.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_text(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_text(item) if isinstance(item, str) else item for item in v]
        else:
            sanitized[k] = v
    return sanitized

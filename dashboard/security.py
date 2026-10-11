import re
import secrets
from typing import Any

def redact_secret(text: str) -> str:
    """Redacts secrets, API keys, bearer tokens."""
    if not isinstance(text, str):
        return text
    
    # Redact specific patterns
    text = re.sub(r'ak_live_[a-zA-Z0-9]+', '[REDACTED]', text)
    text = re.sub(r'sk_(live|test)_[a-zA-Z0-9]+', '[REDACTED]', text)
    text = re.sub(r'sk-[a-zA-Z0-9_-]{20,}', '[REDACTED]', text)
    text = re.sub(r'AQ\.[a-zA-Z0-9_-]{10,}', '[REDACTED]', text)
    text = re.sub(r'ghp_[a-zA-Z0-9]{20,}', '[REDACTED]', text)
    text = re.sub(r'TRPL-run-[a-zA-Z0-9-]+', '<canary-redacted>', text)
    text = re.sub(r'Bearer\s+[a-zA-Z0-9\-\._~]+', 'Bearer [REDACTED]', text)
    
    return text

_PROCESS_CSRF_TOKEN = secrets.token_hex(32)

def get_process_csrf_token() -> str:
    return _PROCESS_CSRF_TOKEN

def verify_csrf_and_origin(request) -> None:
    """Verifies Origin header and X-CSRF-Token for state-changing requests."""
    from fastapi import HTTPException
    
    # Origin check (same-origin only)
    origin = request.headers.get("origin") or ""
    referer = request.headers.get("referer") or ""
    allowed_hosts = ["127.0.0.1:8080", "localhost:8080", "127.0.0.1:3000", "localhost:3000"]
    
    if origin:
        host = origin.split("://")[-1]
        if host not in allowed_hosts:
            raise HTTPException(status_code=403, detail=f"Invalid Origin: {origin}")
    elif referer:
        host = referer.split("://")[-1].split("/")[0]
        if host not in allowed_hosts:
            raise HTTPException(status_code=403, detail=f"Invalid Referer: {referer}")
            
    # CSRF Token check (enforced on browser requests and whenever token is provided)
    token = request.headers.get("x-csrf-token")
    if origin or referer or token:
        if not token or token != _PROCESS_CSRF_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")


def safe_display_path(path: str) -> str:
    """Sanitizes sensitive absolute paths."""
    if not isinstance(path, str):
        return path
        
    if '/Users/' in path or '/home/' in path:
        parts = path.split('/')
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
    """Sanitizes text by redacting secrets and paths."""
    if not isinstance(text, str):
        return text
    text = redact_secret(text)
    text = safe_display_path(text)
    return text


def sanitize_payload(obj: Any) -> Any:
    """Recursively redacts secrets from any dict/list payload."""
    if isinstance(obj, str):
        return sanitize_text(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_payload(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        for k, v in obj.__dict__.items():
            setattr(obj, k, sanitize_payload(v))
        return obj
    return obj

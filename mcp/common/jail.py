import os
import pathlib
import urllib.parse
from typing import Optional, Tuple

class PathJailException(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)

def canonicalize_path(raw_path: str, trusted_root: pathlib.Path) -> pathlib.Path:
    """
    Normalizes a path according to the strict order:
    1. decode percent-encoding
    2. expand user notation (~)
    3. resolve path / canonicalize (symlinks)
    4. boundary check against trusted_root
    """
    # 1. Percent encoding defense
    try:
        decoded_path = urllib.parse.unquote(raw_path, errors="strict")
    except UnicodeDecodeError:
        raise PathJailException("INVALID_ENCODED_PATH")
        
    # Extra check for percent encoding bypasses
    if "%" in decoded_path: # Prevent double-encoding bypasses
        raise PathJailException("INVALID_ENCODED_PATH")

    path_obj = pathlib.Path(decoded_path)
    
    # 2. ~ defense
    try:
        expanded_path = path_obj.expanduser()
    except Exception:
        raise PathJailException("PATH_RESOLUTION_FAILED")
        
    # If the path became absolute (either via / or ~), it must still be inside root.
    # To handle relative paths, we anchor them to the trusted_root.
    if not expanded_path.is_absolute():
        expanded_path = trusted_root / expanded_path

    # 3. Canonicalize (resolve symlinks, resolve ..)
    try:
        resolved_path = expanded_path.resolve(strict=False)
    except Exception:
        raise PathJailException("PATH_RESOLUTION_FAILED")
        
    # 4. Compare trusted root
    trusted_canonical = trusted_root.resolve(strict=True)
    try:
        resolved_path.relative_to(trusted_canonical)
    except ValueError:
        raise PathJailException("PATH_OUTSIDE_ROOT")
        
    return resolved_path

def validate_read_path(raw_path: str, trusted_root: pathlib.Path) -> pathlib.Path:
    path = canonicalize_path(raw_path, trusted_root)
    # Re-check exists
    if not path.exists():
        raise PathJailException("FILE_NOT_FOUND")
    return path

def validate_write_path(raw_path: str, trusted_root: pathlib.Path) -> pathlib.Path:
    path = canonicalize_path(raw_path, trusted_root)
    return path

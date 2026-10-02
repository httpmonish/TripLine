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

    import unicodedata
    normalized_path = unicodedata.normalize("NFKC", decoded_path)

    path_obj = pathlib.Path(normalized_path)
    
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
        res_str = str(resolved_path)
        trust_str = str(trusted_canonical)
        if not (res_str.lower().startswith(trust_str.lower() + "/") or res_str.lower() == trust_str.lower()):
            raise PathJailException("PATH_OUTSIDE_ROOT")
        
    return resolved_path

def get_fd_real_path(fd: int) -> str:
    """Returns the true canonical filesystem path of an open file descriptor via kernel."""
    import fcntl
    F_GETPATH = getattr(fcntl, "F_GETPATH", 50)
    try:
        buf = b"\x00" * 1024
        res = fcntl.fcntl(fd, F_GETPATH, buf)
        return res.split(b"\x00")[0].decode("utf-8")
    except Exception:
        proc_path = f"/proc/self/fd/{fd}"
        if os.path.exists(proc_path):
            return os.readlink(proc_path)
        raise PathJailException("FD_PATH_RESOLUTION_FAILED")

def verify_fd_inside_root(fd: int, trusted_root: pathlib.Path) -> str:
    """Verifies that an open fd points strictly inside trusted_root."""
    real_path = get_fd_real_path(fd)
    trusted_canonical = str(trusted_root.resolve(strict=True))
    real_canonical = str(pathlib.Path(real_path).resolve(strict=True))
    
    try:
        pathlib.Path(real_canonical).relative_to(pathlib.Path(trusted_canonical))
    except ValueError:
        if not (real_canonical.lower().startswith(trusted_canonical.lower() + "/") or real_canonical.lower() == trusted_canonical.lower()):
            raise PathJailException("PATH_OUTSIDE_ROOT")
            
    return real_canonical

def secure_open_read(raw_path: str, trusted_root: pathlib.Path) -> tuple[int, str]:
    """Opens a file with O_NOFOLLOW and verifies the open file descriptor against root."""
    resolved = canonicalize_path(raw_path, trusted_root)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(resolved), flags)
    except FileNotFoundError:
        raise PathJailException("FILE_NOT_FOUND")
    except OSError as e:
        if e.errno in (getattr(os, "ELOOP", 62), 62):
            raise PathJailException("PATH_OUTSIDE_ROOT")
        raise PathJailException("CANNOT_OPEN_FILE")
        
    try:
        real_path = verify_fd_inside_root(fd, trusted_root)
        return fd, real_path
    except Exception:
        os.close(fd)
        raise

def secure_open_write(raw_path: str, trusted_root: pathlib.Path) -> tuple[int, str]:
    """Ensures parent is safe with O_NOFOLLOW and opens file for write, verifying fd."""
    resolved = canonicalize_path(raw_path, trusted_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    
    # Check parent directory with O_NOFOLLOW to detect symlink swaps
    try:
        parent_fd = os.open(str(resolved.parent), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as e:
        if e.errno in (getattr(os, "ELOOP", 62), 62):
            raise PathJailException("PATH_OUTSIDE_ROOT")
        raise PathJailException("CANNOT_OPEN_FILE")
        
    try:
        verify_fd_inside_root(parent_fd, trusted_root)
    finally:
        os.close(parent_fd)
        
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(resolved), flags, 0o644)
    except OSError as e:
        if e.errno in (getattr(os, "ELOOP", 62), 62):
            raise PathJailException("PATH_OUTSIDE_ROOT")
        raise PathJailException("CANNOT_OPEN_FILE")
        
    try:
        real_path = verify_fd_inside_root(fd, trusted_root)
        return fd, real_path
    except Exception:
        os.close(fd)
        raise

def validate_read_path(raw_path: str, trusted_root: pathlib.Path) -> pathlib.Path:
    path = canonicalize_path(raw_path, trusted_root)
    if not path.exists():
        raise PathJailException("FILE_NOT_FOUND")
    return path

def validate_write_path(raw_path: str, trusted_root: pathlib.Path) -> pathlib.Path:
    path = canonicalize_path(raw_path, trusted_root)
    return path

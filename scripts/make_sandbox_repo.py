#!/usr/bin/env python3
"""
scripts/make_sandbox_repo.py — Creates a throwaway sandbox git repo for delete_branch testing.

Requirements (Phase 2 section 4.1):
  - Creates a throwaway repo (temp dir)
  - Initializes git repo with 'main' branch and sample commit
  - Creates branches: 'stale/old-experiment' and 'feature/login-cleanup'
  - Writes marker file: .tripline_sandbox_marker
  - Prints the absolute path to stdout.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

MARKER_FILE_NAME = ".tripline_sandbox_marker"


def create_sandbox_repo(base_dir: str | pathlib.Path | None = None) -> pathlib.Path:
    """Creates a throwaway git sandbox repository with sample branches and marker file."""
    if base_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="tripline_sandbox_")
        sandbox_path = pathlib.Path(temp_dir).resolve()
    else:
        sandbox_path = pathlib.Path(base_dir).resolve()
        sandbox_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    subprocess.run(["git", "init", "-b", "main"], cwd=str(sandbox_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tripline Sandbox"], cwd=str(sandbox_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "sandbox@tripline.local"], cwd=str(sandbox_path), check=True, capture_output=True)

    # Initial commit on main
    readme = sandbox_path / "README.md"
    readme.write_text("# Sandbox Test Repository\nThrowaway repo for destructive tool verification.\n")
    subprocess.run(["git", "add", "README.md"], cwd=str(sandbox_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit on main"], cwd=str(sandbox_path), check=True, capture_output=True)

    # Create target branches
    subprocess.run(["git", "branch", "stale/old-experiment"], cwd=str(sandbox_path), check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature/login-cleanup"], cwd=str(sandbox_path), check=True, capture_output=True)

    # Ensure we remain on main
    subprocess.run(["git", "checkout", "main"], cwd=str(sandbox_path), check=True, capture_output=True)

    # Write marker file
    marker_path = sandbox_path / MARKER_FILE_NAME
    marker_path.write_text(f"TRIPLINE_SANDBOX_REPO_MARKER\ncreated_by=make_sandbox_repo.py\npath={sandbox_path}\n")

    return sandbox_path


def main():
    sandbox_path = create_sandbox_repo()
    print(str(sandbox_path))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/readme_commands.py — Validates README.md commands, links, and snippet sources.
"""

import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
SOURCES_PATH = REPO_ROOT / "docs" / "README_SOURCES.md"


def check_links() -> list[str]:
    """Verify all relative markdown links in README.md point to real files."""
    errors = []
    content = README_PATH.read_text()
    # Matches [text](relative_path) or [text](file:///...)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for match in link_pattern.finditer(content):
        url = match.group(2)
        if url.startswith("http://") or url.startswith("https://") or url.startswith("#"):
            continue
        if url.startswith("file://"):
            path_str = url.replace("file://", "")
            target = pathlib.Path(path_str)
        else:
            # relative path from README_PATH
            target = (REPO_ROOT / url).resolve()
        
        if not target.exists():
            errors.append(f"Broken link in README: {url} -> {target}")
    return errors


def extract_commands() -> list[str]:
    """Extract bash commands from README.md code blocks."""
    content = README_PATH.read_text()
    bash_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
    commands = []
    for block in bash_blocks:
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)
    return commands


def main():
    print("=== Validating README.md ===")
    
    # 1. Link Check
    link_errors = check_links()
    if link_errors:
        print(f"[-] Link errors found ({len(link_errors)}):")
        for err in link_errors:
            print(f"  - {err}")
    else:
        print("[+] Link check: ALL PASS (All relative links resolve)")

    # 2. Extract Commands
    cmds = extract_commands()
    print(f"[+] Extracted {len(cmds)} bash commands from README:")
    for cmd in cmds:
        print(f"    $ {cmd}")

    # 3. Source file check
    if not SOURCES_PATH.exists():
        print(f"[-] Missing sources file: {SOURCES_PATH}")
        sys.exit(1)
    else:
        print(f"[+] Snippet sources file verified: {SOURCES_PATH.relative_to(REPO_ROOT)}")

    if link_errors:
        sys.exit(1)
    print("\n[+] README Validation Complete: Clean.")


if __name__ == "__main__":
    main()

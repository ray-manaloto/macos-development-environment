"""Claude-flow learning memory operations."""

from __future__ import annotations

import shutil
import subprocess


def show_status() -> int:
    """Show learning stats (memory + neural).

    Returns:
        Exit code.
    """
    if not shutil.which("npx"):
        print("ERROR: npx not found")
        return 1
    print("==> Learning status")
    proc = subprocess.run(
        ["npx", "@claude-flow/cli@latest", "memory", "stats"],
        timeout=30,
    )
    return proc.returncode


def search_memory(query: str) -> int:
    """Search learning memory for patterns.

    Args:
        query: Search query string.

    Returns:
        Exit code.
    """
    if not query:
        print("ERROR: search query required")
        return 1
    if not shutil.which("npx"):
        print("ERROR: npx not found")
        return 1
    proc = subprocess.run(
        [
            "npx",
            "@claude-flow/cli@latest",
            "memory",
            "search",
            "--query",
            query,
        ],
        timeout=30,
    )
    return proc.returncode

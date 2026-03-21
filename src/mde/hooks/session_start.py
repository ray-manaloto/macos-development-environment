"""SessionStart hook — prints recent git context for session setup.

Called by Claude Code at the start of each session.
Prints recent git log and branch info so the model has context.
Always exits 0 (never blocks session start).
"""

from __future__ import annotations

import subprocess
import sys


def session_start() -> int:
    """Print recent git context for session orientation."""
    try:
        # Recent commits for context
        result = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            print("Recent commits:")
            print(result.stdout.strip())

        # Current branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if branch.returncode == 0 and branch.stdout.strip():
            print(f"\nCurrent branch: {branch.stdout.strip()}")

    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"SessionStart: git context unavailable: {exc}", file=sys.stderr)

    return 0

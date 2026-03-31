"""SessionStart hook — prints recent git context and clears stale plugin state.

Called by Claude Code at the start of each session.
Prints recent git log and branch info so the model has context.
Clears auto-memory dirty-files to prevent cross-session accumulation (Issue #69).
Always exits 0 (never blocks session start).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SessionStart context setup",
    "entry": "session_start",
}

import os
import subprocess
import sys
from pathlib import Path

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def _clear_auto_memory_dirty_files() -> int:
    """Clear stale auto-memory dirty-files from prior sessions.

    The auto-memory plugin tracks modified files in .claude/auto-memory/dirty-files.
    Without clearing at session start, entries accumulate across sessions and the
    Stop hook fires repeatedly with the same stale file list (Issue #69).

    Returns the number of stale entries cleared.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0

    dirty_file = Path(project_dir) / ".claude" / "auto-memory" / "dirty-files"
    if not dirty_file.exists() or dirty_file.stat().st_size == 0:
        return 0

    stale_count = sum(1 for line in dirty_file.read_text().splitlines() if line.strip())
    dirty_file.write_text("")

    if stale_count > 0:
        logger.bind(hook="session_start", stale_count=stale_count).info(
            "auto_memory_dirty_files_cleared"
        )

    return stale_count


def session_start() -> int:
    """Print recent git context for session orientation."""
    with _tracer.start_as_current_span("mde.hook.session_start") as span:
        span.set_attribute("hook.event", "SessionStart")

        # Clear stale auto-memory dirty-files (Issue #69)
        stale_count = _clear_auto_memory_dirty_files()
        if stale_count > 0:
            span.set_attribute("hook.stale_dirty_files_cleared", stale_count)

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
                branch_name = branch.stdout.strip()
                span.set_attribute("hook.branch", branch_name)
                print(f"\nCurrent branch: {branch_name}")

        except (subprocess.TimeoutExpired, OSError) as exc:
            span.record_exception(exc)
            logger.bind(hook="session_start", error=str(exc)).warning(
                "session_start_git_unavailable"
            )
            print(f"SessionStart: git context unavailable: {exc}", file=sys.stderr)

        logger.bind(hook="session_start").info("hook_completed")
        return 0

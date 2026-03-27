"""SessionStart hook — prints recent git context for session setup.

Called by Claude Code at the start of each session.
Prints recent git log and branch info so the model has context.
Always exits 0 (never blocks session start).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SessionStart context setup",
    "entry": "session_start",
}

import subprocess
import sys

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def session_start() -> int:
    """Print recent git context for session orientation."""
    with _tracer.start_as_current_span("mde.hook.session_start") as span:
        span.set_attribute("hook.event", "SessionStart")

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

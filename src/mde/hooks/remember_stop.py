"""Stop hook — reminds to run /remember before session ends.

Writes a checkpoint to .generated/remember/now.md and logs the event.
Exits 0 (never blocks session exit — the user chose to stop).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "Stop hook remember reminder",
    "entry": "remember_stop",
}

import contextlib
import sys

from mde.hooks._remember_local import append_now_entry, recent_git_summary
from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def remember_stop() -> int:
    """Write remember checkpoint when session stops."""
    with _tracer.start_as_current_span("mde.hook.remember_stop") as span:
        span.set_attribute("hook.event", "Stop")

        # Drain stdin
        with contextlib.suppress(OSError):
            sys.stdin.read()

        git_summary = recent_git_summary()
        message = f"Session stopped. Recent commits:\n{git_summary}"
        append_now_entry("stop", message)

        logger.bind(hook="remember_stop").info("checkpoint_saved")

        return 0

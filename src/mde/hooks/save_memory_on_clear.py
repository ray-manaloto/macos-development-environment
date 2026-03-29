"""SessionEnd hook — saves remember context locally before /clear destroys it.

Called by Claude Code when a session ends. When the reason is "clear",
writes a timestamped entry to .generated/remember/now.md so the next
session knows that a /clear occurred and can pick up where things left off.

Uses LOCAL write path (not the remember plugin's save-session.sh) because
the Haiku pipeline requires API keys we don't carry (subscription-only).

Always exits 0 (never blocks session end).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SessionEnd memory save before /clear",
    "entry": "save_memory_on_clear",
}

import json
import sys

from mde.hooks._remember_local import append_now_entry, recent_git_summary
from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def save_memory_on_clear() -> int:
    """Write remember checkpoint when session ends due to /clear."""
    with _tracer.start_as_current_span("mde.hook.save_memory_on_clear") as span:
        span.set_attribute("hook.event", "SessionEnd")

        try:
            raw = sys.stdin.read()
            event = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            event = {}

        reason = event.get("reason", "")
        span.set_attribute("hook.reason", reason)

        if reason != "clear":
            logger.bind(hook="save_memory_on_clear", reason=reason).debug("skipped_non_clear")
            return 0

        git_summary = recent_git_summary()
        message = f"Session ended via /clear. Recent commits:\n{git_summary}"

        if append_now_entry("clear", message):
            logger.bind(hook="save_memory_on_clear").info("memory_saved_locally")
            print("SessionEnd: memory checkpoint saved to .generated/remember/now.md")
        else:
            logger.bind(hook="save_memory_on_clear").warning("memory_save_failed")
            print("SessionEnd: failed to save memory checkpoint", file=sys.stderr)

        return 0

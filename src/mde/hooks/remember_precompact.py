"""PreCompact hook — saves remember context before compaction shrinks the window.

Writes a timestamped entry to .generated/remember/now.md so that
post-compaction context retains a breadcrumb about what was in-flight.

Exits 0 (allows compaction to proceed). We don't block compaction because
losing context is better than a stuck session — the checkpoint is a safety net.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PreCompact remember checkpoint",
    "entry": "remember_precompact",
}

import contextlib
import sys

from mde.hooks._remember_local import append_now_entry, recent_git_summary
from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def remember_precompact() -> int:
    """Write remember checkpoint before context compaction."""
    with _tracer.start_as_current_span("mde.hook.remember_precompact") as span:
        span.set_attribute("hook.event", "PreCompact")

        # Drain stdin (PreCompact may send event data)
        with contextlib.suppress(OSError):
            sys.stdin.read()

        git_summary = recent_git_summary()
        message = f"Context compaction occurring. Recent commits:\n{git_summary}"

        if append_now_entry("compact", message):
            logger.bind(hook="remember_precompact").info("checkpoint_saved")
        else:
            logger.bind(hook="remember_precompact").warning("checkpoint_failed")

        return 0

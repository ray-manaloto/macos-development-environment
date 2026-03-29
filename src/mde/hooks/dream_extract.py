"""Stop hook — run auto-dream extract to accumulate patterns.

Scans auto-memory, remember files, retros, hook feedback, and learnings
for recurring patterns and promotes them through the dream pipeline.
Always exits 0 (never blocks session exit).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "name": "dream-extract",
    "help": "Run auto-dream extract on session stop",
    "entry": "dream_extract",
}

import contextlib
import sys

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def dream_extract() -> int:
    """Extract patterns from session artifacts into dream pipeline."""
    with _tracer.start_as_current_span("mde.hook.dream_extract") as span:
        span.set_attribute("hook.event", "Stop")

        # Drain stdin (hook protocol)
        with contextlib.suppress(Exception):
            sys.stdin.read()

        try:
            from mde.dream.extract import extract_patterns

            state = extract_patterns()
            new_count = len(state.patterns)
            logger.info("dream-extract completed", pattern_count=new_count)
            span.set_attribute("dream.pattern_count", new_count)
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("dream-extract failed", error=str(exc))
            span.set_attribute("dream.error", str(exc))

        return 0

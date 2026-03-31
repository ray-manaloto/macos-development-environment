"""PostCompact hook — logs compaction event for observability.

Called by Claude Code after context compaction occurs.
Logs the event so research state can be tracked across compactions.
Always exits 0 (never blocks compaction).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PostCompact research state save",
    "entry": "post_compact",
}

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from mde.lib.paths import get_paths
from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)


def _compact_log() -> Path:
    """Return the compact event log path (computed lazily to avoid git at import time)."""
    gen = get_paths().generated_dir
    assert gen is not None  # noqa: S101 — always set by model_post_init
    return gen / "compact-events.jsonl"


def post_compact() -> int:
    """Log compaction event for observability."""
    with _tracer.start_as_current_span("mde.hook.post_compact") as span:
        span.set_attribute("hook.event", "PostCompact")

        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "event": "post_compact",
        }

        log_path = _compact_log()
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            span.record_exception(exc)
            print(f"PostCompact: could not log event: {exc}", file=sys.stderr)

        logger.bind(hook="post_compact").info("hook_completed")
        return 0

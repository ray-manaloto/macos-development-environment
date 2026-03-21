"""PostCompact hook — logs compaction event for observability.

Called by Claude Code after context compaction occurs.
Logs the event so research state can be tracked across compactions.
Always exits 0 (never blocks compaction).
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_COMPACT_LOG = Path(".artifacts/compact-events.jsonl")


def post_compact() -> int:
    """Log compaction event for observability."""
    record = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "event": "post_compact",
    }

    try:
        _COMPACT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _COMPACT_LOG.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:
        print(f"PostCompact: could not log event: {exc}", file=sys.stderr)

    return 0

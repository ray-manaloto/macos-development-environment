"""PostCompact hook — logs compaction event for observability.

Called by Claude Code after context compaction occurs.
Logs the event so research state can be tracked across compactions.
Always exits 0 (never blocks compaction).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    """Return the git repository root, falling back to cwd on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        pass
    return Path.cwd()


def _compact_log() -> Path:
    """Return the compact event log path (computed lazily to avoid git at import time)."""
    return _repo_root() / ".artifacts" / "compact-events.jsonl"


def post_compact() -> int:
    """Log compaction event for observability."""
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
        print(f"PostCompact: could not log event: {exc}", file=sys.stderr)

    return 0

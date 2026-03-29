"""Shared local-write utilities for remember enforcement hooks.

The remember plugin's Haiku pipeline requires API keys we don't carry
(subscription-only policy). These hooks use a LOCAL write path instead,
appending timestamped entries to .generated/remember/now.md so the next
session's /remember consolidation picks them up.
"""

from __future__ import annotations

import contextlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mde.log import logger


def _repo_root() -> Path:
    """Return the git repository root, falling back to cwd."""
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return Path.cwd()


def remember_dir() -> Path:
    """Return the remember data directory (.generated/remember/)."""
    return _repo_root() / ".generated" / "remember"


def append_now_entry(event: str, message: str) -> bool:
    """Append a timestamped entry to .generated/remember/now.md.

    Returns True if the write succeeded, False otherwise.
    """
    rdir = remember_dir()
    try:
        rdir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.bind(error=str(exc)).warning("remember_dir_create_failed")
        return False

    now_file = rdir / "now.md"
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n[{ts}] ({event}) {message}\n"

    try:
        with now_file.open("a") as f:
            f.write(entry)
    except OSError as exc:
        logger.bind(error=str(exc)).warning("remember_now_write_failed")
        return False
    return True


def recent_git_summary(n: int = 5) -> str:
    """Return a short summary of recent git activity for context."""
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return "(git log unavailable)"

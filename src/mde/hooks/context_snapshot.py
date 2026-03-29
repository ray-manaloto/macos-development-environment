"""SessionStart hook — write context snapshot of recent changes.

Captures git diff HEAD~1..HEAD --stat and branch info into
.generated/context-snapshot.json so each session knows what
changed since the last commit. Inspired by superpowers-optimized
pattern (context-snapshot.json at session start).

Always exits 0 (never blocks session start).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "name": "context-snapshot",
    "help": "Write .generated/context-snapshot.json at session start",
    "entry": "context_snapshot",
}

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)

_GENERATED_DIR = Path(".generated")
_SNAPSHOT_PATH = _GENERATED_DIR / "context-snapshot.json"


def _run_git(args: list[str], *, timeout: int = 5) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def context_snapshot() -> int:
    """Write context snapshot JSON with recent change summary."""
    with _tracer.start_as_current_span("mde.hook.context_snapshot") as span:
        span.set_attribute("hook.event", "SessionStart")

        try:
            snapshot = _build_snapshot()
            _GENERATED_DIR.mkdir(parents=True, exist_ok=True)
            _SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n")
            logger.bind(path=str(_SNAPSHOT_PATH)).info("context_snapshot_written")
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).warning("context_snapshot_failed")

        # Never block session start
        return 0


def _build_snapshot() -> dict:
    """Gather git state into a snapshot dict."""
    branch = _run_git(["branch", "--show-current"])
    head_sha = _run_git(["rev-parse", "--short", "HEAD"])
    diff_stat = _run_git(["diff", "HEAD~1..HEAD", "--stat"])
    diff_files = _run_git(["diff", "HEAD~1..HEAD", "--name-only"])
    uncommitted = _run_git(["diff", "--name-only"])
    untracked = _run_git(["ls-files", "--others", "--exclude-standard"])

    changed_files = [f for f in diff_files.splitlines() if f]
    uncommitted_files = [f for f in uncommitted.splitlines() if f]
    untracked_files = [f for f in untracked.splitlines() if f]

    return {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "branch": branch,
        "head": head_sha,
        "last_commit_diff_stat": diff_stat,
        "last_commit_files_changed": changed_files,
        "uncommitted_files": uncommitted_files,
        "untracked_files": untracked_files[:20],  # cap to avoid bloat
    }

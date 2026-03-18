"""TaskCompleted hook — blocks completion without verification evidence.

Called by Claude Code when a task is marked complete.
Reads JSON from stdin with: task_id, task_subject, task_description,
teammate_name, team_name.

Exit 2 = BLOCK completion (missing evidence).
Exit 0 = ALLOW completion.
"""

from __future__ import annotations

import json
import re
import sys

_EVIDENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:exit(?:ed)?|return(?:ed)?)\s+(?:code\s+)?0", re.IGNORECASE),
    re.compile(r"(?:all\s+)?tests?\s+pass(?:ed|ing)?", re.IGNORECASE),
    re.compile(r"PASSED", re.IGNORECASE),
    re.compile(r"✓|✅|☑", re.IGNORECASE),
    re.compile(r"verified|confirmed|validated", re.IGNORECASE),
    re.compile(r"ruff\s+check.*ok", re.IGNORECASE),
    re.compile(r"ty\s+check.*ok", re.IGNORECASE),
    re.compile(r"pytest.*passed", re.IGNORECASE),
]


def _has_evidence(text: str) -> bool:
    """Check if text contains verification evidence patterns."""
    return any(p.search(text) for p in _EVIDENCE_PATTERNS)


def verify_task_completion() -> int:
    """Read task JSON from stdin, check for verification evidence."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # If we can't parse input, don't block
        return 0

    description = data.get("task_description", "")
    subject = data.get("task_subject", "")
    combined = f"{subject} {description}"

    if not combined.strip():
        # No content to check — allow
        return 0

    if _has_evidence(combined):
        return 0

    # Block: no verification evidence found
    print(
        "BLOCKED: Task completion requires verification evidence. "
        "Run proof commands (tests, linting, type checks) and include "
        "results in your task description before completing.",
        file=sys.stderr,
    )
    return 2

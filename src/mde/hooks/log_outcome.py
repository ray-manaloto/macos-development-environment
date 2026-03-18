"""PostToolUse hook — logs edit outcomes for self-learning pattern analysis.

Called by Claude Code after Write or Edit tool use.
Reads JSON from stdin with: tool_name, tool_input, tool_response.

Always exits 0 (never blocks).
Appends structured JSONL to .artifacts/edit-outcomes.jsonl.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_OUTCOME_FILE = Path(".artifacts/edit-outcomes.jsonl")


def _extract_file_path(tool_input: dict[str, object]) -> str:
    """Extract the file path from tool input."""
    # Both Write and Edit tools use 'file_path'
    return str(tool_input.get("file_path", "unknown"))


def log_edit_outcome() -> int:
    """Read tool JSON from stdin, log outcome to JSONL file."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    file_path = _extract_file_path(tool_input)

    record = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "tool": tool_name,
        "file": file_path,
        "operation": "write" if tool_name == "Write" else "edit",
    }

    try:
        _OUTCOME_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _OUTCOME_FILE.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        # Never block on logging failures
        pass

    return 0

"""PostToolUse hook — logs edit outcomes for self-learning pattern analysis.

Called by Claude Code after Write or Edit tool use.
Reads JSON from stdin with: tool_name, tool_input, tool_response.

Always exits 0 (never blocks).
Appends structured JSONL to .artifacts/edit-outcomes.jsonl.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_OUTCOME_FILE = Path(".artifacts/edit-outcomes.jsonl")


def _extract_file_path(tool_input: dict[str, object]) -> str:
    """Extract the file path from tool input."""
    # Both Write and Edit tools use 'file_path'
    return str(tool_input.get("file_path", "unknown"))


def log_edit_outcome() -> int:
    """Read tool JSON from stdin, log outcome to JSONL file."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="log_edit_outcome", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("log_edit_outcome", "PostToolUse", data) as span:
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})
        if not isinstance(tool_input, dict):
            tool_input = {}

        file_path = _extract_file_path(tool_input)
        span.set_attribute("hook.tool_name", tool_name)
        span.set_attribute("hook.file_path", file_path)

        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "tool": tool_name,
            "file": file_path,
            "operation": {"Write": "write", "Edit": "edit"}.get(str(tool_name), "unknown"),
        }

        try:
            _OUTCOME_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _OUTCOME_FILE.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            # Never block on logging failures
            span.record_exception(exc)

        session_id = data.get("session_id", "")
        logger.bind(
            hook="log_edit_outcome",
            tool=tool_name,
            file=file_path,
            session_id=session_id,
        ).info("hook_completed")
        return 0

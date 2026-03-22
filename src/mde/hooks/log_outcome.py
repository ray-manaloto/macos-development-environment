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

from mde.observability import get_logger, get_tracer

_logger = get_logger(__name__)
_tracer = get_tracer(__name__)

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

    session_id = data.get("session_id", "")
    tool_use_id = data.get("tool_use_id", "")

    with _tracer.start_as_current_span("mde.hook.log_edit_outcome") as span:
        span.set_attribute("claude.session_id", session_id)
        span.set_attribute("claude.tool_use_id", tool_use_id)
        span.set_attribute("hook.event", "PostToolUse")

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

        _logger.info(
            "hook_completed",
            hook="log_edit_outcome",
            tool=tool_name,
            file=file_path,
            session_id=session_id,
        )
        return 0

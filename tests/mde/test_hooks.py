"""Tests for Claude Code hook handlers."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch


class TestLogEditOutcome:
    """Tests for the PostToolUse hook handler."""

    def test_logs_write_operation(self, tmp_path: object) -> None:
        from mde.hooks import log_outcome

        outfile = tmp_path / "edit-outcomes.jsonl"  # type: ignore[operator]
        with patch.object(log_outcome, "_OUTCOME_FILE", outfile):
            data = {
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/test.py"},
                "tool_response": "ok",
            }
            stdin = io.StringIO(json.dumps(data))
            with patch.object(sys, "stdin", stdin):
                assert log_outcome.log_edit_outcome() == 0

        lines = outfile.read_text().strip().split("\n")  # type: ignore[union-attr]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["tool"] == "Write"
        assert record["file"] == "/tmp/test.py"
        assert record["operation"] == "write"

    def test_handles_invalid_json(self) -> None:
        from mde.hooks.log_outcome import log_edit_outcome

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert log_edit_outcome() == 0

"""Tests for Claude Code hook handlers."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch


class TestVerifyTaskCompletion:
    """Tests for the TaskCompleted hook handler."""

    def test_allows_with_evidence(self) -> None:
        from mde.hooks.verify_task import verify_task_completion

        data = {"task_description": "All tests passed. Exit code 0.", "task_subject": "Fix bug"}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert verify_task_completion() == 0

    def test_blocks_without_evidence(self) -> None:
        from mde.hooks.verify_task import verify_task_completion

        data = {"task_description": "I think it works now.", "task_subject": "Fix bug"}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert verify_task_completion() == 2

    def test_allows_empty_input(self) -> None:
        from mde.hooks.verify_task import verify_task_completion

        data = {"task_description": "", "task_subject": ""}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert verify_task_completion() == 0

    def test_allows_invalid_json(self) -> None:
        from mde.hooks.verify_task import verify_task_completion

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert verify_task_completion() == 0


class TestCheckTeammateWork:
    """Tests for the TeammateIdle hook handler."""

    def test_allows_idle_by_default(self) -> None:
        from mde.hooks.check_teammate import check_teammate_work

        data = {"teammate_name": "coder", "team_name": "test-team"}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert check_teammate_work() == 0


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

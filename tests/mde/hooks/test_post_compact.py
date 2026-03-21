"""Tests for the PostCompact hook handler."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def test_post_compact_returns_zero() -> None:
    """PostCompact should always succeed (never block compaction)."""
    from mde.hooks.post_compact import post_compact

    result = post_compact()
    assert result == 0


def test_post_compact_writes_valid_json_to_log(monkeypatch: object) -> None:
    """PostCompact should write a valid JSON record to the compact log."""
    import mde.hooks.post_compact as module

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / ".artifacts" / "compact-events.jsonl"
        monkeypatch.setattr(module, "_COMPACT_LOG", log_path)

        from mde.hooks.post_compact import post_compact

        result = post_compact()

        assert result == 0
        assert log_path.exists(), "compact-events.jsonl was not created"
        lines = log_path.read_text().splitlines()
        assert len(lines) == 1, f"Expected 1 log line, got {len(lines)}"
        record = json.loads(lines[0])
        assert record["event"] == "post_compact"
        assert "timestamp" in record


def test_post_compact_cli_dispatch() -> None:
    """CLI should dispatch 'hooks post-compact' correctly."""
    proc = subprocess.run(
        ["uv", "run", "mde-py", "hooks", "post-compact"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0

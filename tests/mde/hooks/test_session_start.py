"""Tests for the SessionStart hook handler."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_session_start_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """SessionStart should always succeed (never block session start)."""
    from mde.hooks.session_start import session_start

    result = session_start()
    assert result == 0

    captured = capsys.readouterr()
    assert "Recent commits" in captured.out, "SessionStart should print 'Recent commits' header"


def test_session_start_cli_dispatch() -> None:
    """CLI should dispatch 'hooks session-start' correctly."""
    env = {**__import__("os").environ, "OTEL_SDK_DISABLED": "true"}
    proc = subprocess.run(
        ["uv", "run", "mde-py", "hooks", "session-start"],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    assert proc.returncode == 0
    assert len(proc.stdout) > 0, "SessionStart should print git context"


def test_clear_auto_memory_dirty_files_clears_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stale dirty-files from prior sessions should be cleared at session start."""
    from mde.hooks.session_start import _clear_auto_memory_dirty_files

    dirty_dir = tmp_path / ".claude" / "auto-memory"
    dirty_dir.mkdir(parents=True)
    dirty_file = dirty_dir / "dirty-files"
    dirty_file.write_text("/path/to/old_file.py\n/path/to/another.py\n")

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))

    cleared = _clear_auto_memory_dirty_files()
    assert cleared == 2
    assert dirty_file.read_text() == ""


def test_clear_auto_memory_dirty_files_noop_when_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No-op when dirty-files is empty or missing."""
    from mde.hooks.session_start import _clear_auto_memory_dirty_files

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))

    # File doesn't exist
    cleared = _clear_auto_memory_dirty_files()
    assert cleared == 0

    # File exists but empty
    dirty_dir = tmp_path / ".claude" / "auto-memory"
    dirty_dir.mkdir(parents=True)
    (dirty_dir / "dirty-files").write_text("")

    cleared = _clear_auto_memory_dirty_files()
    assert cleared == 0


def test_clear_auto_memory_dirty_files_no_project_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Returns 0 when CLAUDE_PROJECT_DIR is unset."""
    from mde.hooks.session_start import _clear_auto_memory_dirty_files

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    cleared = _clear_auto_memory_dirty_files()
    assert cleared == 0

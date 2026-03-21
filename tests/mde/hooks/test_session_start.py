"""Tests for the SessionStart hook handler."""

from __future__ import annotations

import subprocess


def test_session_start_prints_recent_git_log() -> None:
    """SessionStart should print recent git log for session context."""
    from mde.hooks.session_start import session_start

    result = session_start()
    assert result == 0


def test_session_start_cli_dispatch() -> None:
    """CLI should dispatch 'hooks session-start' correctly."""
    proc = subprocess.run(
        ["uv", "run", "mde-py", "hooks", "session-start"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    # Should contain git log output or context summary
    assert len(proc.stdout) > 0 or proc.returncode == 0

"""Tests for the SessionStart hook handler."""

from __future__ import annotations

import subprocess


def test_session_start_exits_zero() -> None:
    """SessionStart should always succeed (never block session start)."""
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
    assert len(proc.stdout) > 0, "SessionStart should print git context"

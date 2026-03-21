"""Tests for the PostCompact hook handler."""

from __future__ import annotations

import subprocess


def test_post_compact_returns_zero() -> None:
    """PostCompact should always succeed (never block compaction)."""
    from mde.hooks.post_compact import post_compact

    result = post_compact()
    assert result == 0


def test_post_compact_cli_dispatch() -> None:
    """CLI should dispatch 'hooks post-compact' correctly."""
    proc = subprocess.run(
        ["uv", "run", "mde-py", "hooks", "post-compact"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0

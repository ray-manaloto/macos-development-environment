"""Tests that ty type checker passes on all source files."""

from __future__ import annotations

import subprocess


def test_ty_check_passes() -> None:
    """Type checker must pass with zero errors."""
    result = subprocess.run(
        ["uv", "run", "ty", "check", "src/mde/"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"ty check failed:\n{result.stdout}\n{result.stderr}"

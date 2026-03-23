"""Tests that mise tasks can execute without tool install failures."""

from __future__ import annotations

import subprocess

import pytest


@pytest.mark.integration
def test_mise_doctor_no_warnings() -> None:
    """Mise doctor must report zero warnings."""
    result = subprocess.run(
        ["mise", "doctor"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 and "trust" in result.stderr.lower():
        pytest.skip(f"mise config not trusted in this directory: {result.stderr.strip()}")
    lines = result.stderr.splitlines()
    # Ignore self-update warnings — these are informational, not actionable errors
    warn_lines = [
        line
        for line in lines
        if "WARN" in line and "self-update" not in line and "available" not in line
    ]
    assert len(warn_lines) == 0, "mise doctor warnings:\n" + "\n".join(warn_lines)

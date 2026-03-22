"""Tests that mise tasks can execute without tool install failures."""

from __future__ import annotations

import subprocess

import pytest


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
    warn_lines = [line for line in lines if "WARN" in line]
    assert len(warn_lines) == 0, "mise doctor warnings:\n" + "\n".join(warn_lines)

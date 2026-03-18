"""Tests that mise tasks can execute without tool install failures."""

from __future__ import annotations

import subprocess


def test_mise_doctor_no_warnings() -> None:
    """Mise doctor must report zero warnings."""
    result = subprocess.run(
        ["mise", "doctor"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    lines = result.stderr.splitlines()
    warn_lines = [line for line in lines if "WARN" in line]
    assert len(warn_lines) == 0, "mise doctor warnings:\n" + "\n".join(warn_lines)

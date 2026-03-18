"""Secrets smoke test."""

from __future__ import annotations

import subprocess


def run_smoke_test() -> int:
    """Run secrets availability smoke test.

    Returns:
        Exit code.
    """
    print("==> Running secrets smoke test")
    proc = subprocess.run(
        ["bash", "scripts/secrets-smoke-test.sh"],
        timeout=30,
    )
    return proc.returncode

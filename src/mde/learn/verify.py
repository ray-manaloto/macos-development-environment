"""Learning registry verification."""

from __future__ import annotations

import subprocess


def verify_learning() -> int:
    """Verify learning registry coverage and writeback requirements.

    Returns:
        Exit code.
    """
    print("==> Verifying learning registry")
    proc = subprocess.run(
        ["bash", "scripts/mde-learn-verify.sh"],
        timeout=30,
    )
    return proc.returncode

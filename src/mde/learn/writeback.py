"""Learning writeback to registry."""

from __future__ import annotations

import subprocess


def run_writeback() -> int:
    """Run learning writeback to update the registry.

    Returns:
        Exit code.
    """
    print("==> Running learning writeback")
    proc = subprocess.run(
        ["bash", "scripts/mde-learning-writeback.sh"],
        timeout=60,
    )
    return proc.returncode

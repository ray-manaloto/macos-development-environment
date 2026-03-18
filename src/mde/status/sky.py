"""SkyPilot status."""

from __future__ import annotations

import shutil
import subprocess


def show_sky_status() -> int:
    """Show SkyPilot cluster status.

    Returns:
        Exit code.
    """
    if not shutil.which("sky"):
        print("SKIP: SkyPilot not installed")
        return 0
    proc = subprocess.run(
        ["sky", "status"],
        timeout=30,
    )
    return proc.returncode

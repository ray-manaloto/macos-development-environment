"""Status dashboard display."""

from __future__ import annotations

import subprocess


def show_dashboard() -> int:
    """Show the MDE status dashboard.

    Returns:
        Exit code.
    """
    print("==> MDE Status Dashboard")
    proc = subprocess.run(
        ["bash", "scripts/status-dashboard.sh", "--json"],
        timeout=30,
    )
    return proc.returncode

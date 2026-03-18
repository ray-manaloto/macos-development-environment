"""Agent stack installation (fabric, etc.)."""

from __future__ import annotations

import shutil
import subprocess


def install_agent_stack() -> int:
    """Install the AI agent stack tools.

    Returns:
        Exit code.
    """
    print("==> Installing agent stack")
    if not shutil.which("mise"):
        print("ERROR: mise is required")
        return 1

    proc = subprocess.run(
        ["mise", "install"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        print(f"ERROR: mise install failed: {proc.stderr}")
        return 1

    print("Agent stack installed successfully")
    return 0

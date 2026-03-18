"""AI research skills installation."""

from __future__ import annotations

import shutil
import subprocess


def install_research_skills() -> int:
    """Install AI research skill tools via mise.

    Returns:
        Exit code.
    """
    print("==> Installing AI research skills")
    if not shutil.which("mise"):
        print("ERROR: mise is required")
        return 1
    proc = subprocess.run(
        ["mise", "install"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return proc.returncode

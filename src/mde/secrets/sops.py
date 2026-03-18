"""SOPS secrets management."""

from __future__ import annotations

import shutil
import subprocess


def refresh_secrets() -> int:
    """Refresh the global SOPS runtime secret file from fnox.

    Returns:
        Exit code.
    """
    if not shutil.which("sops"):
        print("ERROR: sops is not installed")
        return 1
    if not shutil.which("fnox"):
        print("ERROR: fnox is not installed")
        return 1
    print("==> Refreshing SOPS secrets from fnox")
    proc = subprocess.run(
        ["bash", "scripts/mde-sops-secrets-refresh.sh"],
        timeout=60,
    )
    return proc.returncode

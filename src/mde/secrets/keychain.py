"""macOS Keychain secrets management."""

from __future__ import annotations

import subprocess
import sys


def import_to_keychain() -> int:
    """Import SOPS secrets into macOS Keychain via fnox.

    Returns:
        Exit code.
    """
    if sys.platform != "darwin":
        print("SKIP: Keychain operations only available on macOS")
        return 0
    print("==> Importing secrets to Keychain")
    proc = subprocess.run(
        ["bash", "scripts/mde-sops-secrets-import-keychain.sh"],
        timeout=60,
    )
    return proc.returncode

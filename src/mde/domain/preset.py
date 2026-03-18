"""Preset bundle verification."""

from __future__ import annotations

import subprocess


def verify_presets() -> int:
    """Verify preset bundle coverage and cookbook ownership.

    Returns:
        Exit code.
    """
    print("==> Verifying preset bundles")
    proc = subprocess.run(
        ["bash", "scripts/mde-preset-verify.sh"],
        timeout=30,
    )
    return proc.returncode

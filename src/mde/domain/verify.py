"""Domain catalog verification."""

from __future__ import annotations

import subprocess


def verify_domains() -> int:
    """Verify domain catalog coverage and team config delegation.

    Returns:
        Exit code.
    """
    print("==> Verifying domain catalog")
    proc = subprocess.run(
        ["bash", "scripts/mde-domain-verify.sh"],
        timeout=30,
    )
    return proc.returncode

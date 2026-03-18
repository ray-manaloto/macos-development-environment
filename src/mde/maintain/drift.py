"""Drift detection for tool ownership and runtime configs."""

from __future__ import annotations

import shutil
import subprocess


def check_drift() -> int:
    """Check for runtime/tool ownership drift.

    Returns:
        Exit code (0 = no drift, 1 = drift detected).
    """
    drift_found = False

    # Check chezmoi drift
    if shutil.which("chezmoi"):
        proc = subprocess.run(
            ["chezmoi", "verify", "--exclude=scripts"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            print("DRIFT: chezmoi managed files have diverged")
            drift_found = True

    # Check mise tool versions
    if shutil.which("mise"):
        proc = subprocess.run(
            ["mise", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            print("DRIFT: mise doctor reports issues")
            drift_found = True

    if not drift_found:
        print("No drift detected")
    return 1 if drift_found else 0

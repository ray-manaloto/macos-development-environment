"""Deterministic host remediation workflow."""

from __future__ import annotations


def run_remediate() -> int:
    """Run deterministic host remediation.

    Returns:
        Exit code.
    """
    from mde.maintain.drift import check_drift
    from mde.maintain.update import run_update

    print("==> Running remediation workflow")
    drift_code = check_drift()
    if drift_code != 0:
        print("==> Drift detected, running update")
        return run_update()
    print("==> No remediation needed")
    return 0

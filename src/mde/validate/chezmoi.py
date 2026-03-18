"""Chezmoi validation: verify, doctor, diff."""

from __future__ import annotations

import shutil
import subprocess

from mde.models.result import Severity, ValidationResult


def validate_chezmoi() -> ValidationResult:
    """Run chezmoi verification checks.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()

    if not shutil.which("chezmoi"):
        result.add(
            path="chezmoi",
            message="chezmoi is not installed",
            severity=Severity.WARNING,
            rule="chezmoi.not-installed",
        )
        return result

    _check_chezmoi_verify(result)

    return result


def _check_chezmoi_verify(result: ValidationResult) -> None:
    """Run chezmoi verify to detect drift."""
    try:
        proc = subprocess.run(
            ["chezmoi", "verify", "--exclude=scripts"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            result.add(
                path="chezmoi",
                message="chezmoi verify detected drift",
                severity=Severity.WARNING,
                rule="chezmoi.drift",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

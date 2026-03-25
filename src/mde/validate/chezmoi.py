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
    _check_chezmoi_doctor(result)

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
                severity=Severity.ERROR,
                rule="chezmoi.drift",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def _check_chezmoi_doctor(result: ValidationResult) -> None:
    """Run chezmoi doctor and treat unexpected warnings as errors.

    Known benign warnings (working-tree dirty, suspicious-entries for
    .chezmoisource) are filtered out.
    """
    benign_patterns = (
        "working-tree",
        "suspicious-entries",
    )
    try:
        proc = subprocess.run(
            ["chezmoi", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in proc.stdout.splitlines():
            if not line.startswith("warning"):
                continue
            if any(p in line for p in benign_patterns):
                continue
            # Extract check name and message from doctor output
            parts = line.split(None, maxsplit=2)
            msg = parts[-1] if len(parts) > 1 else line
            result.add(
                path="chezmoi",
                message=f"chezmoi doctor warning: {msg.strip()}",
                severity=Severity.ERROR,
                rule="chezmoi.doctor",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

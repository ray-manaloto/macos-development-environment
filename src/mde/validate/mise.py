"""Mise-specific validation: mise fmt --check, mise doctor."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mde.models.result import Severity, ValidationResult


def validate_mise(root: Path | None = None) -> ValidationResult:
    """Run mise validation checks.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    if not shutil.which("mise"):
        result.add(
            path="mise",
            message="mise is not installed",
            severity=Severity.WARNING,
            rule="mise.not-installed",
        )
        return result

    _check_mise_fmt(root, result)
    _check_mise_doctor(result)

    return result


def _check_mise_fmt(root: Path, result: ValidationResult) -> None:
    """Run mise fmt --check to verify TOML formatting."""
    mise_toml = root / ".mise.toml"
    if not mise_toml.exists():
        return

    result.files_checked += 1
    try:
        proc = subprocess.run(
            ["mise", "fmt", "--check"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=30,
        )
        if proc.returncode != 0:
            result.add(
                path=str(mise_toml),
                message="mise fmt --check failed: TOML needs formatting",
                severity=Severity.ERROR,
                rule="mise.fmt",
                fixable=True,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def _check_mise_doctor(result: ValidationResult) -> None:
    """Run mise doctor for health checks."""
    try:
        proc = subprocess.run(
            ["mise", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            for line in proc.stderr.splitlines():
                if "WARN" in line or "ERROR" in line:
                    result.add(
                        path="mise",
                        message=f"mise doctor: {line.strip()}",
                        severity=Severity.ERROR,
                        rule="mise.doctor",
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

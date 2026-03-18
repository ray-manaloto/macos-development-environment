"""Homebrew health validation."""

from __future__ import annotations

import shutil
import subprocess

from mde.models.result import Severity, ValidationResult

EXPECTED_FORMULAE = {"gnupg", "curl", "chafa", "tree"}


def validate_brew() -> ValidationResult:
    """Validate Homebrew installation and formula inventory."""
    result = ValidationResult()
    if not shutil.which("brew"):
        result.add(
            "brew",
            "brew is not installed",
            severity=Severity.WARNING,
            rule="brew.not-installed",
        )
        return result
    _check_brew_doctor(result)
    _check_unexpected_formulae(result)
    return result


def _check_brew_doctor(result: ValidationResult) -> None:
    try:
        proc = subprocess.run(["brew", "doctor"], capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            for line in proc.stderr.splitlines():
                if line.strip():
                    result.add_warning(
                        "brew",
                        f"brew doctor: {line.strip()}",
                        rule="brew.doctor",
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def _check_unexpected_formulae(result: ValidationResult) -> None:
    try:
        proc = subprocess.run(
            ["brew", "leaves", "--installed-on-request"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            result.files_checked += 1
            installed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
            unexpected = installed - EXPECTED_FORMULAE
            # Filter out tapped formulae (e.g. charmbracelet/tap/crush)
            for formula in sorted(unexpected):
                if "/" not in formula:
                    result.add_warning(
                        "brew",
                        f"Unexpected formula not in expected set: {formula}",
                        rule="brew.unexpected-formula",
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

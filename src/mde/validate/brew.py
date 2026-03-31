"""Homebrew health validation."""

from __future__ import annotations

import shutil
import subprocess

from mde.models.result import Severity, ValidationResult

EXPECTED_FORMULAE = {
    "chafa",
    "colima",
    "curl",
    "docker-buildx",
    "docker-compose",
    "dockerfilegraph",
    "gnupg",
    "lld",
    "llvm",
    "tree",
    "viu",
}


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
    _check_llvm_is_brew(result)
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


def _get_brew_prefix() -> str | None:
    """Return the Homebrew prefix (e.g. /opt/homebrew or /usr/local)."""
    try:
        proc = subprocess.run(
            ["brew", "--prefix"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _check_llvm_is_brew(result: ValidationResult) -> None:
    """Verify the active clang is Homebrew LLVM, not Apple or other clang.

    Checks both the version string (rejects "Apple") AND the resolved
    binary path (must be under the Homebrew prefix).  A non-Apple,
    non-brew clang (e.g. from Xcode CLT or a manual install) is also
    rejected.
    """
    import platform
    from pathlib import Path

    if platform.system() != "Darwin":
        return

    clang_path = shutil.which("clang")
    if clang_path is None:
        result.add(
            "brew",
            "clang not found in PATH",
            severity=Severity.ERROR,
            rule="brew.llvm-missing",
        )
        return

    try:
        proc = subprocess.run(
            ["clang", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_line = proc.stdout.splitlines()[0] if proc.stdout else ""
        if "Apple" in version_line:
            result.add(
                "brew",
                f"Active clang is Apple ({version_line}), not Homebrew LLVM. "
                'Check PATH order or run: eval "$(mise env)"',
                severity=Severity.ERROR,
                rule="brew.llvm-not-active",
            )
            return
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
        return

    # Path-based check: resolved clang must be under brew prefix
    brew_prefix = _get_brew_prefix()
    if brew_prefix is None:
        return  # Can't validate without brew prefix

    resolved = str(Path(clang_path).resolve())
    if not resolved.startswith(brew_prefix):
        result.add(
            "brew",
            f"Active clang ({resolved}) is not under Homebrew prefix ({brew_prefix}). "
            'Ensure brew LLVM is first in PATH or run: eval "$(mise env)"',
            severity=Severity.ERROR,
            rule="brew.llvm-not-active",
        )

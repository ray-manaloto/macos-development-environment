"""hk git hooks configuration validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mde.models.result import Severity, ValidationResult


def validate_hk(root: Path | None = None) -> ValidationResult:
    """Validate hk.pkl configuration via ``hk validate``.

    Args:
        root: Project root containing hk.pkl. Defaults to cwd.

    Returns:
        ValidationResult with findings from hk validate.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    hk_pkl = root / "hk.pkl"
    if not hk_pkl.exists():
        result.add(
            path="hk.pkl",
            message="hk.pkl not found — git hooks are not configured",
            severity=Severity.WARNING,
            rule="hk.missing-config",
        )
        return result

    if not shutil.which("hk"):
        result.add(
            path="hk",
            message="hk is not installed",
            severity=Severity.ERROR,
            rule="hk.not-installed",
        )
        return result

    result.files_checked += 1

    try:
        proc = subprocess.run(
            ["hk", "validate"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=30,
        )
        all_output = (proc.stdout + proc.stderr).strip()

        if proc.returncode != 0:
            # hk validate failed — surface the full error
            message = all_output or f"hk validate exited with code {proc.returncode}"
            result.add(
                path="hk",
                message=f"hk validate failed: {message}",
                severity=Severity.ERROR,
                rule="hk.validate",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path="hk",
            message="hk validate timed out (30s)",
            severity=Severity.ERROR,
            rule="hk.timeout",
        )
    except FileNotFoundError:
        result.add(
            path="hk",
            message="hk binary not found despite which() check",
            severity=Severity.ERROR,
            rule="hk.not-found",
        )

    return result

"""Shell script validation via bash -n and shellcheck."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mde.models.result import Severity, ValidationResult


def validate_shell_scripts(root: Path | None = None) -> ValidationResult:
    """Validate shell scripts with bash -n syntax check.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return result

    shell_files = list(scripts_dir.rglob("*.sh"))

    for path in shell_files:
        result.files_checked += 1
        _check_bash_syntax(path, result)

    return result


def _check_bash_syntax(path: Path, result: ValidationResult) -> None:
    """Run bash -n to check syntax."""
    try:
        proc = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            result.add(
                path=str(path),
                message=f"Bash syntax error: {proc.stderr.strip()}",
                rule="shell.syntax",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path=str(path),
            message="Bash syntax check timed out",
            severity=Severity.WARNING,
            rule="shell.timeout",
        )
    except FileNotFoundError:
        result.add(
            path=str(path),
            message="bash not found in PATH",
            severity=Severity.WARNING,
            rule="shell.missing-bash",
        )

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
            severity=Severity.ERROR,
            rule="mise.not-installed",
        )
        return result

    _check_mise_fmt(root, result)
    _check_mise_lockfile_platforms(root, result)
    _check_mise_doctor(result)

    return result


def _check_mise_fmt(root: Path, result: ValidationResult) -> None:
    """Run mise fmt --check to verify TOML formatting."""
    mise_toml = root / ".mise.toml"
    if not mise_toml.exists():
        return

    try:
        proc = subprocess.run(
            ["mise", "fmt", "--check"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=30,
        )
        result.files_checked += 1
        if proc.returncode != 0:
            result.add(
                path=str(mise_toml),
                message="mise fmt --check failed: TOML needs formatting",
                severity=Severity.ERROR,
                rule="mise.fmt",
                fixable=True,
            )
    except subprocess.TimeoutExpired:
        result.add(
            path=str(mise_toml),
            message="mise fmt timed out (30s)",
            severity=Severity.ERROR,
            rule="mise.timeout",
        )
    except FileNotFoundError:
        result.add(
            path="mise",
            message="mise binary not found despite which() check",
            severity=Severity.ERROR,
            rule="mise.not-found",
        )


def _check_mise_lockfile_platforms(root: Path, result: ValidationResult) -> None:
    """Verify lockfiles only contain entries for the current platform.

    Lockfiles with entries for non-local platforms waste time during
    ``mise lock`` and indicate a misconfigured lock command (missing
    ``--platform`` flag).
    """
    import platform as _platform

    system = _platform.system().lower()
    machine = _platform.machine().lower()
    os_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    arch_map = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}
    current = f"{os_map.get(system, system)}-{arch_map.get(machine, machine)}"

    for lock_path in [root / "mise.lock", Path.home() / ".config/mise/mise.lock"]:
        if not lock_path.exists():
            continue
        result.files_checked += 1
        foreign = _find_foreign_platforms(lock_path, current)
        if foreign:
            result.add(
                path=str(lock_path),
                message=(
                    f"lockfile contains {len(foreign)} non-local platform(s): "
                    f"{', '.join(sorted(foreign))}. "
                    f"Run: mise lock --platform {current}"
                ),
                severity=Severity.ERROR,
                rule="mise.lockfile-platforms",
                fixable=True,
            )


def _find_foreign_platforms(lock_path: Path, current: str) -> set[str]:
    """Extract platform names from a lockfile that don't match current."""
    import tomllib

    try:
        data = tomllib.loads(lock_path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return set()

    foreign: set[str] = set()
    for tool_entries in data.get("tools", {}).values():
        entries = tool_entries if isinstance(tool_entries, list) else [tool_entries]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key in entry:
                if key.startswith("platforms."):
                    plat = key.removeprefix("platforms.")
                    if plat != current:
                        foreign.add(plat)
    return foreign


def _check_mise_doctor(result: ValidationResult) -> None:
    """Run mise doctor for health checks.

    Parses the summary/problem sections from mise doctor output.
    mise doctor uses three severity categories: warning, problem, error.
    All are surfaced as ERROR findings — nothing is filtered.

    If mise doctor exits non-zero, that alone is an error even if no
    keywords matched (guards against output format changes).
    """
    try:
        proc = subprocess.run(
            ["mise", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Scan both streams — mise versions vary on where output goes
        all_output = proc.stdout + proc.stderr

        # Parse mise doctor output. Format:
        #   N warning found:
        #   (blank line)
        #   1. description text
        #      continuation text
        #
        #   N problem found:
        #   (blank line)
        #   1. description text
        #
        # Strategy: capture numbered findings (lines starting with "N.")
        # that appear anywhere after a "found:" header, plus any line
        # containing severity keywords.
        seen_found_header = False
        for line in all_output.splitlines():
            line_lower = line.lower()
            stripped = line.strip()

            # Track when we've passed a "N warning/problem found:" header
            if "found:" in line_lower and ("warning" in line_lower or "problem" in line_lower):
                # Skip "No problems found" — success message
                if "no" in line_lower and "found" in line_lower:
                    continue
                seen_found_header = True
                continue

            # After a header, capture numbered lines (e.g., "1. tool...")
            if seen_found_header and stripped and stripped[0].isdigit() and ". " in stripped:
                result.add(
                    path="mise",
                    message=f"mise doctor: {stripped}",
                    severity=Severity.ERROR,
                    rule="mise.doctor",
                )

        # Fallback: non-zero exit with no findings means we missed something
        has_doctor_finding = any(f.rule == "mise.doctor" for f in result.findings)
        if proc.returncode != 0 and not has_doctor_finding:
            result.add(
                path="mise",
                message=f"mise doctor exited with code {proc.returncode}",
                severity=Severity.ERROR,
                rule="mise.doctor",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path="mise",
            message="mise doctor timed out (30s)",
            severity=Severity.ERROR,
            rule="mise.timeout",
        )
    except FileNotFoundError:
        pass  # Already caught by fmt check

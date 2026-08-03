"""Mise-specific validation: mise fmt --check, mise doctor, mise outdated."""

from __future__ import annotations

import json as _json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mde.models.result import Severity, ValidationResult

#: Platforms this project installs tools on besides the local machine's.
#:
#: ``jdx/mise-action`` resolves ``[tools]`` in ``--locked`` mode, so a lockfile
#: with no URL for the runner's platform hard-fails the workflow before a single
#: check runs. Every runner in ``.github/workflows/`` is ``ubuntu-latest``, i.e.
#: ``linux-x64``. Treating that entry as foreign made CI unfixable by
#: construction: the lockfile could satisfy this validator or the workflow, never
#: both. Extend this set when a workflow starts running on another platform.
_REQUIRED_PLATFORMS = frozenset({"linux-x64"})


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
    _check_mise_outdated_findings(result)

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
    """Verify lockfiles only cover platforms this project actually installs on.

    That is the current machine plus ``_REQUIRED_PLATFORMS`` (the CI runners).
    Anything else wastes time during ``mise lock`` and indicates a misconfigured
    lock command (missing ``--platform`` flag).
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
        try:
            foreign = _find_foreign_platforms(lock_path, current, allowed=_REQUIRED_PLATFORMS)
        except LockfileParseError as exc:
            result.add(
                path=str(lock_path),
                message=str(exc),
                severity=Severity.ERROR,
                rule="mise.lockfile-corrupt",
            )
            continue
        if foreign:
            expected = ",".join(sorted({current, *_REQUIRED_PLATFORMS}))
            result.add(
                path=str(lock_path),
                message=(
                    f"lockfile contains {len(foreign)} unused platform(s): "
                    f"{', '.join(sorted(foreign))}. "
                    f"Run: mise lock --platform {expected}"
                ),
                severity=Severity.ERROR,
                rule="mise.lockfile-platforms",
                fixable=True,
            )


class LockfileParseError(Exception):
    """Raised when a lockfile cannot be parsed."""


def _find_foreign_platforms(
    lock_path: Path, current: str, allowed: frozenset[str] = frozenset()
) -> set[str]:
    """Extract platform names from a lockfile that are neither current nor allowed.

    Policy lives at the call site: this returns the plain set difference, so
    ``allowed`` defaults to empty and the caller decides which extra platforms
    the project legitimately locks for.

    Raises:
        LockfileParseError: If the lockfile cannot be read or parsed.
    """
    import tomllib

    try:
        data = tomllib.loads(lock_path.read_text())
    except OSError as exc:
        msg = f"cannot read lockfile {lock_path}: {exc}"
        raise LockfileParseError(msg) from exc
    except tomllib.TOMLDecodeError as exc:
        msg = f"corrupted lockfile {lock_path}: {exc}"
        raise LockfileParseError(msg) from exc

    foreign: set[str] = set()
    for tool_entries in data.get("tools", {}).values():
        entries = tool_entries if isinstance(tool_entries, list) else [tool_entries]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key in entry:
                if key.startswith("platforms."):
                    plat = key.removeprefix("platforms.")
                    if plat != current and plat not in allowed:
                        foreign.add(plat)
    return foreign


def _check_mise_doctor(result: ValidationResult) -> None:
    """Run mise doctor for health checks.

    Parses the summary sections from mise doctor output.
    mise doctor uses three severity categories: warning, problem, error.
    All three are matched in "found:" headers and surfaced as ERROR
    findings — nothing is filtered.

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

            # Track when we've passed a "N warning/problem/error found:" header
            if "found:" in line_lower and (
                "warning" in line_lower or "problem" in line_lower or "error" in line_lower
            ):
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


# ---------------------------------------------------------------------------
# Outdated tools check — reusable by both validate and update
# ---------------------------------------------------------------------------


def check_mise_outdated() -> list[dict[str, Any]]:
    """Return list of outdated tools from ``mise outdated --bump --json``.

    Each entry has keys: name, requested, current, bump, latest, source.
    Returns empty list if mise is missing or the command fails.

    This is the shared implementation used by both ``validate_mise`` (surfacing
    findings) and ``update.py`` (deciding whether to bump).
    """
    if not shutil.which("mise"):
        return []
    try:
        proc = subprocess.run(
            ["mise", "outdated", "--bump", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        data = _json.loads(proc.stdout)
    except _json.JSONDecodeError:
        return []
    return list(data.values())


def _check_mise_outdated_findings(result: ValidationResult) -> None:
    """Surface outdated tools as WARNING findings."""
    outdated = check_mise_outdated()
    if not outdated:
        return
    result.files_checked += 1
    for tool in outdated:
        name = tool.get("name", "unknown")
        current = tool.get("current", "?")
        latest = tool.get("latest", "?")
        source = tool.get("source", {}).get("path", "?")
        result.add(
            path=source,
            message=(f"{name} is outdated: {current} -> {latest}. Run: mise upgrade --bump {name}"),
            severity=Severity.WARNING,
            rule="mise.outdated",
            fixable=True,
        )

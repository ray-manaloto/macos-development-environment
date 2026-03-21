"""Unified quality gate for the mde project.

Single entry point for all code quality checks: lint, type check, test, validate.
Called by: hk pre-commit, mise tasks, and direct CLI invocation.

Usage:
    uv run mde-py quality          # Full gate (lint + test + validate)
    uv run mde-py quality --lint   # Lint only (ruff + ty + pyright)
    uv run mde-py quality --test   # Test only (pytest)
    uv run mde-py quality --validate  # Validate only (mde-py validate)
"""

from __future__ import annotations

import subprocess
import sys

__all__ = ["run_quality_gate"]

# Each check: (name, command, description)
_LINT_CHECKS: list[tuple[str, list[str], str]] = [
    ("ruff-check", ["uv", "run", "ruff", "check", "src/", "tests/"], "Lint rules"),
    ("ruff-format", ["uv", "run", "ruff", "format", "--check", "src/", "tests/"], "Format check"),
    ("ty", ["uv", "run", "ty", "check"], "Type check (ty)"),
    ("pyright", ["uv", "run", "pyright", "src/mde/"], "Type check (pyright)"),
]

_TEST_CHECKS: list[tuple[str, list[str], str]] = [
    ("pytest", ["uv", "run", "pytest", "tests/", "-x", "-q"], "Test suite"),
]

_VALIDATE_CHECKS: list[tuple[str, list[str], str]] = [
    ("mde-validate", ["uv", "run", "mde-py", "validate"], "Config validation"),
]


def _run_check(name: str, cmd: list[str], description: str) -> bool:
    """Run a single check, return True if passed."""
    print(f"  [{name}] {description}...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # Show compact success output
        last_line = (result.stdout.strip().split("\n") or [""])[-1]
        print(f"  [{name}] {last_line or 'OK'}")
        return True
    # Show failure details
    print(f"  [{name}] FAILED (exit {result.returncode})")
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n")[-10:]:
            print(f"    {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n")[-5:]:
            print(f"    {line}")
    return False


def run_quality_gate(
    *,
    lint: bool = True,
    test: bool = True,
    validate: bool = True,
) -> int:
    """Run the quality gate. Returns 0 on success, 1 on any failure."""
    checks: list[tuple[str, list[str], str]] = []
    if lint:
        checks.extend(_LINT_CHECKS)
    if test:
        checks.extend(_TEST_CHECKS)
    if validate:
        checks.extend(_VALIDATE_CHECKS)

    if not checks:
        print("No checks selected.", file=sys.stderr)
        return 1

    passed = 0
    failed = 0
    failures: list[str] = []

    print(f"Running {len(checks)} quality checks...\n")
    for name, cmd, description in checks:
        if _run_check(name, cmd, description):
            passed += 1
        else:
            failed += 1
            failures.append(name)

    print(f"\n{'=' * 40}")
    print(f"Quality gate: {passed} passed, {failed} failed")
    if failures:
        print(f"Failed: {', '.join(failures)}")
        return 1
    print("All checks passed.")
    return 0


def cli_main(args: list[str] | None = None) -> int:
    """CLI entry point for quality gate."""
    import argparse

    parser = argparse.ArgumentParser(description="Run quality gate checks")
    parser.add_argument("--lint", action="store_true", help="Run lint checks only")
    parser.add_argument("--test", action="store_true", help="Run test checks only")
    parser.add_argument("--validate", action="store_true", help="Run validation only")

    parsed = parser.parse_args(args)

    # If no flags specified, run everything
    run_all = not (parsed.lint or parsed.test or parsed.validate)

    return run_quality_gate(
        lint=run_all or parsed.lint,
        test=run_all or parsed.test,
        validate=run_all or parsed.validate,
    )

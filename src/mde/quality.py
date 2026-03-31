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
    ("vulture", ["uv", "run", "vulture", "src/mde/"], "Dead code check"),
    ("import-linter", ["uv", "run", "lint-imports"], "Architectural contract check"),
]

_TEST_CHECKS: list[tuple[str, list[str], str]] = [
    (
        "pytest",
        ["uv", "run", "pytest", "tests/", "-x", "-q", "-m", "not integration"],
        "Test suite",
    ),
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


def _run_validate() -> tuple[bool, int]:
    """Run validation in-process, return (passed, warning_count).

    Calls ``run_validators`` directly so we get the full ValidationResult
    with warning counts — no log parsing needed.
    """
    from mde.validate import _print_findings, run_validators

    print("  [mde-validate] Config validation...", flush=True)
    result = run_validators()
    _print_findings(result)

    if not result.passed:
        print(f"  [mde-validate] FAILED ({result.error_count} errors)")
    else:
        print("  [mde-validate] OK")
    return result.passed, result.warning_count


def _print_summary(
    passed: int,
    failed: int,
    total_warnings: int,
    failures: list[str],
    *,
    strict: bool,
) -> int:
    """Print gate summary and return exit code."""
    print(f"\n{'=' * 40}")
    warning_suffix = f" ({total_warnings} warnings)" if total_warnings > 0 else ""
    print(f"Quality gate: {passed} passed, {failed} failed{warning_suffix}")
    if failures:
        print(f"Failed: {', '.join(failures)}")
        return 1
    if strict and total_warnings > 0:
        print(f"STRICT: {total_warnings} warning(s) treated as errors")
        return 1
    print("All checks passed.")
    return 0


def run_quality_gate(
    *,
    lint: bool = True,
    test: bool = True,
    validate: bool = True,
    strict: bool = False,
) -> int:
    """Run the quality gate. Returns 0 on success, 1 on any failure.

    When *strict* is True, warnings also cause a non-zero exit (for CI/agents).
    """
    checks: list[tuple[str, list[str], str]] = []
    if lint:
        checks.extend(_LINT_CHECKS)
    if test:
        checks.extend(_TEST_CHECKS)

    if not checks and not validate:
        print("No checks selected.", file=sys.stderr)
        return 1

    passed = 0
    failed = 0
    total_warnings = 0
    failures: list[str] = []

    total_checks = len(checks) + (1 if validate else 0)
    print(f"Running {total_checks} quality checks...\n")

    for name, cmd, description in checks:
        if _run_check(name, cmd, description):
            passed += 1
        else:
            failed += 1
            failures.append(name)

    # Run validation in-process to get warning counts
    if validate:
        validate_passed, warning_count = _run_validate()
        total_warnings += warning_count
        if validate_passed:
            passed += 1
        else:
            failed += 1
            failures.append("mde-validate")

    return _print_summary(passed, failed, total_warnings, failures, strict=strict)


def cli_main(args: list[str] | None = None) -> int:
    """CLI entry point for quality gate."""
    import argparse

    parser = argparse.ArgumentParser(description="Run quality gate checks")
    parser.add_argument("--lint", action="store_true", help="Run lint checks only")
    parser.add_argument("--test", action="store_true", help="Run test checks only")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat mde-validate warnings as errors (exit 1 if any warnings)",
    )

    parsed = parser.parse_args(args)

    # If no flags specified, run everything
    run_all = not (parsed.lint or parsed.test or parsed.validate)

    return run_quality_gate(
        lint=run_all or parsed.lint,
        test=run_all or parsed.test,
        validate=run_all or parsed.validate,
        strict=parsed.strict,
    )

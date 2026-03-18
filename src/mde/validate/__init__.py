"""Validation modules for MDE configs."""

from __future__ import annotations

import json
import sys

from mde.models.result import ValidationResult
from mde.validate.json_validator import validate_json_files
from mde.validate.mise import validate_mise
from mde.validate.shell import validate_shell_scripts
from mde.validate.structural import validate_structural
from mde.validate.toml import validate_toml_files
from mde.validate.yaml_validator import validate_yaml_files


def validate_all(
    *,
    fix: bool = False,
    configs_only: bool = False,
    json_output: bool = False,
) -> int:
    """Run all validators and return exit code.

    Args:
        fix: Auto-fix known issues.
        configs_only: Only validate config files, skip scripts.
        json_output: Output findings as JSON.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    result = ValidationResult()

    result.merge(validate_toml_files(fix=fix))
    result.merge(validate_yaml_files())
    result.merge(validate_json_files())
    result.merge(validate_mise())

    if not configs_only:
        result.merge(validate_shell_scripts())

    result.merge(validate_structural())

    if json_output:
        print(json.dumps(result.model_dump(), indent=2))
    else:
        _print_findings(result)

    return 0 if result.passed else 1


def _print_findings(result: ValidationResult) -> None:
    """Print findings to stderr in a human-readable format."""
    for finding in result.findings:
        loc = finding.path
        if finding.line is not None:
            loc = f"{loc}:{finding.line}"
        severity = finding.severity.value.upper()
        print(f"[{severity}] {loc}: {finding.message}", file=sys.stderr)

    errors = result.error_count
    warnings = result.warning_count
    total = result.files_checked
    print(f"\nChecked {total} files: {errors} errors, {warnings} warnings", file=sys.stderr)

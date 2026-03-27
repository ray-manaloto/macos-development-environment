"""Validation modules for MDE configs."""

from __future__ import annotations

import json
import sys

from mde.models.result import ValidationResult
from mde.validate.brew import validate_brew
from mde.validate.chezmoi import validate_chezmoi
from mde.validate.docker import validate_docker
from mde.validate.json_validator import validate_json_files
from mde.validate.memory import validate_memory
from mde.validate.mise import validate_mise
from mde.validate.package_managers import validate_package_managers
from mde.validate.plugin_health import validate_plugin_health
from mde.validate.plugins import validate_plugins
from mde.validate.shell import validate_shell_scripts
from mde.validate.skill_frontmatter import validate_skill_frontmatter
from mde.validate.skill_sync import validate_skill_sync
from mde.validate.structural import validate_structural
from mde.validate.toml import validate_toml_files
from mde.validate.yaml_validator import validate_yaml_files


def validate_all(
    *,
    fix: bool = False,
    configs_only: bool = False,
    json_output: bool = False,
    brew_only: bool = False,
    docker_only: bool = False,
    package_managers_only: bool = False,
    skills_only: bool = False,
    plugins_only: bool = False,
    plugins_health_only: bool = False,
) -> int:
    """Run validators and return exit code.

    Args:
        fix: Auto-fix known issues.
        configs_only: Only validate config files, skip scripts.
        json_output: Output findings as JSON.
        brew_only: Only run brew validation.
        docker_only: Only run docker validation.
        package_managers_only: Only run package manager dedup validation.
        skills_only: Only run skill frontmatter validation.
        plugins_only: Only run rsm-subagents plugin validation.
        plugins_health_only: Only run plugin installation health checks.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    result = ValidationResult()

    # Single-category mode
    if brew_only:
        result.merge(validate_brew())
    elif docker_only:
        result.merge(validate_docker())
    elif package_managers_only:
        result.merge(validate_package_managers())
    elif skills_only:
        result.merge(validate_skill_frontmatter())
    elif plugins_only:
        result.merge(validate_plugins())
    elif plugins_health_only:
        result.merge(validate_plugin_health())
    else:
        # Full validation
        result.merge(validate_toml_files(fix=fix))
        result.merge(validate_yaml_files())
        result.merge(validate_json_files())
        result.merge(validate_mise())
        result.merge(validate_chezmoi())
        result.merge(validate_brew())
        result.merge(validate_docker())
        result.merge(validate_memory())
        result.merge(validate_package_managers())
        result.merge(validate_skill_frontmatter())
        result.merge(validate_skill_sync())

        result.merge(validate_plugins())
        result.merge(validate_plugin_health())

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

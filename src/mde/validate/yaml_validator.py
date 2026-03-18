"""YAML syntax and structure validation."""

from __future__ import annotations

from pathlib import Path

import yaml

from mde.models.result import ValidationResult


def validate_yaml_files(root: Path | None = None) -> ValidationResult:
    """Validate all YAML files in configs/ and team configs.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    yaml_files = [
        *root.glob("configs/**/*.yaml"),
        *root.glob("configs/**/*.yml"),
        *root.glob("configs/agent-teams/**/*.yaml"),
    ]

    for path in yaml_files:
        if not path.exists():
            continue
        result.files_checked += 1
        _validate_single_yaml(path, result)

    return result


def _validate_single_yaml(path: Path, result: ValidationResult) -> None:
    """Validate a single YAML file for syntax errors."""
    try:
        content = path.read_text(encoding="utf-8")
        yaml.safe_load(content)
    except yaml.YAMLError as exc:
        result.add(
            path=str(path),
            message=f"YAML syntax error: {exc}",
            rule="yaml.syntax",
        )

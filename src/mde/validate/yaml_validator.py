"""YAML syntax and structure validation."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from mde.models.result import ValidationResult
from mde.models.team import TeamConfig

log = logging.getLogger(__name__)


def validate_yaml_files(root: Path | None = None) -> ValidationResult:
    """Validate all YAML files in configs/ and team configs.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    yaml_files = sorted(
        {
            *root.glob("configs/**/*.yaml"),
            *root.glob("configs/**/*.yml"),
        }
    )

    for path in yaml_files:
        if not path.exists():
            continue
        result.files_checked += 1
        _validate_single_yaml(path, result)

    return result


def _sanitize_templates(content: str) -> str:
    """Replace template placeholders so YAML can parse structure."""
    return content.replace("{{", "__TPL_OPEN__").replace("}}", "__TPL_CLOSE__")


def _validate_single_yaml(path: Path, result: ValidationResult) -> None:
    """Validate a single YAML file for syntax and schema errors."""
    try:
        content = path.read_text(encoding="utf-8")
        sanitized = _sanitize_templates(content)
        data = yaml.safe_load(sanitized)
    except yaml.YAMLError as exc:
        result.add(
            path=str(path),
            message=f"YAML syntax error: {exc}",
            rule="yaml.syntax",
        )
        return

    # Schema validation for agent-team configs
    if "agent-teams" in str(path) and isinstance(data, dict) and "team" in data:
        _validate_team_schema(path, data, result)


def _validate_team_schema(path: Path, data: dict, result: ValidationResult) -> None:
    """Validate agent-team config against Pydantic schema."""
    try:
        TeamConfig.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            result.add(
                path=str(path),
                message=f"Schema error at {loc}: {err['msg']}",
                rule="yaml.schema.team",
            )

"""Cross-file structural consistency checks."""

from __future__ import annotations

from pathlib import Path

from mde.models.result import Severity, ValidationResult


def validate_structural(root: Path | None = None) -> ValidationResult:
    """Check cross-file consistency.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    _check_mise_task_targets(root, result)
    _check_team_config_references(root, result)

    return result


def _check_mise_task_targets(root: Path, result: ValidationResult) -> None:
    """Verify that mise task run targets exist."""
    mise_toml = root / ".mise.toml"
    if not mise_toml.exists():
        return

    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    content = mise_toml.read_text(encoding="utf-8")
    data = tomllib.loads(content)

    tasks = data.get("tasks", {})
    if not isinstance(tasks, dict):
        return

    result.files_checked += 1
    for task_name, task_def in tasks.items():
        if not isinstance(task_def, dict):
            continue
        run_cmd = task_def.get("run", "")
        if not isinstance(run_cmd, str):
            continue
        # Check if script file references exist
        for token in run_cmd.split():
            if token.startswith("scripts/") and token.endswith(".sh"):
                script_path = root / token
                if not script_path.exists():
                    result.add(
                        path=str(mise_toml),
                        message=f"Task '{task_name}' references missing script: {token}",
                        severity=Severity.ERROR,
                        rule="structural.missing-script",
                    )


def _check_team_config_references(root: Path, result: ValidationResult) -> None:
    """Verify that team config references point to existing files."""
    teams_dir = root / "configs" / "agent-teams"
    if not teams_dir.exists():
        return

    import yaml

    for config_path in teams_dir.glob("*.yaml"):
        result.files_checked += 1
        try:
            content = config_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            continue  # Already caught by yaml validator

        if not isinstance(data, dict):
            continue

        # Check for validator script references
        validator = data.get("output_validator", "")
        if validator and not (root / validator).exists():
            result.add(
                path=str(config_path),
                message=f"Team config references missing validator: {validator}",
                severity=Severity.WARNING,
                rule="structural.missing-validator",
            )

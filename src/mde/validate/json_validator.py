"""JSON syntax validation for config files."""

from __future__ import annotations

import json
from pathlib import Path

from mde.models.result import ValidationResult


def validate_json_files(root: Path | None = None) -> ValidationResult:
    """Validate all JSON config files.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    json_files = [
        *root.glob("configs/*.json"),
        *root.glob("configs/**/*.json"),
    ]

    for path in json_files:
        if not path.exists():
            continue
        result.files_checked += 1
        _validate_single_json(path, result)

    return result


def _validate_single_json(path: Path, result: ValidationResult) -> None:
    """Validate a single JSON file for syntax errors."""
    try:
        content = path.read_text(encoding="utf-8")
        json.loads(content)
    except json.JSONDecodeError as exc:
        result.add(
            path=str(path),
            message=f"JSON syntax error: {exc}",
            rule="json.syntax",
        )

"""Validate research evaluation completeness.

Ensures every required candidate has a verdict (INSTALL/EXTRACT/REJECT)
with rationale. Prevents skipping evaluations.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from mde.models.result import ValidationResult

if TYPE_CHECKING:
    from typing import Any

_VALID_VERDICTS = frozenset({"INSTALL", "EXTRACT", "REJECT"})


def validate_evaluations(
    *,
    evaluation_path: Path,
    required_candidates: list[str],
) -> ValidationResult:
    """Validate that all required candidates have been evaluated.

    Args:
        evaluation_path: Path to the evaluation YAML file.
        required_candidates: List of candidate names that must have verdicts.

    Returns:
        ValidationResult with errors for missing/invalid evaluations.
    """
    result = ValidationResult()
    result.files_checked = 1

    if not evaluation_path.exists():
        result.add_error(
            str(evaluation_path),
            f"Evaluation file not found: {evaluation_path}",
            rule="evaluations.file-exists",
        )
        return result

    data = _load_yaml(evaluation_path, result)
    if data is None:
        return result

    evaluations: list[dict[str, Any]] = data.get("evaluations", [])
    evaluated: dict[str, dict[str, Any]] = {}
    for entry in evaluations:
        name = entry.get("name", "")
        if name:
            evaluated[name] = entry

    for candidate in required_candidates:
        if candidate not in evaluated:
            result.add_error(
                str(evaluation_path),
                f"Required candidate '{candidate}' not found — evaluation incomplete",
                rule="evaluations.completeness",
            )
            continue

        entry = evaluated[candidate]
        verdict = entry.get("verdict")

        if not verdict:
            result.add_error(
                str(evaluation_path),
                f"Candidate '{candidate}' has missing verdict"
                " — must be INSTALL, EXTRACT, or REJECT",
                rule="evaluations.verdict-required",
            )
            continue

        if verdict not in _VALID_VERDICTS:
            result.add_error(
                str(evaluation_path),
                f"Candidate '{candidate}' has invalid verdict '{verdict}'"
                " — must be INSTALL, EXTRACT, or REJECT",
                rule="evaluations.verdict-valid",
            )
            continue

        if not entry.get("rationale"):
            result.add_warning(
                str(evaluation_path),
                f"Candidate '{candidate}' has verdict '{verdict}' but no rationale",
                rule="evaluations.rationale-recommended",
            )

    return result


def _load_yaml(path: Path, result: ValidationResult) -> dict[str, Any] | None:
    """Load and parse a YAML file, adding errors on failure."""
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error(str(path), f"Invalid YAML: {e}", rule="evaluations.yaml-parse")
        return None
    if not isinstance(data, dict):
        result.add_error(
            str(path), "Expected YAML mapping at top level", rule="evaluations.yaml-structure"
        )
        return None
    return data

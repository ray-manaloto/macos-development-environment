"""Tests for research evaluation completeness validator."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from mde.validate.evaluations import validate_evaluations


def test_all_candidates_evaluated(tmp_path: Path) -> None:
    """All required candidates have verdicts."""
    yaml_file = tmp_path / "evaluations.yaml"
    yaml_file.write_text(
        dedent("""\
        id: finding-community-plugin-evaluations
        evaluations:
          - name: test-generator
            verdict: INSTALL
            rationale: Auto pytest scaffolding, no overlap
          - name: srclight
            verdict: REJECT
            rationale: Overlaps with existing LSP
          - name: scenario-testing
            verdict: EXTRACT
            rationale: Good patterns but overlaps integration tests
          - name: mcp2cli
            verdict: INSTALL
            rationale: Core MCP access pattern
          - name: workflow-toolkit
            verdict: REJECT
            rationale: Session journaling not needed
          - name: superdevflow
            verdict: EXTRACT
            rationale: CLAUDE.md review useful but rest overlaps
    """)
    )
    result = validate_evaluations(
        evaluation_path=yaml_file,
        required_candidates=[
            "test-generator",
            "srclight",
            "scenario-testing",
            "mcp2cli",
            "workflow-toolkit",
            "superdevflow",
        ],
    )
    assert result.passed
    assert result.error_count == 0


def test_missing_candidate_is_error(tmp_path: Path) -> None:
    """Missing a required candidate produces an error."""
    yaml_file = tmp_path / "evaluations.yaml"
    yaml_file.write_text(
        dedent("""\
        id: finding-community-plugin-evaluations
        evaluations:
          - name: test-generator
            verdict: INSTALL
            rationale: Good fit
          - name: srclight
            verdict: REJECT
            rationale: Overlaps
    """)
    )
    result = validate_evaluations(
        evaluation_path=yaml_file,
        required_candidates=["test-generator", "srclight", "scenario-testing"],
    )
    assert not result.passed
    assert result.error_count == 1
    assert "scenario-testing" in result.findings[0].message


def test_missing_verdict_is_error(tmp_path: Path) -> None:
    """Candidate present but without verdict is an error."""
    yaml_file = tmp_path / "evaluations.yaml"
    yaml_file.write_text(
        dedent("""\
        id: finding-community-plugin-evaluations
        evaluations:
          - name: test-generator
            rationale: No verdict field
    """)
    )
    result = validate_evaluations(
        evaluation_path=yaml_file,
        required_candidates=["test-generator"],
    )
    assert not result.passed
    assert "missing verdict" in result.findings[0].message.lower()


def test_invalid_verdict_is_error(tmp_path: Path) -> None:
    """Verdict must be INSTALL, EXTRACT, or REJECT."""
    yaml_file = tmp_path / "evaluations.yaml"
    yaml_file.write_text(
        dedent("""\
        id: finding-community-plugin-evaluations
        evaluations:
          - name: test-generator
            verdict: SKIP
            rationale: Skipping
    """)
    )
    result = validate_evaluations(
        evaluation_path=yaml_file,
        required_candidates=["test-generator"],
    )
    assert not result.passed
    assert "invalid verdict" in result.findings[0].message.lower()


def test_missing_rationale_is_warning(tmp_path: Path) -> None:
    """Verdict without rationale is a warning."""
    yaml_file = tmp_path / "evaluations.yaml"
    yaml_file.write_text(
        dedent("""\
        id: finding-community-plugin-evaluations
        evaluations:
          - name: test-generator
            verdict: INSTALL
    """)
    )
    result = validate_evaluations(
        evaluation_path=yaml_file,
        required_candidates=["test-generator"],
    )
    assert result.passed  # warnings don't fail
    assert result.warning_count == 1


def test_file_not_found_is_error(tmp_path: Path) -> None:
    """Missing evaluation file is an error."""
    result = validate_evaluations(
        evaluation_path=tmp_path / "nonexistent.yaml",
        required_candidates=["test-generator"],
    )
    assert not result.passed
    assert "not found" in result.findings[0].message.lower()

"""Tests for mde.autonomous_review — 7-phase autonomous fix-review orchestrator.

Tests the orchestration layer that wires reviewd CLI invocations through
the consensus gate. All CLI calls are mocked (zero API keys).

Phase 0c of the autonomous-fix-review skill.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mde.autonomous_review import (
    Finding,
    ReviewPhase,
    ReviewPhaseError,
    ReviewPipeline,
    ReviewPipelineConfig,
    ReviewPipelineResult,
    parse_finding_input,
    run_multi_model_review,
)
from mde.consensus import (
    AutonomyMode,
    ConsensusDecision,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


def _make_review_json(
    *,
    approve: bool = True,
    findings: list[dict[str, Any]] | None = None,
    overview: str = "Looks good",
) -> str:
    """Build a fake reviewd JSON response wrapped in markdown code fence."""
    data = {
        "overview": overview,
        "findings": findings or [],
        "summary": "Review complete",
        "tests_passed": True,
        "approve": approve,
        "approve_reason": "LGTM" if approve else "Issues found",
    }
    return f"Here is my review:\n```json\n{json.dumps(data)}\n```\n"


def _make_reject_json(
    findings: list[dict[str, Any]] | None = None,
) -> str:
    """Build a fake reviewd rejection response."""
    default_findings = [
        {
            "severity": "critical",
            "category": "bug",
            "title": "Null pointer",
            "file": "src/main.py",
            "line": 42,
            "issue": "x could be None",
            "fix": "Add None check",
        },
    ]
    return _make_review_json(
        approve=False,
        findings=findings or default_findings,
        overview="Found issues",
    )


# ── Finding input parsing ─────────────────────────────────────────────────


class TestParseFindinginput:
    """Test parsing finding descriptions from CLI input."""

    def test_parse_string_description(self) -> None:
        finding = parse_finding_input("Fix the null pointer in src/main.py:42")
        assert finding.description == "Fix the null pointer in src/main.py:42"
        assert finding.source == "cli"

    def test_parse_yaml_file(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "finding.yaml"
        yaml_file.write_text(
            "title: Null pointer bug\n"
            "description: x could be None at src/main.py:42\n"
            "severity: critical\n"
            "file: src/main.py\n"
            "line: 42\n"
        )
        finding = parse_finding_input(str(yaml_file))
        assert finding.description == "x could be None at src/main.py:42"
        assert finding.source == str(yaml_file)

    def test_parse_nonexistent_file_treated_as_description(self) -> None:
        finding = parse_finding_input("/nonexistent/path.yaml")
        assert finding.description == "/nonexistent/path.yaml"
        assert finding.source == "cli"


# ── Pipeline config ───────────────────────────────────────────────────────


class TestReviewPipelineConfig:
    """Test pipeline configuration defaults and overrides."""

    def test_default_config(self) -> None:
        config = ReviewPipelineConfig()
        assert config.autonomy == AutonomyMode.SEMI_AUTONOMOUS
        assert config.models == ["claude", "codex", "gemini"]
        assert config.max_retries == 2
        assert config.run_quality_gate is True

    def test_custom_models(self) -> None:
        config = ReviewPipelineConfig(models=["claude", "codex"])
        assert len(config.models) == 2

    def test_supervised_mode(self) -> None:
        config = ReviewPipelineConfig(autonomy=AutonomyMode.SUPERVISED)
        assert config.autonomy == AutonomyMode.SUPERVISED


# ── Multi-model review invocation ─────────────────────────────────────────


class TestRunMultiModelReview:
    """Test parallel multi-model review invocation via reviewd."""

    @patch("mde.autonomous_review.invoke_cli")
    def test_invokes_all_three_models(self, mock_invoke: MagicMock) -> None:
        mock_invoke.return_value = _make_review_json()
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["claude", "codex", "gemini"],
        )
        assert len(reviews) == 3
        assert mock_invoke.call_count == 3
        assert all(r.approve for r in reviews)

    @patch("mde.autonomous_review.invoke_cli")
    def test_handles_mixed_approve_reject(self, mock_invoke: MagicMock) -> None:
        mock_invoke.side_effect = [
            _make_review_json(approve=True),
            _make_reject_json(),
            _make_review_json(approve=True),
        ]
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["claude", "codex", "gemini"],
        )
        assert reviews[0].approve is True
        assert reviews[1].approve is False
        assert reviews[2].approve is True

    @patch("mde.autonomous_review.invoke_cli")
    def test_cli_failure_produces_reject_review(self, mock_invoke: MagicMock) -> None:
        """If a CLI invocation fails, treat it as a rejection with error."""
        mock_invoke.side_effect = [
            _make_review_json(approve=True),
            RuntimeError("codex crashed"),
            _make_review_json(approve=True),
        ]
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["claude", "codex", "gemini"],
        )
        assert len(reviews) == 3
        # Failed CLI → synthetic rejection
        assert reviews[1].approve is False
        assert reviews[1].critical_count == 0

    @patch("mde.autonomous_review.invoke_cli")
    def test_malformed_json_produces_reject(self, mock_invoke: MagicMock) -> None:
        """If JSON extraction fails, treat as rejection."""
        mock_invoke.return_value = "This is not JSON at all, just prose."
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["claude"],
        )
        assert len(reviews) == 1
        assert reviews[0].approve is False


# ── Pipeline phases ───────────────────────────────────────────────────────


class TestReviewPhase:
    """Test phase enum values."""

    def test_all_seven_phases_exist(self) -> None:
        phases = list(ReviewPhase)
        assert len(phases) == 7
        assert ReviewPhase.RESEARCH in phases
        assert ReviewPhase.IMPLEMENT in phases
        assert ReviewPhase.REVIEW in phases
        assert ReviewPhase.CONSENSUS in phases
        assert ReviewPhase.DECISION in phases
        assert ReviewPhase.QUALITY_GATE in phases
        assert ReviewPhase.COMMIT in phases


# ── Full pipeline integration ─────────────────────────────────────────────


class TestReviewPipeline:
    """Test the full 7-phase pipeline with mocked CLI calls."""

    @patch("mde.autonomous_review.invoke_cli")
    def test_unanimous_approve_proceeds(self, mock_invoke: MagicMock) -> None:
        """All models approve → PROCEED, pipeline succeeds."""
        mock_invoke.return_value = _make_review_json(approve=True)
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(
                run_quality_gate=False,  # Skip quality gate in test
            ),
        )
        finding = Finding(description="Fix null pointer", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert result.consensus_decision == ConsensusDecision.PROCEED
        assert result.phase_reached == ReviewPhase.DECISION
        assert result.success is True

    @patch("mde.autonomous_review.invoke_cli")
    def test_unanimous_reject_with_criticals_escalates(self, mock_invoke: MagicMock) -> None:
        """All models reject with criticals → ESCALATE."""
        mock_invoke.return_value = _make_reject_json()
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(
                autonomy=AutonomyMode.SEMI_AUTONOMOUS,
                run_quality_gate=False,
            ),
        )
        finding = Finding(description="Fix bug", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert result.consensus_decision == ConsensusDecision.ESCALATE
        assert result.success is False
        assert result.needs_human is True

    @patch("mde.autonomous_review.invoke_cli")
    def test_supervised_mode_escalates_on_warn(self, mock_invoke: MagicMock) -> None:
        """SUPERVISED + PROCEED_WARN → ESCALATE (human must approve)."""
        # 3 of 4 approve (75%) → PROCEED_WARN, supervised → ESCALATE
        mock_invoke.side_effect = [
            _make_review_json(approve=True),
            _make_review_json(approve=True),
            _make_review_json(approve=True),
            _make_review_json(approve=False),
        ]
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(
                autonomy=AutonomyMode.SUPERVISED,
                models=["claude", "codex", "gemini", "extra"],
                run_quality_gate=False,
            ),
        )
        finding = Finding(description="Fix style", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert result.consensus_decision == ConsensusDecision.ESCALATE
        assert result.needs_human is True

    @patch("mde.autonomous_review.invoke_cli")
    def test_pipeline_records_all_reviews(self, mock_invoke: MagicMock) -> None:
        """Pipeline result includes all model reviews."""
        mock_invoke.return_value = _make_review_json(approve=True)
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(run_quality_gate=False),
        )
        finding = Finding(description="Fix something", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert len(result.reviews) == 3
        model_names = [r.model for r in result.reviews]
        assert "claude" in model_names
        assert "codex" in model_names
        assert "gemini" in model_names

    @patch("mde.autonomous_review.invoke_cli")
    def test_integrity_violations_recorded(self, mock_invoke: MagicMock) -> None:
        """Debate integrity violations are recorded in the result."""
        # Approval with no findings → ANTI_RUBBER_STAMP
        mock_invoke.return_value = _make_review_json(approve=True)
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(run_quality_gate=False),
        )
        finding = Finding(description="Fix something", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        # All three reviews have no findings → rubber stamp violations
        assert len(result.integrity_violations) > 0


# ── Result model ──────────────────────────────────────────────────────────


class TestReviewPipelineResult:
    """Test ReviewPipelineResult construction."""

    def test_successful_result(self) -> None:
        result = ReviewPipelineResult(
            finding=Finding(description="test", source="cli"),
            reviews=[],
            consensus_decision=ConsensusDecision.PROCEED,
            phase_reached=ReviewPhase.DECISION,
            success=True,
            needs_human=False,
            integrity_violations={},
        )
        assert result.success is True
        assert result.needs_human is False

    def test_escalated_result(self) -> None:
        result = ReviewPipelineResult(
            finding=Finding(description="test", source="cli"),
            reviews=[],
            consensus_decision=ConsensusDecision.ESCALATE,
            phase_reached=ReviewPhase.DECISION,
            success=False,
            needs_human=True,
            integrity_violations={},
        )
        assert result.needs_human is True


# ── Error handling ────────────────────────────────────────────────────────


class TestReviewPhaseError:
    """Test ReviewPhaseError exception."""

    def test_captures_phase_and_message(self) -> None:
        err = ReviewPhaseError(ReviewPhase.REVIEW, "CLI timed out")
        assert err.phase == ReviewPhase.REVIEW
        assert "CLI timed out" in str(err)

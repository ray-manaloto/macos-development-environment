"""Tests for mde.autonomous_review — 7-phase autonomous fix-review orchestrator.

Tests the orchestration layer that wires debate/invoke.py invocations through
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
    _extract_json,
    parse_finding_input,
    run_multi_model_review,
    run_multi_model_review_parallel,
)
from mde.consensus import (
    AutonomyMode,
    ConsensusDecision,
)
from mde.debate.invoke import InvocationResult

# ── Fixtures ──────────────────────────────────────────────────────────────


def _make_review_json(
    *,
    approve: bool = True,
    findings: list[dict[str, Any]] | None = None,
    overview: str = "Looks good",
) -> str:
    """Build a fake review JSON response wrapped in markdown code fence."""
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
    """Build a fake rejection response."""
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


def _make_invocation_result(
    model: str = "claude",
    response: str = "",
    *,
    success: bool = True,
    error: str | None = None,
) -> InvocationResult:
    """Build a fake InvocationResult from debate/invoke.py."""
    return InvocationResult(
        model=model,
        prompt="test prompt",
        response=response,
        success=success,
        duration_seconds=1.0,
        error=error,
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
        assert config.models == ["codex", "gemini"]
        assert config.max_retries == 2
        assert config.run_quality_gate is True

    def test_custom_models(self) -> None:
        config = ReviewPipelineConfig(models=["claude", "codex"])
        assert len(config.models) == 2

    def test_supervised_mode(self) -> None:
        config = ReviewPipelineConfig(autonomy=AutonomyMode.SUPERVISED)
        assert config.autonomy == AutonomyMode.SUPERVISED


# ── JSON extraction ──────────────────────────────────────────────────────


class TestExtractJson:
    """Test _extract_json helper for parsing model responses."""

    def test_extracts_from_json_fence(self) -> None:
        text = 'Here is my review:\n```json\n{"approve": true}\n```\n'
        result = _extract_json(text)
        assert result == {"approve": True}

    def test_extracts_from_bare_fence(self) -> None:
        text = '```\n{"approve": false}\n```'
        result = _extract_json(text)
        assert result == {"approve": False}

    def test_extracts_raw_json(self) -> None:
        text = '{"approve": true, "findings": []}'
        result = _extract_json(text)
        assert result == {"approve": True, "findings": []}

    def test_raises_on_invalid_json(self) -> None:
        import pytest

        with pytest.raises((json.JSONDecodeError, ValueError)):
            _extract_json("This is not JSON at all, just prose.")


# ── Multi-model review invocation ─────────────────────────────────────────


class TestRunMultiModelReview:
    """Test multi-model review invocation via debate/invoke.py."""

    @patch("mde.autonomous_review.invoke_model")
    def test_invokes_all_three_models(self, mock_invoke: MagicMock) -> None:
        mock_invoke.return_value = _make_invocation_result(
            response=_make_review_json(),
        )
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["codex", "gemini"],
        )
        assert len(reviews) == 2
        assert mock_invoke.call_count == 2
        assert all(r.approve for r in reviews)

    @patch("mde.autonomous_review.invoke_model")
    def test_handles_mixed_approve_reject(self, mock_invoke: MagicMock) -> None:
        mock_invoke.side_effect = [
            _make_invocation_result(model="codex", response=_make_reject_json()),
            _make_invocation_result(model="gemini", response=_make_review_json(approve=True)),
        ]
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["codex", "gemini"],
        )
        assert reviews[0].approve is False
        assert reviews[1].approve is True

    @patch("mde.autonomous_review.invoke_model")
    def test_cli_failure_produces_reject_review(self, mock_invoke: MagicMock) -> None:
        """If a CLI invocation fails, treat it as a rejection with error."""
        mock_invoke.side_effect = [
            _make_invocation_result(
                model="codex", response="", success=False, error="codex crashed"
            ),
            _make_invocation_result(model="gemini", response=_make_review_json(approve=True)),
        ]
        reviews = run_multi_model_review(
            prompt="Review this diff",
            cwd="/tmp/test",
            models=["codex", "gemini"],
        )
        assert len(reviews) == 2
        # Failed CLI → synthetic rejection
        assert reviews[0].approve is False
        assert reviews[0].critical_count == 0

    @patch("mde.autonomous_review.invoke_model")
    def test_malformed_json_produces_reject(self, mock_invoke: MagicMock) -> None:
        """If JSON extraction fails, treat as rejection."""
        mock_invoke.return_value = _make_invocation_result(
            response="This is not JSON at all, just prose.",
        )
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

    @patch("mde.autonomous_review.invoke_model")
    def test_unanimous_approve_proceeds(self, mock_invoke: MagicMock) -> None:
        """All models approve → PROCEED, pipeline succeeds."""
        mock_invoke.return_value = _make_invocation_result(
            response=_make_review_json(approve=True),
        )
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

    @patch("mde.autonomous_review.invoke_model")
    def test_unanimous_reject_with_criticals_escalates(self, mock_invoke: MagicMock) -> None:
        """All models reject with criticals → ESCALATE."""
        mock_invoke.return_value = _make_invocation_result(
            response=_make_reject_json(),
        )
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

    @patch("mde.autonomous_review.invoke_model")
    def test_supervised_mode_escalates_on_warn(self, mock_invoke: MagicMock) -> None:
        """SUPERVISED + PROCEED_WARN → ESCALATE (human must approve)."""
        # 2 of 3 approve (67%) → PROCEED_WARN, supervised → ESCALATE
        mock_invoke.side_effect = [
            _make_invocation_result(model="codex", response=_make_review_json(approve=True)),
            _make_invocation_result(model="gemini", response=_make_review_json(approve=True)),
            _make_invocation_result(model="extra", response=_make_review_json(approve=False)),
        ]
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(
                autonomy=AutonomyMode.SUPERVISED,
                models=["codex", "gemini", "extra"],
                run_quality_gate=False,
            ),
        )
        finding = Finding(description="Fix style", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert result.consensus_decision == ConsensusDecision.ESCALATE
        assert result.needs_human is True

    @patch("mde.autonomous_review.invoke_model")
    def test_pipeline_records_all_reviews(self, mock_invoke: MagicMock) -> None:
        """Pipeline result includes all model reviews."""
        mock_invoke.return_value = _make_invocation_result(
            response=_make_review_json(approve=True),
        )
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(run_quality_gate=False),
        )
        finding = Finding(description="Fix something", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        assert len(result.reviews) == 2
        model_names = [r.model for r in result.reviews]
        assert "codex" in model_names
        assert "gemini" in model_names

    @patch("mde.autonomous_review.invoke_model")
    def test_integrity_violations_recorded(self, mock_invoke: MagicMock) -> None:
        """Debate integrity violations are recorded in the result."""
        # Approval with no findings → ANTI_RUBBER_STAMP
        mock_invoke.return_value = _make_invocation_result(
            response=_make_review_json(approve=True),
        )
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(run_quality_gate=False),
        )
        finding = Finding(description="Fix something", source="cli")
        result = pipeline.run_review_phase(finding, cwd="/tmp/test")

        # Both reviews have no findings → rubber stamp violations
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


# ── Parallel multi-model review ──────────────────────────────────────────


class TestRunMultiModelReviewParallel:
    """Test async parallel multi-model review invocation."""

    @patch("mde.autonomous_review.invoke_all_parallel")
    def test_parallel_invokes_all_models(self, mock_parallel: MagicMock) -> None:
        import asyncio

        mock_parallel.return_value = [
            _make_invocation_result("codex", _make_review_json(approve=True)),
            _make_invocation_result("gemini", _make_review_json(approve=True)),
        ]
        reviews = asyncio.run(
            run_multi_model_review_parallel("Review this", models=["codex", "gemini"])
        )
        assert len(reviews) == 2
        assert all(r.approve for r in reviews)
        mock_parallel.assert_called_once()

    @patch("mde.autonomous_review.invoke_all_parallel")
    def test_parallel_handles_cli_failure(self, mock_parallel: MagicMock) -> None:
        import asyncio

        mock_parallel.return_value = [
            _make_invocation_result("codex", "", success=False, error="timeout"),
            _make_invocation_result("gemini", _make_review_json(approve=True)),
        ]
        reviews = asyncio.run(
            run_multi_model_review_parallel("Review this", models=["codex", "gemini"])
        )
        assert len(reviews) == 2
        assert reviews[0].approve is False
        assert reviews[1].approve is True

    @patch("mde.autonomous_review.invoke_all_parallel")
    def test_parallel_handles_json_parse_failure(self, mock_parallel: MagicMock) -> None:
        import asyncio

        mock_parallel.return_value = [
            _make_invocation_result("codex", "not json at all"),
        ]
        reviews = asyncio.run(run_multi_model_review_parallel("Review this", models=["codex"]))
        assert len(reviews) == 1
        assert reviews[0].approve is False
        assert "Parse error" in reviews[0].approve_reason


class TestReviewPipelineParallel:
    """Test pipeline with parallel review phase."""

    @patch("mde.autonomous_review.invoke_all_parallel")
    def test_parallel_pipeline_unanimous_approve(self, mock_parallel: MagicMock) -> None:
        import asyncio

        mock_parallel.return_value = [
            _make_invocation_result("codex", _make_review_json(approve=True)),
            _make_invocation_result("gemini", _make_review_json(approve=True)),
        ]
        pipeline = ReviewPipeline(
            config=ReviewPipelineConfig(
                models=["codex", "gemini"],
                run_quality_gate=False,
            ),
        )
        finding = Finding(description="Fix null pointer", source="cli")
        result = asyncio.run(pipeline.run_review_phase_parallel(finding))

        assert result.consensus_decision == ConsensusDecision.PROCEED
        assert result.success is True

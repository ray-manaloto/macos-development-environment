"""Autonomous fix-review orchestrator — 7-phase pipeline.

Wires debate/invoke.py CLI invocations through the consensus gate to achieve
zero-human-attention code review on the happy path.

Phases:
    1. RESEARCH   — gather context (docs, code, community)
    2. IMPLEMENT  — dispatch coder subagent in worktree with TDD
    3. REVIEW     — run multi-model review via debate/invoke.py
    4. CONSENSUS  — evaluate consensus across model reviews
    5. DECISION   — apply autonomy mode to consensus result
    6. QUALITY_GATE — run uv run mde-py quality
    7. COMMIT     — commit on feature branch (or escalate)

All LLM calls go through subscription CLIs (zero API keys).

References:
    - Design doc: ~/.gstack/projects/ray-manaloto-macos-development-environment/
      rmanaloto-main-design-20260325-171540.md
    - Phase 0b: src/mde/consensus.py (consensus gate + debate integrity)
    - Phase 0b: src/mde/debate/invoke.py (multi-model CLI invocation backend)
"""

from __future__ import annotations

import enum
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from mde.consensus import (
    AutonomyMode,
    ConsensusDecision,
    ConsensusGate,
    DebateIntegrityRule,
    ModelReview,
    check_debate_integrity,
    evaluate_consensus,
)
from mde.debate.invoke import InvocationResult, invoke_all_parallel, invoke_model
from mde.log import logger

# ── Enums ─────────────────────────────────────────────────────────────────


class ReviewPhase(enum.Enum):
    """The 7 phases of the autonomous review pipeline."""

    RESEARCH = "research"
    IMPLEMENT = "implement"
    REVIEW = "review"
    CONSENSUS = "consensus"
    DECISION = "decision"
    QUALITY_GATE = "quality_gate"
    COMMIT = "commit"


# ── Models ────────────────────────────────────────────────────────────────


class Finding(BaseModel):
    """A finding to be reviewed — either from a YAML file or CLI string."""

    description: str
    source: str  # "cli" or file path


class ReviewPipelineConfig(BaseModel):
    """Configuration for the review pipeline."""

    autonomy: AutonomyMode = AutonomyMode.SEMI_AUTONOMOUS
    models: list[str] = ["claude", "codex", "gemini"]
    max_retries: int = 2
    run_quality_gate: bool = True
    timeout: int = 600


class ReviewPipelineResult(BaseModel):
    """Result of running the review pipeline."""

    finding: Finding
    reviews: list[ModelReview]
    consensus_decision: ConsensusDecision
    phase_reached: ReviewPhase
    success: bool
    needs_human: bool
    integrity_violations: dict[str, list[DebateIntegrityRule]]
    error: str | None = None


# ── Exceptions ────────────────────────────────────────────────────────────


class ReviewPhaseError(Exception):
    """Error during a specific phase of the review pipeline."""

    def __init__(self, phase: ReviewPhase, message: str) -> None:
        """Initialize with the phase that failed and an error message."""
        self.phase = phase
        super().__init__(f"Phase {phase.value}: {message}")


# ── Finding input parsing ─────────────────────────────────────────────────


def parse_finding_input(input_str: str) -> Finding:
    """Parse a finding from a CLI argument — file path or description string.

    If the input is a path to an existing YAML file, parse it.
    Otherwise treat the string as a plain-text description.

    Args:
        input_str: File path or description string.

    Returns:
        Finding with description and source.
    """
    path = Path(input_str)
    if path.exists() and path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(path.read_text())
        return Finding(
            description=data.get("description", data.get("title", input_str)),
            source=str(path),
        )
    return Finding(description=input_str, source="cli")


# ── JSON extraction ──────────────────────────────────────────────────────


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from text that may contain ```json fences.

    Args:
        text: Raw model response text.

    Returns:
        Parsed JSON dict.

    Raises:
        json.JSONDecodeError: If no valid JSON found.
        ValueError: If no valid JSON found.
    """
    # Try to find JSON in code fence
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try raw JSON parse
    return json.loads(text)


# ── Multi-model review ────────────────────────────────────────────────────


def _invoke_single_model(
    model: str,
    prompt: str,
    timeout: int = 600,
) -> ModelReview:
    """Invoke a single model via debate/invoke.py and return a ModelReview.

    On CLI failure or JSON parse failure, returns a synthetic rejection
    so the consensus gate can still operate on partial results.

    Args:
        model: Model name (claude, codex, gemini).
        prompt: The review prompt.
        timeout: CLI timeout in seconds.

    Returns:
        ModelReview from the model's response.
    """
    result: InvocationResult = invoke_model(model, prompt, timeout=timeout)

    if not result.success:
        logger.bind(model=model).warning(f"CLI invocation failed: {result.error}")
        return ModelReview(
            model=model,
            approve=False,
            approve_reason=f"CLI error: {result.error}",
            findings=[],
            critical_count=0,
            suggestion_count=0,
        )

    try:
        data = _extract_json(result.response)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        logger.bind(model=model).warning(f"JSON parse failed: {exc}")
        return ModelReview(
            model=model,
            approve=False,
            approve_reason=f"Parse error: {exc}",
            findings=[],
            critical_count=0,
            suggestion_count=0,
        )

    # Convert parsed JSON → consensus ModelReview
    findings_raw: list[dict[str, Any]] = data.get("findings", [])
    critical_count = sum(1 for f in findings_raw if f.get("severity") == "critical")
    suggestion_count = sum(1 for f in findings_raw if f.get("severity") == "suggestion")

    return ModelReview(
        model=model,
        approve=bool(data.get("approve", False)),
        approve_reason=data.get("approve_reason", ""),
        findings=findings_raw,
        critical_count=critical_count,
        suggestion_count=suggestion_count,
    )


def run_multi_model_review(
    prompt: str,
    cwd: str,  # noqa: ARG001 — kept for API compatibility with callers
    models: list[str] | None = None,
    timeout: int = 600,
) -> list[ModelReview]:
    """Run review across multiple models sequentially.

    Each model is invoked via debate/invoke.py's invoke_model(). Failures
    are captured as synthetic rejections so consensus can still operate.

    Args:
        prompt: The review prompt.
        cwd: Working directory for the review (reserved for future use).
        models: List of model names. Defaults to claude, codex, gemini.
        timeout: CLI timeout in seconds per model.

    Returns:
        List of ModelReview results (one per model).
    """
    if models is None:
        models = ["claude", "codex", "gemini"]

    reviews: list[ModelReview] = []
    for model in models:
        review = _invoke_single_model(model, prompt, timeout)
        reviews.append(review)

    return reviews


async def run_multi_model_review_parallel(
    prompt: str,
    models: list[str] | None = None,
    timeout_seconds: int = 600,
) -> list[ModelReview]:
    """Run review across multiple models concurrently.

    Uses invoke_all_parallel() to run codex+gemini in parallel threads.
    Each InvocationResult is converted to a ModelReview for the consensus gate.

    Args:
        prompt: The review prompt.
        models: List of model names. Defaults to codex, gemini.
        timeout_seconds: CLI timeout in seconds per model.

    Returns:
        List of ModelReview results (one per model).
    """
    if models is None:
        models = ["codex", "gemini"]

    results = await invoke_all_parallel(prompt, models=models, timeout_seconds=timeout_seconds)

    reviews: list[ModelReview] = []
    for result in results:
        if not result.success:
            logger.bind(model=result.model).warning(f"CLI invocation failed: {result.error}")
            reviews.append(
                ModelReview(
                    model=result.model,
                    approve=False,
                    approve_reason=f"CLI error: {result.error}",
                    findings=[],
                    critical_count=0,
                    suggestion_count=0,
                )
            )
            continue

        try:
            data = _extract_json(result.response)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.bind(model=result.model).warning(f"JSON parse failed: {exc}")
            reviews.append(
                ModelReview(
                    model=result.model,
                    approve=False,
                    approve_reason=f"Parse error: {exc}",
                    findings=[],
                    critical_count=0,
                    suggestion_count=0,
                )
            )
            continue

        findings_raw: list[dict[str, Any]] = data.get("findings", [])
        critical_count = sum(1 for f in findings_raw if f.get("severity") == "critical")
        suggestion_count = sum(1 for f in findings_raw if f.get("severity") == "suggestion")

        reviews.append(
            ModelReview(
                model=result.model,
                approve=bool(data.get("approve", False)),
                approve_reason=data.get("approve_reason", ""),
                findings=findings_raw,
                critical_count=critical_count,
                suggestion_count=suggestion_count,
            )
        )

    return reviews


# ── Pipeline orchestrator ─────────────────────────────────────────────────


class ReviewPipeline:
    """The 7-phase autonomous fix-review pipeline.

    Phases 1-2 (research, implement) are handled by the calling skill/agent.
    This class handles phases 3-7 (review, consensus, decision, quality, commit).
    """

    def __init__(self, config: ReviewPipelineConfig | None = None) -> None:
        """Initialize the pipeline with optional configuration."""
        self.config = config or ReviewPipelineConfig()
        self.gate = ConsensusGate(
            autonomy=self.config.autonomy,
            max_retries=self.config.max_retries,
        )

    def run_review_phase(
        self,
        finding: Finding,
        cwd: str,
    ) -> ReviewPipelineResult:
        """Execute phases 3-5 of the pipeline: review → consensus → decision.

        Args:
            finding: The finding being reviewed.
            cwd: Working directory containing the code to review.

        Returns:
            ReviewPipelineResult with consensus decision and metadata.
        """
        # Phase 3: REVIEW — invoke all models (sequential)
        prompt = self._build_review_prompt(finding)
        reviews = run_multi_model_review(
            prompt=prompt,
            cwd=cwd,
            models=self.config.models,
            timeout=self.config.timeout,
        )
        return self._evaluate_reviews(finding, reviews)

    async def run_review_phase_parallel(
        self,
        finding: Finding,
    ) -> ReviewPipelineResult:
        """Execute phases 3-5 with parallel model invocation.

        Same as run_review_phase but uses invoke_all_parallel() to run
        codex+gemini concurrently instead of sequentially.

        Args:
            finding: The finding being reviewed.

        Returns:
            ReviewPipelineResult with consensus decision and metadata.
        """
        prompt = self._build_review_prompt(finding)
        reviews = await run_multi_model_review_parallel(
            prompt=prompt,
            models=self.config.models,
            timeout_seconds=self.config.timeout,
        )
        return self._evaluate_reviews(finding, reviews)

    def _evaluate_reviews(
        self,
        finding: Finding,
        reviews: list[ModelReview],
    ) -> ReviewPipelineResult:
        """Evaluate reviews through integrity check, consensus, and autonomy gate.

        Shared by both sync and async review phase methods.
        """
        # Phase 3.5: Check debate integrity
        integrity_violations: dict[str, list[DebateIntegrityRule]] = {}
        for review in reviews:
            violations = check_debate_integrity(review)
            if violations:
                integrity_violations[review.model] = violations

        # Phase 4: CONSENSUS — evaluate agreement
        consensus = evaluate_consensus(reviews)

        # Phase 5: DECISION — apply autonomy mode
        final_decision = self.gate.apply_autonomy(consensus.decision)

        # Determine outcome
        success = final_decision == ConsensusDecision.PROCEED
        needs_human = final_decision in (
            ConsensusDecision.ESCALATE,
            ConsensusDecision.ABORT,
        )

        return ReviewPipelineResult(
            finding=finding,
            reviews=reviews,
            consensus_decision=final_decision,
            phase_reached=ReviewPhase.DECISION,
            success=success,
            needs_human=needs_human,
            integrity_violations=integrity_violations,
        )

    def _build_review_prompt(self, finding: Finding) -> str:
        """Build the review prompt from a finding.

        Args:
            finding: The finding to review.

        Returns:
            Prompt string for the reviewers.
        """
        return (
            f"Review the following code change that addresses this finding:\n\n"
            f"Finding: {finding.description}\n"
            f"Source: {finding.source}\n\n"
            f"Please review the current diff in this directory. "
            f"Output your review as JSON with fields: overview, findings, "
            f"summary, tests_passed, approve, approve_reason."
        )


# ── CLI entry point ───────────────────────────────────────────────────────


def cli_review(args: Any) -> int:
    """CLI handler for `mde-py review <finding>`.

    Args:
        args: Parsed argparse namespace with 'finding' attribute.

    Returns:
        Exit code (0 = success/proceed, 1 = escalate/abort, 2 = error).
    """
    finding_input: str = args.finding
    finding = parse_finding_input(finding_input)
    logger.bind(finding=finding.description, source=finding.source).info("review_start")

    autonomy_str = getattr(args, "autonomy", None)
    autonomy = AutonomyMode(autonomy_str) if autonomy_str else AutonomyMode.SEMI_AUTONOMOUS
    config = ReviewPipelineConfig(
        autonomy=autonomy,
        run_quality_gate=not getattr(args, "skip_quality", False),
    )

    pipeline = ReviewPipeline(config=config)

    try:
        import asyncio

        result = asyncio.run(pipeline.run_review_phase_parallel(finding))
    except ReviewPhaseError as exc:
        logger.error(f"Pipeline failed: {exc}")
        sys.stderr.write(f"ERROR: {exc}\n")
        return 2

    # Output result summary
    _print_result(result)

    if result.success:
        return 0
    return 1


def _print_result(result: ReviewPipelineResult) -> None:
    """Write a human-readable summary of the pipeline result to stderr."""
    w = sys.stderr.write
    sep = "=" * 60
    w(f"\n{sep}\n")
    w(f"Finding: {result.finding.description}\n")
    w(f"Decision: {result.consensus_decision.value}\n")
    w(f"Phase reached: {result.phase_reached.value}\n")
    w(f"Reviews: {len(result.reviews)}\n")

    for review in result.reviews:
        status = "APPROVE" if review.approve else "REJECT"
        w(f"  {review.model}: {status} — {review.approve_reason}\n")

    if result.integrity_violations:
        w("\nIntegrity violations:\n")
        for model, violations in result.integrity_violations.items():
            rules = ", ".join(v.value for v in violations)
            w(f"  {model}: {rules}\n")

    if result.needs_human:
        w("\n** HUMAN REVIEW REQUIRED **\n")
    elif result.success:
        w("\n** PROCEED — all models agree **\n")

    w(f"{sep}\n\n")

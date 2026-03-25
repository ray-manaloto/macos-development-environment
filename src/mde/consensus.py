"""Multi-model consensus gate and debate integrity checking.

Ported from claude-octopus v9.13.0 (MIT license):
- quality.sh: evaluate_quality_branch() — 75% threshold consensus gate
- debate.sh: grapple_debate() — adversarial debate integrity rules

This module provides the decision logic layer. It does NOT invoke CLIs
or run subprocesses — that's the orchestrator's job. This module accepts
structured review results and returns consensus decisions.

References:
    - Source: ~/.claude/plugins/cache/nyldn-plugins/octo/9.13.0/scripts/lib/
    - Design doc: ~/.gstack/projects/ray-manaloto-macos-development-environment/
      rmanaloto-main-design-20260325-171540.md
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, field_validator

# ── Enums ────────────────────────────────────────────────────────────────


class ReviewSeverity(enum.Enum):
    """Severity levels matching reviewd's Severity enum.

    Each level has a numeric weight for aggregation.
    """

    CRITICAL = "critical"
    SUGGESTION = "suggestion"
    NITPICK = "nitpick"
    GOOD = "good"

    @property
    def weight(self) -> int:
        """Numeric weight for severity comparison and aggregation."""
        return _SEVERITY_WEIGHTS[self]


_SEVERITY_WEIGHTS: dict[ReviewSeverity, int] = {
    ReviewSeverity.CRITICAL: 100,
    ReviewSeverity.SUGGESTION: 50,
    ReviewSeverity.NITPICK: 10,
    ReviewSeverity.GOOD: 0,
}


class ConsensusDecision(enum.Enum):
    """Exit decisions from the consensus gate.

    Ported from claude-octopus quality.sh evaluate_quality_branch().
    """

    PROCEED = "proceed"
    PROCEED_WARN = "proceed_warn"
    RETRY = "retry"
    ESCALATE = "escalate"
    ABORT = "abort"


class AutonomyMode(enum.Enum):
    """Autonomy modes controlling how warnings/failures are handled.

    Ported from claude-octopus quality.sh AUTONOMY_MODE.
    """

    SUPERVISED = "supervised"
    SEMI_AUTONOMOUS = "semi-autonomous"
    AUTONOMOUS = "autonomous"


class DebateIntegrityRule(enum.Enum):
    """Debate integrity rules from claude-octopus debate.sh.

    These prevent low-quality reviews from polluting consensus.
    """

    ANTI_CONTRARIAN = "anti-contrarian"
    ANTI_RUBBER_STAMP = "anti-rubber-stamp"
    EVIDENCE_BASED = "evidence-based"
    PROPORTIONAL = "proportional"


# ── Models ───────────────────────────────────────────────────────────────


class ModelReview(BaseModel):
    """A single model's review output.

    Wraps reviewd's ReviewResult with consensus-relevant metadata.
    """

    model: str
    approve: bool
    approve_reason: str
    findings: list[dict[str, Any]]
    critical_count: int
    suggestion_count: int

    @field_validator("model")
    @classmethod
    def model_must_be_nonempty(cls, v: str) -> str:
        """Model name must not be empty."""
        if not v.strip():
            msg = "model must be a non-empty string"
            raise ValueError(msg)
        return v


class ConsensusResult(BaseModel):
    """Result of evaluating consensus across multiple model reviews."""

    decision: ConsensusDecision
    agreement_pct: float
    approve_count: int
    reject_count: int
    total_reviews: int
    has_critical_findings: bool
    reviews: list[ModelReview]


class DebateRound(BaseModel):
    """A single round in a multi-round debate."""

    round_number: int
    reviews: list[ModelReview]
    integrity_violations: dict[str, list[DebateIntegrityRule]]


class DebateResult(BaseModel):
    """Full result of a multi-round adversarial debate."""

    rounds: list[DebateRound]
    final_decision: ConsensusDecision
    agreement_pct: float


# ── Consensus gate ───────────────────────────────────────────────────────

# Default thresholds from claude-octopus quality.sh
DEFAULT_QUALITY_THRESHOLD: float = 75.0
DEFAULT_PROCEED_THRESHOLD: float = 90.0


def evaluate_consensus(
    reviews: list[ModelReview],
    *,
    threshold_pct: float = DEFAULT_QUALITY_THRESHOLD,
    proceed_threshold_pct: float = DEFAULT_PROCEED_THRESHOLD,
) -> ConsensusResult:
    """Evaluate consensus across multiple model reviews.

    Ported from claude-octopus quality.sh evaluate_quality_branch().

    Decision logic:
        - >= proceed_threshold (90%) approval AND no criticals → PROCEED
        - >= threshold (75%) approval AND no criticals → PROCEED_WARN
        - Any model found critical findings → ESCALATE
        - < threshold approval → ESCALATE
        - No reviews → ABORT

    Args:
        reviews: List of model review results.
        threshold_pct: Minimum approval percentage to pass (default 75%).
        proceed_threshold_pct: Approval percentage for clean proceed (default 90%).

    Returns:
        ConsensusResult with decision and metadata.
    """
    if not reviews:
        return ConsensusResult(
            decision=ConsensusDecision.ABORT,
            agreement_pct=0.0,
            approve_count=0,
            reject_count=0,
            total_reviews=0,
            has_critical_findings=False,
            reviews=[],
        )

    approve_count = sum(1 for r in reviews if r.approve)
    reject_count = len(reviews) - approve_count
    total = len(reviews)
    has_criticals = any(r.critical_count > 0 for r in reviews)

    # Agreement percentage is based on the majority position
    majority_count = max(approve_count, reject_count)
    agreement_pct = (majority_count / total) * 100.0

    # Determine decision
    approval_pct = (approve_count / total) * 100.0

    if has_criticals:
        decision = ConsensusDecision.ESCALATE
    elif approval_pct >= proceed_threshold_pct:
        decision = ConsensusDecision.PROCEED
    elif approval_pct >= threshold_pct:
        decision = ConsensusDecision.PROCEED_WARN
    elif approve_count == 0:
        decision = ConsensusDecision.ABORT
    else:
        decision = ConsensusDecision.ESCALATE

    return ConsensusResult(
        decision=decision,
        agreement_pct=agreement_pct,
        approve_count=approve_count,
        reject_count=reject_count,
        total_reviews=total,
        has_critical_findings=has_criticals,
        reviews=reviews,
    )


# ── Autonomy mode application ───────────────────────────────────────────


class ConsensusGate(BaseModel):
    """Consensus gate with configurable autonomy mode.

    Ported from claude-octopus quality.sh autonomy modes.
    """

    autonomy: AutonomyMode = AutonomyMode.SEMI_AUTONOMOUS
    threshold_pct: float = DEFAULT_QUALITY_THRESHOLD
    max_retries: int = 3

    def apply_autonomy(self, decision: ConsensusDecision) -> ConsensusDecision:
        """Apply autonomy mode to modify a consensus decision.

        - PROCEED and ABORT are always final (no override).
        - PROCEED_WARN behavior depends on autonomy mode:
          - SUPERVISED → ESCALATE (human must approve)
          - SEMI_AUTONOMOUS → RETRY (auto-retry)
          - AUTONOMOUS → PROCEED (just go)
        - RETRY and ESCALATE pass through unchanged.

        Args:
            decision: The raw consensus decision.

        Returns:
            Modified decision based on autonomy mode.
        """
        # Terminal decisions are never overridden
        if decision in (ConsensusDecision.PROCEED, ConsensusDecision.ABORT):
            return decision

        # PROCEED_WARN is the only decision affected by autonomy mode
        if decision == ConsensusDecision.PROCEED_WARN:
            if self.autonomy == AutonomyMode.SUPERVISED:
                return ConsensusDecision.ESCALATE
            if self.autonomy == AutonomyMode.SEMI_AUTONOMOUS:
                return ConsensusDecision.RETRY
            if self.autonomy == AutonomyMode.AUTONOMOUS:
                return ConsensusDecision.PROCEED

        return decision


# ── Debate integrity checking ────────────────────────────────────────────


def check_debate_integrity(review: ModelReview) -> list[DebateIntegrityRule]:
    """Check a model review for debate integrity violations.

    Ported from claude-octopus debate.sh integrity rules:
    - ANTI-CONTRARIAN: Rejection without specific counter-evidence
    - ANTI-RUBBER-STAMP: Approval without reviewing any code
    - EVIDENCE-BASED: Findings without file:line references

    Args:
        review: A single model's review to check.

    Returns:
        List of violated integrity rules (empty = clean).
    """
    violations: list[DebateIntegrityRule] = []

    # ANTI-CONTRARIAN: Disagreement without specific findings is contrarian
    if not review.approve and not review.findings:
        violations.append(DebateIntegrityRule.ANTI_CONTRARIAN)

    # ANTI-RUBBER-STAMP: Approval with no findings means reviewer didn't engage
    if review.approve and not review.findings:
        violations.append(DebateIntegrityRule.ANTI_RUBBER_STAMP)

    # EVIDENCE-BASED: Every finding must have file references
    if review.findings:
        has_ungrounded = any(
            not finding.get("file") and not finding.get("line") for finding in review.findings
        )
        if has_ungrounded:
            violations.append(DebateIntegrityRule.EVIDENCE_BASED)

    return violations

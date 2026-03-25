"""Tests for mde.consensus — multi-model consensus gate and debate integrity.

Ported from claude-octopus quality.sh (75% threshold) and debate.sh
(ANTI-CONTRARIAN, ANTI-RUBBER-STAMP, EVIDENCE-BASED integrity rules).
"""

from __future__ import annotations

import pytest

from mde.consensus import (
    AutonomyMode,
    ConsensusDecision,
    ConsensusGate,
    DebateIntegrityRule,
    DebateResult,
    DebateRound,
    ModelReview,
    ReviewSeverity,
    check_debate_integrity,
    evaluate_consensus,
)

# ── Pydantic model construction ──────────────────────────────────────────


class TestModelReview:
    """Test ModelReview construction and validation."""

    def test_create_approving_review(self) -> None:
        review = ModelReview(
            model="claude",
            approve=True,
            approve_reason="Code looks good",
            findings=[],
            critical_count=0,
            suggestion_count=0,
        )
        assert review.model == "claude"
        assert review.approve is True
        assert review.critical_count == 0

    def test_create_rejecting_review_with_findings(self) -> None:
        review = ModelReview(
            model="codex",
            approve=False,
            approve_reason="Critical bug found",
            findings=[
                {"severity": "critical", "title": "Null deref", "file": "main.py", "line": 10},
            ],
            critical_count=1,
            suggestion_count=0,
        )
        assert review.approve is False
        assert review.critical_count == 1
        assert len(review.findings) == 1

    def test_model_must_be_nonempty(self) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            ModelReview(
                model="",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            )


# ── Consensus gate: 75% threshold logic ─────────────────────────────────


class TestConsensusGate:
    """Test consensus evaluation with configurable thresholds.

    Ported from claude-octopus quality.sh evaluate_quality_branch().
    Default threshold: 75%. Proceed threshold: 90%.
    """

    def test_unanimous_approve_returns_proceed(self) -> None:
        reviews = [
            ModelReview(
                model=m,
                approve=True,
                approve_reason="LGTM",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            )
            for m in ("claude", "codex", "gemini")
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.PROCEED
        assert result.agreement_pct == 100.0

    def test_unanimous_reject_with_criticals_returns_escalate(self) -> None:
        """All reject + criticals → ESCALATE (criticals always need human)."""
        reviews = [
            ModelReview(
                model=m,
                approve=False,
                approve_reason="Critical bugs",
                findings=[{"severity": "critical", "title": "bug"}],
                critical_count=1,
                suggestion_count=0,
            )
            for m in ("claude", "codex", "gemini")
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.ESCALATE
        assert result.agreement_pct == 100.0

    def test_unanimous_reject_no_criticals_returns_abort(self) -> None:
        """All reject, no criticals → ABORT (nothing to escalate about)."""
        reviews = [
            ModelReview(
                model=m,
                approve=False,
                approve_reason="Not good enough",
                findings=[{"severity": "suggestion", "title": "style issue"}],
                critical_count=0,
                suggestion_count=1,
            )
            for m in ("claude", "codex", "gemini")
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.ABORT

    def test_two_of_three_approve_escalates_below_threshold(self) -> None:
        """2/3 approve = 66.7% < 75% threshold → ESCALATE."""
        reviews = [
            ModelReview(
                model="claude",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
            ModelReview(
                model="codex",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
            ModelReview(
                model="gemini",
                approve=False,
                approve_reason="issue found",
                findings=[{"severity": "suggestion", "title": "nit"}],
                critical_count=0,
                suggestion_count=1,
            ),
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.ESCALATE
        assert 66.0 <= result.agreement_pct <= 67.0

    def test_three_of_four_approve_returns_proceed_warn(self) -> None:
        """3/4 approve = 75% >= threshold but < 90% → PROCEED_WARN."""
        reviews = [
            ModelReview(
                model=m,
                approve=True,
                approve_reason="ok",
                findings=[{"severity": "nitpick", "title": "nit", "file": "a.py", "line": 1}],
                critical_count=0,
                suggestion_count=0,
            )
            for m in ("claude", "codex", "gemini")
        ] + [
            ModelReview(
                model="perplexity",
                approve=False,
                approve_reason="issue",
                findings=[{"severity": "suggestion", "title": "nit", "file": "b.py", "line": 2}],
                critical_count=0,
                suggestion_count=1,
            ),
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.PROCEED_WARN

    def test_one_of_three_approve_returns_escalate(self) -> None:
        """1/3 approve = 33.3% < 75% → escalate to human."""
        reviews = [
            ModelReview(
                model="claude",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
            ModelReview(
                model="codex",
                approve=False,
                approve_reason="bugs",
                findings=[{"severity": "critical", "title": "bug"}],
                critical_count=1,
                suggestion_count=0,
            ),
            ModelReview(
                model="gemini",
                approve=False,
                approve_reason="bugs",
                findings=[{"severity": "critical", "title": "bug"}],
                critical_count=1,
                suggestion_count=0,
            ),
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.ESCALATE

    def test_custom_threshold_lowers_bar(self) -> None:
        """Override default 75% threshold to 50% — 50% approval passes."""
        reviews = [
            ModelReview(
                model="claude",
                approve=True,
                approve_reason="ok",
                findings=[{"severity": "nitpick", "title": "nit", "file": "a.py", "line": 1}],
                critical_count=0,
                suggestion_count=0,
            ),
            ModelReview(
                model="codex",
                approve=False,
                approve_reason="nope",
                findings=[{"severity": "suggestion", "title": "issue", "file": "b.py", "line": 2}],
                critical_count=0,
                suggestion_count=0,
            ),
        ]
        # 50% approval with 50% threshold → proceed_warn (>= threshold, < 90%)
        result = evaluate_consensus(reviews, threshold_pct=50.0)
        assert result.decision == ConsensusDecision.PROCEED_WARN

    def test_empty_reviews_returns_abort(self) -> None:
        result = evaluate_consensus([])
        assert result.decision == ConsensusDecision.ABORT

    def test_single_review_uses_that_decision(self) -> None:
        reviews = [
            ModelReview(
                model="claude",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
        ]
        result = evaluate_consensus(reviews)
        assert result.decision == ConsensusDecision.PROCEED

    def test_critical_findings_override_approval(self) -> None:
        """If any model found criticals, escalate even if majority approves."""
        reviews = [
            ModelReview(
                model="claude",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
            ModelReview(
                model="codex",
                approve=True,
                approve_reason="ok with caveat",
                findings=[{"severity": "critical", "title": "race condition"}],
                critical_count=1,
                suggestion_count=0,
            ),
            ModelReview(
                model="gemini",
                approve=True,
                approve_reason="ok",
                findings=[],
                critical_count=0,
                suggestion_count=0,
            ),
        ]
        result = evaluate_consensus(reviews)
        # All approve but one found criticals → escalate despite 100% approval
        assert result.decision == ConsensusDecision.ESCALATE
        assert result.has_critical_findings is True


# ── Consensus decision enum ──────────────────────────────────────────────


class TestConsensusDecision:
    """Verify exit codes match claude-octopus quality.sh."""

    def test_all_decisions_exist(self) -> None:
        assert ConsensusDecision.PROCEED is not None
        assert ConsensusDecision.PROCEED_WARN is not None
        assert ConsensusDecision.RETRY is not None
        assert ConsensusDecision.ESCALATE is not None
        assert ConsensusDecision.ABORT is not None


# ── Autonomy modes ───────────────────────────────────────────────────────


class TestAutonomyModes:
    """Test autonomy mode behavior from claude-octopus quality.sh."""

    def test_supervised_escalates_on_warn(self) -> None:
        gate = ConsensusGate(autonomy=AutonomyMode.SUPERVISED)
        result = gate.apply_autonomy(ConsensusDecision.PROCEED_WARN)
        assert result == ConsensusDecision.ESCALATE

    def test_semi_autonomous_retries_on_warn(self) -> None:
        gate = ConsensusGate(autonomy=AutonomyMode.SEMI_AUTONOMOUS)
        result = gate.apply_autonomy(ConsensusDecision.PROCEED_WARN)
        assert result == ConsensusDecision.RETRY

    def test_autonomous_proceeds_on_warn(self) -> None:
        gate = ConsensusGate(autonomy=AutonomyMode.AUTONOMOUS)
        result = gate.apply_autonomy(ConsensusDecision.PROCEED_WARN)
        assert result == ConsensusDecision.PROCEED

    def test_all_modes_abort_on_abort(self) -> None:
        """ABORT is always final regardless of autonomy mode."""
        for mode in AutonomyMode:
            gate = ConsensusGate(autonomy=mode)
            assert gate.apply_autonomy(ConsensusDecision.ABORT) == ConsensusDecision.ABORT

    def test_all_modes_proceed_on_proceed(self) -> None:
        """PROCEED is always final regardless of autonomy mode."""
        for mode in AutonomyMode:
            gate = ConsensusGate(autonomy=mode)
            assert gate.apply_autonomy(ConsensusDecision.PROCEED) == ConsensusDecision.PROCEED


# ── Debate integrity rules ───────────────────────────────────────────────


class TestDebateIntegrity:
    """Test debate integrity rules from claude-octopus debate.sh.

    Three rules:
    - ANTI-CONTRARIAN: reviewer must not disagree just to disagree
    - ANTI-RUBBER-STAMP: reviewer must not approve without evidence
    - EVIDENCE-BASED: every claim must cite file:line or test output
    """

    def test_anti_contrarian_flags_empty_disagreement(self) -> None:
        """Disagreement without specific counter-evidence is contrarian."""
        review = ModelReview(
            model="gemini",
            approve=False,
            approve_reason="I disagree with the approach",
            findings=[],  # No specific findings — just disagrees
            critical_count=0,
            suggestion_count=0,
        )
        violations = check_debate_integrity(review)
        assert DebateIntegrityRule.ANTI_CONTRARIAN in violations

    def test_anti_rubber_stamp_flags_empty_approval(self) -> None:
        """Approval without reviewing any code is rubber-stamping."""
        review = ModelReview(
            model="codex",
            approve=True,
            approve_reason="LGTM",
            findings=[],  # No findings at all — didn't review
            critical_count=0,
            suggestion_count=0,
        )
        violations = check_debate_integrity(review)
        assert DebateIntegrityRule.ANTI_RUBBER_STAMP in violations

    def test_evidence_based_flags_no_file_references(self) -> None:
        """Findings without file:line references lack evidence."""
        review = ModelReview(
            model="claude",
            approve=False,
            approve_reason="Has issues",
            findings=[
                {"severity": "critical", "title": "Bad code"},  # No file/line
            ],
            critical_count=1,
            suggestion_count=0,
        )
        violations = check_debate_integrity(review)
        assert DebateIntegrityRule.EVIDENCE_BASED in violations

    def test_valid_review_has_no_violations(self) -> None:
        """A well-formed review with evidence passes all integrity checks."""
        review = ModelReview(
            model="claude",
            approve=False,
            approve_reason="Found a real bug at src/main.py:42",
            findings=[
                {
                    "severity": "critical",
                    "title": "Null pointer",
                    "file": "src/main.py",
                    "line": 42,
                    "issue": "x could be None here",
                    "fix": "Add None check",
                },
            ],
            critical_count=1,
            suggestion_count=0,
        )
        violations = check_debate_integrity(review)
        assert len(violations) == 0

    def test_approval_with_findings_passes_rubber_stamp(self) -> None:
        """Approval with actual findings shows the reviewer read the code."""
        review = ModelReview(
            model="gemini",
            approve=True,
            approve_reason="Minor nits only, code is solid",
            findings=[
                {
                    "severity": "nitpick",
                    "title": "Naming",
                    "file": "src/utils.py",
                    "line": 5,
                    "issue": "Could be more descriptive",
                    "fix": "Rename to process_items",
                },
            ],
            critical_count=0,
            suggestion_count=0,
        )
        violations = check_debate_integrity(review)
        assert DebateIntegrityRule.ANTI_RUBBER_STAMP not in violations


# ── Debate round structure ───────────────────────────────────────────────


class TestDebateRound:
    """Test DebateRound and DebateResult models."""

    def test_create_debate_round(self) -> None:
        rnd = DebateRound(
            round_number=1,
            reviews=[
                ModelReview(
                    model="claude",
                    approve=True,
                    approve_reason="ok",
                    findings=[],
                    critical_count=0,
                    suggestion_count=0,
                ),
            ],
            integrity_violations={},
        )
        assert rnd.round_number == 1
        assert len(rnd.reviews) == 1

    def test_debate_result_tracks_rounds(self) -> None:
        result = DebateResult(
            rounds=[
                DebateRound(round_number=1, reviews=[], integrity_violations={}),
                DebateRound(round_number=2, reviews=[], integrity_violations={}),
            ],
            final_decision=ConsensusDecision.PROCEED,
            agreement_pct=100.0,
        )
        assert len(result.rounds) == 2
        assert result.final_decision == ConsensusDecision.PROCEED


# ── ReviewSeverity enum ──────────────────────────────────────────────────


class TestReviewSeverity:
    """Severity levels matching reviewd's Severity enum."""

    def test_severity_ordering(self) -> None:
        assert ReviewSeverity.CRITICAL.weight > ReviewSeverity.SUGGESTION.weight
        assert ReviewSeverity.SUGGESTION.weight > ReviewSeverity.NITPICK.weight
        assert ReviewSeverity.NITPICK.weight > ReviewSeverity.GOOD.weight

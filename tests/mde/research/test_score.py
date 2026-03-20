"""Tests for improvement score calculation."""

from __future__ import annotations

from mde.research.score import BinaryGate, ScoreCard, calculate_score, check_binary_gates


def test_binary_gates_all_pass() -> None:
    """All gates passing returns True."""
    gates = [
        BinaryGate(name="no_regressions", passed=True),
        BinaryGate(name="validation_clean", passed=True),
        BinaryGate(name="tests_pass", passed=True),
    ]
    assert check_binary_gates(gates) is True


def test_binary_gates_one_fails() -> None:
    """A single failing gate returns False."""
    gates = [
        BinaryGate(name="no_regressions", passed=True),
        BinaryGate(name="validation_clean", passed=False),
        BinaryGate(name="tests_pass", passed=True),
    ]
    assert check_binary_gates(gates) is False


def test_calculate_score_returns_0_to_1() -> None:
    """Composite score is clamped to [0.0, 1.0]."""
    card = ScoreCard(
        validation_pass_rate=0.87,
        brew_mise_duplicates=3,
        total_tools=50,
        chezmoi_reproducible=False,
        test_coverage=0.64,
        lint_violations=8,
        stale_sources=14,
        total_sources=127,
        findings_actionable_rate=0.43,
        agent_trigger_accuracy=0.75,
        context_efficiency=0.5,
        rewrite_rate=0.1,
    )
    score = calculate_score(card)
    assert 0.0 <= score <= 1.0

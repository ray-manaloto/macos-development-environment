"""Improvement score calculator with binary gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BinaryGate:
    """A pass/fail gate that must clear before scoring."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class ScoreCard:
    """Metric fields for computing a weighted improvement score."""

    validation_pass_rate: float = 0.0
    brew_mise_duplicates: int = 0
    total_tools: int = 1
    chezmoi_reproducible: bool = False
    test_coverage: float = 0.0
    lint_violations: int = 0
    stale_sources: int = 0
    total_sources: int = 1
    findings_actionable_rate: float = 0.0
    agent_trigger_accuracy: float = 0.0
    context_efficiency: float = 0.0
    rewrite_rate: float = 0.0


def check_binary_gates(gates: list[BinaryGate]) -> bool:
    """Return True only if every gate passes."""
    return all(g.passed for g in gates)


def calculate_score(card: ScoreCard) -> float:
    """Compute a weighted composite score in [0.0, 1.0].

    NOTE: Weights deviate from the original spec (Section 6.2) per the
    implementation plan. Changes: validation_pass_rate reduced from 0.20
    to 0.15, brew_mise_duplicates from 0.15 to 0.10, token_cost_normalized
    replaced by context_efficiency (0.10) + rewrite_rate (0.05).
    See docs/superpowers/plans/2026-03-20-self-improving-research-system.md.

    Formula weights (sum to 1.0):
        validation_pass_rate        0.15
        tool-duplicate ratio        0.10
        chezmoi_reproducible        0.15
        test_coverage               0.10
        lint cleanliness            0.05
        source freshness            0.10
        findings_actionable_rate    0.10
        agent_trigger_accuracy      0.10
        context_efficiency          0.10
        rewrite avoidance           0.05
    """
    total_tools = max(card.total_tools, 1)
    total_sources = max(card.total_sources, 1)

    raw = (
        card.validation_pass_rate * 0.15
        + (1 - card.brew_mise_duplicates / total_tools) * 0.10
        + float(card.chezmoi_reproducible) * 0.15
        + card.test_coverage * 0.10
        + (1 - card.lint_violations / 100) * 0.05
        + (1 - card.stale_sources / total_sources) * 0.10
        + card.findings_actionable_rate * 0.10
        + card.agent_trigger_accuracy * 0.10
        + card.context_efficiency * 0.10
        + (1 - card.rewrite_rate) * 0.05
    )
    return max(0.0, min(1.0, raw))

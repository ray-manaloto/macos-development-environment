"""Generate improvement proposals from extracted patterns.

Applies the promotion ladder: patterns that exceed the recurrence
threshold for a given target type generate proposals. Proposals
are tagged with autonomy tier (auto vs approve).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from mde.dream.models import (
    PROMOTION_THRESHOLDS,
    TIER_MAP,
    Pattern,
    PromotionTarget,
    Proposal,
)
from mde.dream.state import load_state, save_state


def generate_proposals() -> list[Proposal]:
    """Scan patterns and create proposals for those exceeding thresholds.

    Returns newly created proposals (does not include existing ones).
    """
    state = load_state()
    new_proposals: list[Proposal] = []

    # Track which patterns already have pending/applied proposals
    existing_keys = {p.pattern_key for p in state.proposals if p.status in ("pending", "applied")}

    for key, pattern in state.patterns.items():
        if key in existing_keys:
            continue

        target = _select_target(pattern.recurrence)
        if target is None:
            continue

        proposal = Proposal(
            id=_make_id(key, target),
            pattern_key=key,
            target=target,
            tier=TIER_MAP[target],
            title=f"Promote '{key}' to {target.value}",
            description=_draft_description(pattern, target),
            recurrence=pattern.recurrence,
        )
        state.proposals.append(proposal)
        new_proposals.append(proposal)

    state.last_propose = datetime.now(tz=UTC)
    save_state(state)

    return new_proposals


def _select_target(recurrence: int) -> PromotionTarget | None:
    """Select the highest-tier target that the recurrence count qualifies for."""
    # Walk targets from highest threshold to lowest
    candidates = sorted(PROMOTION_THRESHOLDS.items(), key=lambda x: x[1], reverse=True)
    for target, threshold in candidates:
        if recurrence >= threshold:
            return target
    return None


def _draft_description(pattern: Pattern, target: PromotionTarget) -> str:
    """Draft a proposal description from pattern and target."""
    lines = [
        f"Pattern '{pattern.key}' has been observed {pattern.recurrence} time(s).",
        f"Source: {pattern.source.value}",
        f"First seen: {pattern.first_seen.date()}",
        f"Last seen: {pattern.last_seen.date()}",
        "",
        f"Proposed action: create/update {target.value} entry.",
        f"Description: {pattern.description}",
    ]

    if pattern.examples:
        lines.append("")
        lines.append("Examples:")
        lines.extend(f"  - {ex}" for ex in pattern.examples[:3])

    return "\n".join(lines)


def _make_id(key: str, target: PromotionTarget) -> str:
    """Generate a short deterministic proposal ID."""
    raw = f"{key}:{target.value}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]

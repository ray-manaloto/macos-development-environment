"""Show dream pipeline status and pattern inventory."""

from __future__ import annotations

from collections import Counter

from mde.dream.models import PROMOTION_THRESHOLDS, DreamState, PromotionTarget
from mde.dream.state import load_state


def show_status() -> None:
    """Print pipeline state summary."""
    state = load_state()

    print("Dream Pipeline Status")  # noqa: T201
    print("=" * 40)  # noqa: T201

    _print_overview(state)
    _print_patterns(state)
    _print_proposals(state)
    _print_promotion_ladder()


def _print_overview(state: DreamState) -> None:
    """Print high-level stats."""
    print(f"\nPatterns:  {len(state.patterns)}")  # noqa: T201
    print(f"Proposals: {len(state.proposals)}")  # noqa: T201
    print(f"Extracts:  {state.extract_count}")  # noqa: T201
    print(f"Applied:   {state.apply_count}")  # noqa: T201

    if state.last_extract:
        print(f"Last extract: {state.last_extract.date()}")  # noqa: T201
    if state.last_propose:
        print(f"Last propose: {state.last_propose.date()}")  # noqa: T201


def _print_patterns(state: DreamState) -> None:
    """Print top patterns by recurrence."""
    if not state.patterns:
        print("\nNo patterns extracted yet. Run: mde-py dream extract")  # noqa: T201
        return

    print("\nTop Patterns (by recurrence):")  # noqa: T201
    sorted_patterns = sorted(state.patterns.values(), key=lambda p: p.recurrence, reverse=True)
    for p in sorted_patterns[:15]:
        target = _eligible_target(p.recurrence)
        marker = f" → {target.value}" if target else ""
        print(f"  [{p.recurrence:3d}x] {p.key}{marker}")  # noqa: T201

    # Source distribution
    sources = Counter(p.source.value for p in state.patterns.values())
    print(f"\nSources: {dict(sources)}")  # noqa: T201


def _print_proposals(state: DreamState) -> None:
    """Print proposal summary by status."""
    if not state.proposals:
        return

    by_status = Counter(p.status for p in state.proposals)
    print(f"\nProposals: {dict(by_status)}")  # noqa: T201

    pending = [p for p in state.proposals if p.status == "pending"]
    if pending:
        print(f"\nPending proposals ({len(pending)}):")  # noqa: T201
        for p in pending[:10]:
            print(f"  [{p.tier.value:7s}] {p.title} (id: {p.id})")  # noqa: T201


def _print_promotion_ladder() -> None:
    """Print the promotion threshold reference."""
    print("\nPromotion Ladder:")  # noqa: T201
    for target, threshold in sorted(PROMOTION_THRESHOLDS.items(), key=lambda x: x[1]):
        print(f"  {threshold:2d}x → {target.value}")  # noqa: T201


def _eligible_target(recurrence: int) -> PromotionTarget | None:
    """Find the highest target a recurrence count qualifies for."""
    candidates = sorted(PROMOTION_THRESHOLDS.items(), key=lambda x: x[1], reverse=True)
    for target, threshold in candidates:
        if recurrence >= threshold:
            return target
    return None

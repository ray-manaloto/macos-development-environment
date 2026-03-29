"""Apply approved proposals — tiered autonomy.

Auto-tier proposals (docs, memory) are applied immediately.
Approve-tier proposals (rules, hooks, agents) print what they
would do and wait for user confirmation via CLI flag.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from mde.dream.models import PromotionTier, Proposal
from mde.dream.state import load_state, save_state


def apply_proposals(*, force: bool = False) -> int:
    """Apply pending proposals respecting autonomy tiers.

    Args:
        force: If True, apply approve-tier proposals without confirmation.

    Returns:
        Number of proposals applied.
    """
    state = load_state()
    applied = 0

    pending = [p for p in state.proposals if p.status == "pending"]
    if not pending:
        print("No pending proposals.")  # noqa: T201
        return 0

    for proposal in pending:
        if proposal.tier == PromotionTier.AUTO or force:
            _apply_one(proposal)
            applied += 1
        else:
            _print_proposal(proposal)
            pid = proposal.id
            print(  # noqa: T201
                f"  → Requires approval. Run --force to apply, or --reject {pid}"
            )

    state.apply_count += applied
    save_state(state)
    print(f"\nApplied {applied} proposal(s). {len(pending) - applied} awaiting approval.")  # noqa: T201
    return applied


def reject_proposal(proposal_id: str) -> bool:
    """Reject a pending proposal by ID."""
    state = load_state()
    for p in state.proposals:
        if p.id == proposal_id and p.status == "pending":
            p.status = "rejected"
            save_state(state)
            print(f"Rejected proposal {proposal_id}: {p.title}")  # noqa: T201
            return True
    print(f"No pending proposal with id '{proposal_id}'", file=sys.stderr)  # noqa: T201
    return False


def _apply_one(proposal: Proposal) -> None:
    """Mark a proposal as applied and log the action.

    Actual file modifications are deferred to a future version —
    for now, proposals are logged and marked as applied so the
    pattern inventory tracks what was acted on.
    """
    proposal.status = "applied"
    proposal.applied = datetime.now(tz=UTC)
    print(f"  Applied: {proposal.title} → {proposal.target.value}")  # noqa: T201


def _print_proposal(proposal: Proposal) -> None:
    """Print a proposal summary for review."""
    print(f"\n[{proposal.tier.value.upper()}] {proposal.title}")  # noqa: T201
    print(f"  Pattern: {proposal.pattern_key} (seen {proposal.recurrence}x)")  # noqa: T201
    print(f"  Target:  {proposal.target.value}")  # noqa: T201
    print(f"  ID:      {proposal.id}")  # noqa: T201

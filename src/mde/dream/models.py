"""Domain models for the dream self-improvement pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PatternSource(str, Enum):
    """Where a pattern was observed."""

    AUTO_MEMORY = "auto_memory"
    REMEMBER = "remember"
    CLAUDE_MEM = "claude_mem"
    RETRO = "retro"
    QUALITY_GATE = "quality_gate"
    CODE_REVIEW = "code_review"
    HOOK_FEEDBACK = "hook_feedback"
    GITHUB_ISSUES = "github_issues"
    LEARNINGS = "learnings"
    TRANSCRIPTS = "transcripts"


class PromotionTarget(str, Enum):
    """Where a pattern should be promoted to."""

    MEMORY = "memory"  # auto memory entry
    DOCS = "docs"  # documentation update
    RULE = "rule"  # .claude/rules/*.md
    AGENT_DEF = "agent_def"  # .claude/agents/*.md
    HOOK = "hook"  # src/mde/hooks/*.py
    SKILL = "skill"  # rsm-subagents/plugins/*/skills/
    CLAUDE_MD = "claude_md"  # CLAUDE.md section


class PromotionTier(str, Enum):
    """Autonomy tier for applying proposals."""

    AUTO = "auto"  # applied without approval (docs, memory)
    APPROVE = "approve"  # requires user approval (rules, hooks, agents)


# Promotion ladder thresholds (from pskoett-ai-skills pattern)
PROMOTION_THRESHOLDS: dict[PromotionTarget, int] = {
    PromotionTarget.MEMORY: 1,  # immediate
    PromotionTarget.DOCS: 2,  # recurrence ≥2
    PromotionTarget.RULE: 3,  # recurrence ≥3
    PromotionTarget.CLAUDE_MD: 3,  # recurrence ≥3
    PromotionTarget.AGENT_DEF: 5,  # recurrence ≥5
    PromotionTarget.HOOK: 10,  # recurrence ≥10
    PromotionTarget.SKILL: 10,  # recurrence ≥10
}

# Which targets are auto-applied vs require approval
TIER_MAP: dict[PromotionTarget, PromotionTier] = {
    PromotionTarget.MEMORY: PromotionTier.AUTO,
    PromotionTarget.DOCS: PromotionTier.AUTO,
    PromotionTarget.RULE: PromotionTier.APPROVE,
    PromotionTarget.CLAUDE_MD: PromotionTier.APPROVE,
    PromotionTarget.AGENT_DEF: PromotionTier.APPROVE,
    PromotionTarget.HOOK: PromotionTier.APPROVE,
    PromotionTarget.SKILL: PromotionTier.APPROVE,
}


class Pattern(BaseModel):
    """A recurring pattern extracted from signal sources."""

    key: str = Field(description="Unique pattern key (e.g. 'harden.input_validation')")
    description: str = Field(description="Human-readable description of the pattern")
    source: PatternSource = Field(description="Signal source where pattern was observed")
    recurrence: int = Field(default=1, description="Number of times observed")
    first_seen: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    examples: list[str] = Field(default_factory=list, description="Example occurrences (max 5)")


class Proposal(BaseModel):
    """An improvement proposal generated from patterns."""

    id: str = Field(description="Unique proposal ID")
    pattern_key: str = Field(description="Pattern that triggered this proposal")
    target: PromotionTarget = Field(description="Where to apply the improvement")
    tier: PromotionTier = Field(description="Autonomy tier (auto or approve)")
    title: str = Field(description="Short title for the proposal")
    description: str = Field(description="What change to make and why")
    recurrence: int = Field(description="Pattern recurrence count at proposal time")
    status: str = Field(default="pending", description="pending | approved | applied | rejected")
    created: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    applied: datetime | None = Field(default=None, description="When the proposal was applied")


class DreamState(BaseModel):
    """Persistent state for the dream pipeline."""

    patterns: dict[str, Pattern] = Field(default_factory=dict)
    proposals: list[Proposal] = Field(default_factory=list)
    last_extract: datetime | None = Field(default=None)
    last_propose: datetime | None = Field(default=None)
    extract_count: int = Field(default=0)
    apply_count: int = Field(default=0)

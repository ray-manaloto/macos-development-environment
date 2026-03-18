"""Pydantic models for agent team configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamSubagent(BaseModel):
    """A subagent within an agent team."""

    id: str = Field(description="Subagent identifier")
    stage: int | str = Field(default=1, description="Execution stage (int or letter)")
    objective: str = Field(default="", description="What this subagent does")
    required_skills: list[str] = Field(default_factory=list)
    required_plugins: list[str] = Field(default_factory=list)
    gate_criteria: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    prompt_file: str = Field(default="", description="Path to prompt markdown")


class TeamMeta(BaseModel):
    """Team-level metadata."""

    id: str = Field(description="Team identifier")
    name: str = Field(description="Team display name")
    goal: str = Field(default="")
    output_dir: str = Field(default="")
    shared_artifacts_dir: str = Field(default="")
    repo_root: str = Field(default=".")
    depends_on: list[str] = Field(default_factory=list)
    # Domain-team extras (optional)
    domain_id: str = Field(default="")
    bundle_path: str = Field(default="")
    preset_ids: list[str] = Field(default_factory=list)
    reference_source_group: str = Field(default="")
    learning_record_id: str = Field(default="")
    workflow_skill: str = Field(default="")


class TeamConfig(BaseModel):
    """Agent team configuration."""

    team: TeamMeta
    subagents: list[TeamSubagent] = Field(default_factory=list)

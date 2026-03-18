"""Pydantic models for agent team configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamSubagent(BaseModel):
    """A subagent within an agent team."""

    name: str = Field(description="Subagent name")
    role: str = Field(default="", description="Subagent role description")
    agent_type: str = Field(default="general-purpose", description="Agent type to use")


class TeamConfig(BaseModel):
    """Agent team configuration."""

    name: str = Field(description="Team name")
    description: str = Field(default="")
    subagents: list[TeamSubagent] = Field(default_factory=list)
    output_validator: str = Field(default="", description="Path to output validator script")
    config_path: str = Field(default="", description="Source config file path")

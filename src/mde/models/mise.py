"""Pydantic models for mise configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MiseToolEntry(BaseModel):
    """A single tool entry in mise config."""

    name: str = Field(description="Tool name (e.g. 'python', 'node')")
    version: str = Field(description="Version spec (e.g. '3.12', 'latest')")
    backend: str = Field(default="", description="Backend (e.g. 'pipx', 'npm', 'aqua')")


class MiseTaskEntry(BaseModel):
    """A single task entry in mise config."""

    name: str = Field(description="Task name (e.g. 'mde:validate')")
    description: str = Field(default="")
    run: str = Field(default="", description="Shell command to execute")


class MiseConfig(BaseModel):
    """Parsed mise configuration."""

    tools: list[MiseToolEntry] = Field(default_factory=list)
    tasks: list[MiseTaskEntry] = Field(default_factory=list)
    includes: list[str] = Field(default_factory=list, description="Include paths")
    raw_toml: str = Field(default="", description="Raw TOML content for re-serialization")

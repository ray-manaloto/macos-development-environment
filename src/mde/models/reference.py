"""Pydantic models for reference source configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReferenceSource(BaseModel):
    """A single reference source entry."""

    url: str = Field(description="Source URL")
    label: str = Field(default="", description="Human-readable label")
    domain: str = Field(default="", description="Domain this source belongs to")


class SourceGroup(BaseModel):
    """A group of reference sources."""

    domain: str = Field(description="Domain name")
    sources: list[ReferenceSource] = Field(default_factory=list)

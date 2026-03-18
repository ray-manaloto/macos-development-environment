"""Pydantic models for claude-flow swarm configuration."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Topology(str, Enum):
    """Swarm topology types."""

    HIERARCHICAL = "hierarchical"
    MESH = "mesh"
    HIERARCHICAL_MESH = "hierarchical-mesh"
    RING = "ring"
    STAR = "star"
    HYBRID = "hybrid"


class SwarmConfig(BaseModel):
    """Claude-flow swarm configuration."""

    topology: Topology = Field(default=Topology.HIERARCHICAL)
    max_agents: int = Field(default=8)
    strategy: str = Field(default="specialized")
    consensus: str = Field(default="raft")

"""SkillKit API Pydantic models.

Vendored from: https://github.com/rohitg00/skillkit/blob/main/clients/python/skillkit/models.py
License: Apache-2.0
Reason: skillkit-client not published to PyPI (missing README.md in build).

When the upstream package is fixed, replace this with:
    pip install skillkit-client
"""

from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "CacheStats",
    "CategoriesResponse",
    "Category",
    "HealthResponse",
    "SearchResponse",
    "Skill",
    "TrendingResponse",
]


class Skill(BaseModel):
    """A skill from SkillKit search."""

    name: str
    description: str | None = None
    source: str
    repo: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    content: str | None = None
    stars: int | None = None
    installs: int | None = None


class SearchResponse(BaseModel):
    """Response from GET /search."""

    skills: list[Skill]
    total: int
    query: str
    limit: int


class HealthResponse(BaseModel):
    """Response from GET /health."""

    status: str
    version: str
    skill_count: int = 0
    uptime: int = 0


class CacheStats(BaseModel):
    """Response from GET /cache/stats."""

    hits: int
    misses: int
    size: int
    max_size: int = 0
    hit_rate: float = 0.0


class Category(BaseModel):
    """A skill category."""

    name: str
    count: int


class CategoriesResponse(BaseModel):
    """Response from GET /categories."""

    categories: list[Category]
    total: int


class TrendingResponse(BaseModel):
    """Response from GET /trending."""

    skills: list[Skill]
    limit: int

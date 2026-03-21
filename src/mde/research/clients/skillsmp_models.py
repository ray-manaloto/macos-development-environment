"""SkillsMP API Pydantic models.

Auto-generated from SkillsMP REST API responses (2026-03-21).
API docs: https://skillsmp.com/docs/api

Endpoints modeled:
- GET /api/v1/skills/search (keyword search)
- GET /api/v1/skills/ai-search (AI semantic search)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "AISearchResponse",
    "AISearchResult",
    "ErrorDetail",
    "ErrorResponse",
    "Skill",
    "SkillSearchData",
    "SkillSearchResponse",
]


class Skill(BaseModel):
    """A skill from SkillsMP keyword search."""

    id: str
    name: str
    author: str
    description: str = ""
    github_url: str = Field("", alias="githubUrl")
    skill_url: str = Field("", alias="skillUrl")
    stars: int = 0
    updated_at: str = Field("", alias="updatedAt")

    model_config = {"populate_by_name": True}


class SkillSearchData(BaseModel):
    """Data payload from keyword search response."""

    skills: list[Skill] = []
    total: int = 0
    page: int = 1
    limit: int = 20


class SkillSearchResponse(BaseModel):
    """Top-level response from GET /api/v1/skills/search."""

    success: bool
    data: SkillSearchData | None = None


class AISearchResult(BaseModel):
    """A single result from AI semantic search."""

    file_id: str = ""
    filename: str = ""
    score: float = 0.0


class AISearchData(BaseModel):
    """Data payload from AI search response."""

    object: str = ""
    search_query: str = ""
    data: list[AISearchResult] = []


class AISearchResponse(BaseModel):
    """Top-level response from GET /api/v1/skills/ai-search."""

    success: bool
    data: AISearchData | None = None


class ErrorDetail(BaseModel):
    """Error detail from API error responses."""

    code: str = ""
    message: str = ""


class ErrorResponse(BaseModel):
    """Error response from SkillsMP API."""

    success: bool = False
    error: ErrorDetail | None = None

"""Tests for SkillsMP Pydantic models."""

from __future__ import annotations

from mde.research.clients.skillsmp_models import (
    ErrorResponse,
    Skill,
    SkillSearchData,
    SkillSearchResponse,
)


class TestSkill:
    """Tests for the Skill model."""

    def test_minimal_construction(self) -> None:
        skill = Skill(id="abc123", name="terraform", author="hashicorp")
        assert skill.name == "terraform"
        assert skill.author == "hashicorp"
        assert skill.stars == 0
        assert skill.description == ""

    def test_camel_case_alias_parsing(self) -> None:
        data = {
            "id": "1",
            "name": "test",
            "author": "me",
            "githubUrl": "https://github.com/me/test",
            "skillUrl": "https://skillsmp.com/skills/test",
            "updatedAt": "2026-01-01",
        }
        skill = Skill.model_validate(data)
        assert skill.github_url == "https://github.com/me/test"
        assert skill.skill_url == "https://skillsmp.com/skills/test"
        assert skill.updated_at == "2026-01-01"

    def test_snake_case_construction(self) -> None:
        skill = Skill(id="1", name="test", author="me", github_url="https://example.com")
        assert skill.github_url == "https://example.com"


class TestSkillSearchResponse:
    """Tests for the SkillSearchResponse model."""

    def test_success_with_data(self) -> None:
        data = {
            "success": True,
            "data": {
                "skills": [{"id": "1", "name": "terraform", "author": "hashicorp", "stars": 100}],
                "total": 1,
                "page": 1,
                "limit": 20,
            },
        }
        resp = SkillSearchResponse.model_validate(data)
        assert resp.success is True
        assert resp.data is not None
        assert len(resp.data.skills) == 1
        assert resp.data.skills[0].stars == 100

    def test_success_with_null_data(self) -> None:
        resp = SkillSearchResponse(success=True, data=None)
        assert resp.data is None

    def test_empty_skills_list(self) -> None:
        resp = SkillSearchResponse(success=True, data=SkillSearchData())
        assert resp.data is not None
        assert resp.data.skills == []
        assert resp.data.total == 0


class TestErrorResponse:
    """Tests for the ErrorResponse model."""

    def test_error_response(self) -> None:
        data = {
            "success": False,
            "error": {"code": "RATE_LIMIT", "message": "Too many requests"},
        }
        resp = ErrorResponse.model_validate(data)
        assert resp.success is False
        assert resp.error is not None
        assert resp.error.code == "RATE_LIMIT"

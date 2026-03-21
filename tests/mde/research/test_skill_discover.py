"""Tests for unified skill discovery."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    import pytest

from mde.research.skill_discover import (
    DiscoveryResult,
    SkillResult,
    _parse_skills_sh_line,
    _strip_ansi,
    cli_main,
    discover_skills,
)


class TestStripAnsi:
    """Tests for ANSI escape code stripping."""

    def test_removes_color_codes(self) -> None:
        assert _strip_ansi("\x1b[32mhello\x1b[0m") == "hello"

    def test_plain_text_unchanged(self) -> None:
        assert _strip_ansi("hello world") == "hello world"


class TestParseSkillsShLine:
    """Tests for skills.sh line parser."""

    def test_parses_skill_with_installs(self) -> None:
        skills: list[SkillResult] = []
        _parse_skills_sh_line(
            "hashicorp@terraform-style-guide 2,000 installs",
            skills,
        )
        assert len(skills) == 1
        assert skills[0].name == "terraform-style-guide"
        assert skills[0].author == "hashicorp"
        assert skills[0].installs == 2000
        assert skills[0].source == "skills.sh"

    def test_parses_url_line(self) -> None:
        skills: list[SkillResult] = []
        _parse_skills_sh_line("test@my-skill 50 installs", skills)
        _parse_skills_sh_line(
            "\u2514 https://skills.sh/test/my-skill",
            skills,
        )
        assert skills[0].url == "https://skills.sh/test/my-skill"

    def test_ignores_irrelevant_lines(self) -> None:
        skills: list[SkillResult] = []
        _parse_skills_sh_line("Some random output", skills)
        assert len(skills) == 0

    def test_k_suffix_replaced(self) -> None:
        """K replaced with '000': '7.3K' -> '7.3000' -> int(7.3) -> 7."""
        skills: list[SkillResult] = []
        _parse_skills_sh_line("author@skill 7.3K installs", skills)
        assert skills[0].installs == 7


class TestSkillResultSortKey:
    """Tests for SkillResult sort_key property."""

    def test_higher_installs_sorts_first(self) -> None:
        a = SkillResult(name="a", author="x", source="s", installs=100)
        b = SkillResult(name="b", author="x", source="s", installs=50)
        assert a.sort_key < b.sort_key

    def test_same_installs_higher_stars_first(self) -> None:
        a = SkillResult(
            name="a",
            author="x",
            source="s",
            installs=10,
            stars=50,
        )
        b = SkillResult(
            name="b",
            author="x",
            source="s",
            installs=10,
            stars=20,
        )
        assert a.sort_key < b.sort_key

    def test_same_metrics_alphabetical(self) -> None:
        a = SkillResult(name="alpha", author="x", source="s")
        b = SkillResult(name="beta", author="x", source="s")
        assert a.sort_key < b.sort_key


class TestDiscoverSkills:
    """Tests for the discover_skills orchestrator."""

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_merges_results_from_all_sources(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        mock_installed.return_value = set()
        mock_sh.return_value = [
            SkillResult(
                name="skill-a",
                author="a",
                source="skills.sh",
                installs=10,
            ),
        ]
        mock_gh.return_value = [
            SkillResult(name="skill-b", author="b", source="github"),
        ]
        mock_smp.return_value = [
            SkillResult(
                name="skill-c",
                author="c",
                source="skillsmp",
                stars=5,
            ),
        ]

        result = discover_skills("test")
        assert len(result.skills) == 3
        assert set(result.sources_searched) == {
            "skills.sh",
            "github",
            "skillsmp",
        }

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_deduplicates_by_author_name(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        mock_installed.return_value = set()
        mock_sh.return_value = [
            SkillResult(
                name="terraform",
                author="hashicorp",
                source="skills.sh",
                installs=100,
            ),
        ]
        mock_gh.return_value = [
            SkillResult(
                name="terraform",
                author="hashicorp",
                source="github",
                installs=0,
            ),
        ]
        mock_smp.return_value = []

        result = discover_skills("terraform")
        assert len(result.skills) == 1
        assert result.skills[0].installs == 100

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_marks_installed_skills(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        mock_installed.return_value = {"terraform"}
        mock_sh.return_value = [
            SkillResult(
                name="terraform",
                author="h",
                source="skills.sh",
            ),
        ]
        mock_gh.return_value = []
        mock_smp.return_value = []

        result = discover_skills("terraform")
        assert result.skills[0].installed is True

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_failed_source_recorded(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        mock_installed.return_value = set()
        mock_sh.side_effect = TimeoutError("timed out")
        mock_gh.return_value = []
        mock_smp.return_value = []

        result = discover_skills("test")
        assert len(result.sources_failed) == 1
        assert "skills.sh" in result.sources_failed[0]
        assert "github" in result.sources_searched


class TestCliMain:
    """Tests for the CLI entry point."""

    @patch("mde.research.skill_discover.discover_skills")
    def test_json_output(
        self,
        mock_discover: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_discover.return_value = DiscoveryResult(
            query="test",
            skills=[SkillResult(name="s", author="a", source="sh")],
            sources_searched=["skills.sh"],
        )
        result = cli_main(["test", "--json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["query"] == "test"
        assert len(data["skills"]) == 1

    @patch("mde.research.skill_discover.discover_skills")
    def test_no_results_message(
        self,
        mock_discover: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_discover.return_value = DiscoveryResult(
            query="nonexistent",
            skills=[],
            sources_searched=["skills.sh"],
        )
        result = cli_main(["nonexistent"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No skills found" in captured.out

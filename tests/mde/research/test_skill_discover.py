"""Tests for unified skill discovery."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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

    @pytest.mark.parametrize(
        ("line", "expected_name", "expected_author", "expected_installs"),
        [
            (
                "hashicorp@terraform-style-guide 2,000 installs",
                "terraform-style-guide",
                "hashicorp",
                2000,
            ),
            ("author@skill 7.3K installs", "skill", "author", 7300),
            ("author@skill 1.2M installs", "skill", "author", 1_200_000),
            ("author@skill 50 installs", "skill", "author", 50),
        ],
        ids=["comma-separated", "k-suffix", "m-suffix", "plain-number"],
    )
    def test_parses_skill_with_installs(
        self,
        line: str,
        expected_name: str,
        expected_author: str,
        expected_installs: int,
    ) -> None:
        skills: list[SkillResult] = []
        _parse_skills_sh_line(line, skills)
        assert len(skills) == 1
        assert skills[0].name == expected_name
        assert skills[0].author == expected_author
        assert skills[0].installs == expected_installs
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


class TestSearchSkillsSh:
    """Tests for skills.sh subprocess search."""

    @patch("mde.research.skill_discover.subprocess.run")
    def test_nonzero_returncode_logs_warning(
        self,
        mock_run: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Non-zero exit from npx skills search logs a warning."""
        from mde.research.skill_discover import _search_skills_sh

        mock_run.return_value = MagicMock(stdout="", returncode=1, stderr="not found")
        import logging

        with caplog.at_level(logging.WARNING):
            results = _search_skills_sh("nonexistent")
        assert results == []
        assert any("skills.sh" in r.message and "exit" in r.message for r in caplog.records)


class TestSearchGitHub:
    """Tests for GitHub code search result parsing."""

    @patch("mde.research.skill_discover.subprocess.run")
    def test_nonzero_returncode_logs_warning(
        self,
        mock_run: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Non-zero exit from gh search code logs a warning."""
        from mde.research.skill_discover import _search_github

        mock_run.return_value = MagicMock(stdout="", returncode=1, stderr="error")
        import logging

        with caplog.at_level(logging.WARNING):
            results = _search_github("nonexistent")
        assert results == []
        assert any("github" in r.message.lower() and "exit" in r.message for r in caplog.records)

    @patch("mde.research.skill_discover.subprocess.run")
    def test_parses_github_search_output(self, mock_run: MagicMock) -> None:
        """Parse realistic gh search code output into SkillResult."""
        from mde.research.skill_discover import _search_github

        mock_run.return_value = MagicMock(
            stdout=(
                "hashicorp/terraform-skills:skills/terraform-style-guide/SKILL.md: description\n"
                "user/repo:agents/skills/my-skill/SKILL.md: some content\n"
            ),
            returncode=0,
        )
        results = _search_github("terraform")
        assert len(results) >= 1
        assert results[0].source == "github"
        assert results[0].author == "hashicorp"
        assert "github.com" in results[0].url

    @patch("mde.research.skill_discover.subprocess.run")
    def test_deduplicates_by_author_skill(self, mock_run: MagicMock) -> None:
        """Duplicate author/skill combinations are deduplicated."""
        from mde.research.skill_discover import _search_github

        mock_run.return_value = MagicMock(
            stdout=(
                "user/repo:skills/my-skill/SKILL.md: line1\n"
                "user/repo:skills/my-skill/SKILL.md: line2\n"
            ),
            returncode=0,
        )
        results = _search_github("test")
        assert len(results) == 1


class TestSearchSkillsMP:
    """Tests for SkillsMP search result conversion."""

    def test_converts_skillsmp_results(self) -> None:
        """SkillsMP results are correctly mapped to SkillResult fields."""
        from unittest.mock import PropertyMock

        from mde.research.clients.skillsmp_client import SkillsMPClient
        from mde.research.clients.skillsmp_models import Skill as SMPSkill
        from mde.research.clients.skillsmp_models import SkillSearchData, SkillSearchResponse
        from mde.research.skill_discover import _search_skillsmp

        with (
            patch.object(
                SkillsMPClient,
                "is_configured",
                new_callable=PropertyMock,
                return_value=True,
            ),
            patch.object(SkillsMPClient, "search") as mock_search,
        ):
            mock_search.return_value = SkillSearchResponse(
                success=True,
                data=SkillSearchData(
                    skills=[
                        SMPSkill(
                            id="1",
                            name="terraform",
                            author="hashicorp",
                            description="Terraform skills",
                            stars=100,
                            skill_url="https://skillsmp.com/skills/terraform",
                        )
                    ],
                    total=1,
                ),
            )

            results = _search_skillsmp("terraform")

        assert len(results) == 1
        assert results[0].name == "terraform"
        assert results[0].author == "hashicorp"
        assert results[0].source == "skillsmp"
        assert results[0].stars == 100
        assert results[0].description == "Terraform skills"
        assert results[0].url == "https://skillsmp.com/skills/terraform"


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

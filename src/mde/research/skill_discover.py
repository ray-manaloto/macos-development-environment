"""Unified skill discovery across all working sources.

Searches skills.sh, GitHub code search, SkillsMP, and skillport local
inventory. Merges results into a ranked de-duplicated list and marks
installed skills.

All CLI tools are invoked directly via mise-managed PATH — never npx.

Usage:
    uv run mde-py research skill-discover <query>
    uv run mde-py research skill-discover <query> --json
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_log = logging.getLogger(__name__)

__all__ = ["SkillResult", "discover_skills"]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_MIN_PARTS = 2


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return _ANSI_RE.sub("", text)


@dataclass
class SkillResult:
    """A discovered skill from any source."""

    name: str
    author: str
    source: str  # "skills.sh", "github", "skillsmp", "skillport", "skillfish"
    installs: int = 0
    stars: int = 0
    description: str = ""
    url: str = ""
    installed: bool = False

    @property
    def sort_key(self) -> tuple[int, int, str]:
        """Sort by installs (desc), stars (desc), name (asc)."""
        return (-self.installs, -self.stars, self.name)


@dataclass
class DiscoveryResult:
    """Merged results from all sources."""

    query: str
    skills: list[SkillResult] = field(default_factory=list)
    sources_searched: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    installed_matches: list[str] = field(default_factory=list)


def _parse_skills_sh_line(line: str, skills: list[SkillResult]) -> None:
    """Parse a single line of skills.sh output."""
    clean = _strip_ansi(line).strip()
    if "installs" in clean.lower():
        parts = clean.split()
        if len(parts) >= _MIN_PARTS:
            name_part = parts[0]
            raw = parts[1].replace(",", "")
            suffixes = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
            multiplier = suffixes.get(raw[-1:].upper(), 1)
            numeric = raw[:-1] if multiplier > 1 else raw
            try:
                installs = int(float(numeric) * multiplier)
            except ValueError:
                installs = 0
            author, _, skill_name = name_part.partition("@")
            if not skill_name:
                skill_name = author
                author = ""
            elif "/" in author:
                author = author.split("/")[0]
            skills.append(
                SkillResult(name=skill_name, author=author, source="skills.sh", installs=installs),
            )
    elif "skills.sh/" in clean and skills:
        url = clean.lstrip("└ ").strip()
        if url.startswith("http"):
            skills[-1].url = url


def _search_skills_sh(query: str) -> list[SkillResult]:
    """Search skills.sh via mise-managed skills CLI (not npx)."""
    skills_bin = shutil.which("skills")
    if not skills_bin:
        _log.warning("skills CLI not found in PATH (install via mise: npm:skills)")
        return []
    result = subprocess.run(
        [skills_bin, "find", query],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        _log.warning("skills.sh search exit %d: %s", result.returncode, result.stderr.strip())
    skills: list[SkillResult] = []
    for line in result.stdout.split("\n"):
        _parse_skills_sh_line(line, skills)
    return skills


def _search_github(query: str) -> list[SkillResult]:
    """Search GitHub code for SKILL.md files mentioning the query."""
    result = subprocess.run(
        ["gh", "search", "code", query, "--filename", "SKILL.md", "--limit", "10"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        _log.warning("GitHub search exit %d: %s", result.returncode, result.stderr.strip())
    skills: list[SkillResult] = []
    seen: set[str] = set()
    for line in result.stdout.split("\n"):
        if "SKILL.md" not in line or ":" not in line:
            continue
        repo_path = line.split(":")[0]
        if "/" not in repo_path:
            continue
        parts = repo_path.split("/")
        author = parts[0]
        repo = parts[1] if len(parts) > 1 else ""
        path_part = line.split(":")[1] if len(line.split(":")) > 1 else ""
        skill_name = path_part.strip().split("/")[-2] if "/" in path_part else repo
        key = f"{author}/{skill_name}".lower()
        if key not in seen:
            seen.add(key)
            skills.append(
                SkillResult(
                    name=skill_name,
                    author=author,
                    source="github",
                    url=f"https://github.com/{author}/{repo}",
                )
            )
    return skills


def _search_skillsmp(query: str) -> list[SkillResult]:
    """Search SkillsMP via typed client (requires SKILLSMP_API_KEY)."""
    from mde.research.clients.skillsmp_client import SkillsMPClient
    from mde.research.clients.skillsmp_models import SkillSearchResponse

    client = SkillsMPClient()
    if not client.is_configured:
        return []
    result = client.search(query, limit=10)
    if not isinstance(result, SkillSearchResponse) or not result.data:
        return []
    return [
        SkillResult(
            name=s.name,
            author=s.author,
            source="skillsmp",
            stars=s.stars,
            description=s.description,
            url=s.skill_url,
        )
        for s in result.data.skills
    ]


def _extract_author(item: dict[str, str]) -> str:
    """Extract author from a skillfish result item."""
    author = item.get("author", "")
    if author:
        return author
    repo = item.get("repo", "")
    if "/" in repo:
        return repo.split("/")[0]
    return ""


def _search_skillfish(query: str) -> list[SkillResult]:
    """Search skillfish registry via mise-managed CLI.

    Note: skillfish search backend (mcpmarket.com) returns empty results
    as of 2026-03-25. Included for when the backend is fixed upstream.
    """
    skillfish_bin = shutil.which("skillfish")
    if not skillfish_bin:
        return []
    try:
        result = subprocess.run(
            [skillfish_bin, "search", query, "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []
    if not data.get("results"):
        return []
    return [
        SkillResult(
            name=item.get("name", ""),
            author=_extract_author(item),
            source="skillfish",
            description=item.get("description", ""),
            url=item.get("url", ""),
        )
        for item in data["results"]
        if item.get("name")
    ]


def _search_skillport_local(query: str) -> list[SkillResult]:
    """Search locally installed skills via skillport list.

    This searches the local inventory — useful for finding skills
    already installed that match the query.
    """
    skillport_bin = shutil.which("skillport")
    if not skillport_bin:
        return []
    try:
        result = subprocess.run(
            [skillport_bin, "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []
    skills: list[SkillResult] = []
    items = data if isinstance(data, list) else data.get("skills", [])
    for item in items:
        name = item.get("name", "")
        if query.lower() in name.lower() or query.lower() in item.get("description", "").lower():
            skills.append(
                SkillResult(
                    name=name,
                    author=item.get("author", ""),
                    source="skillport",
                    description=item.get("description", ""),
                    installed=True,
                )
            )
    return skills


def _get_installed_skills() -> set[str]:
    """Get names of locally installed skills."""
    installed: set[str] = set()
    for search_dir in [Path(".claude/skills"), Path(".agents/skills")]:
        if search_dir.exists():
            for skill_dir in search_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    installed.add(skill_dir.name)
    # Also check user-level skills
    user_skills = Path.home() / ".agents" / "skills"
    if user_skills.exists():
        for skill_dir in user_skills.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                installed.add(skill_dir.name)
    return installed


def discover_skills(query: str) -> DiscoveryResult:
    """Search all sources and return merged, ranked results.

    Sources searched (in order):
    1. skills.sh — largest open ecosystem, has install counts
    2. GitHub code search — deepest, finds niche/personal skills
    3. SkillsMP — 66K+ skills, requires API key
    4. skillfish — separate registry (backend intermittent)
    5. skillport — local inventory search
    """
    result = DiscoveryResult(query=query)
    installed = _get_installed_skills()
    result.installed_matches = [s for s in installed if query.lower() in s.lower()]

    from collections.abc import Callable

    sources: list[tuple[str, Callable[[str], list[SkillResult]]]] = [
        ("skills.sh", _search_skills_sh),
        ("github", _search_github),
        ("skillsmp", _search_skillsmp),
        ("skillfish", _search_skillfish),
        ("skillport", _search_skillport_local),
    ]

    for source_name, search_fn in sources:
        try:
            skills = search_fn(query)
            result.sources_searched.append(source_name)
            for skill in skills:
                skill.installed = skill.name in installed
            result.skills.extend(skills)
        except Exception as exc:  # noqa: BLE001
            result.sources_failed.append(f"{source_name}: {exc}")

    # De-duplicate by (name, author), keeping highest installs/stars
    seen: dict[str, SkillResult] = {}
    for skill in result.skills:
        key = f"{skill.author}/{skill.name}".lower()
        if key not in seen or skill.installs > seen[key].installs:
            seen[key] = skill
    result.skills = sorted(seen.values(), key=lambda s: s.sort_key)

    return result


def cli_main(args: list[str]) -> int:
    """CLI entry point for unified skill discovery."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Discover skills across all sources")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")

    parsed = parser.parse_args(args)
    result = discover_skills(parsed.query)

    if parsed.json_output:
        data = {
            "query": result.query,
            "sources_searched": result.sources_searched,
            "sources_failed": result.sources_failed,
            "installed_matches": result.installed_matches,
            "skills": [
                {
                    "name": s.name,
                    "author": s.author,
                    "source": s.source,
                    "installs": s.installs,
                    "stars": s.stars,
                    "description": s.description,
                    "url": s.url,
                    "installed": s.installed,
                }
                for s in result.skills
            ],
        }
        sys.stdout.write(json.dumps(data, indent=2))
        sys.stdout.write("\n")
        return 0

    sys.stderr.write(f"Skill Discovery: '{result.query}'\n")
    sys.stderr.write(f"Sources: {', '.join(result.sources_searched)}\n")
    if result.sources_failed:
        sys.stderr.write(f"Failed: {', '.join(result.sources_failed)}\n")
    if result.installed_matches:
        sys.stderr.write(f"Installed: {', '.join(result.installed_matches)}\n")
    sys.stderr.write("\n")

    if not result.skills:
        sys.stderr.write("No skills found.\n")
        return 0

    sys.stderr.write(f"Found {len(result.skills)} skills:\n\n")
    for i, skill in enumerate(result.skills, 1):
        marker = " [INSTALLED]" if skill.installed else ""
        metrics = []
        if skill.installs:
            metrics.append(f"{skill.installs} installs")
        if skill.stars:
            metrics.append(f"{skill.stars} stars")
        metrics_str = f" ({', '.join(metrics)})" if metrics else ""
        sys.stderr.write(
            f"  {i}. {skill.author}/{skill.name}{metrics_str} [{skill.source}]{marker}\n"
        )
        if skill.description:
            sys.stderr.write(f"     {skill.description[:80]}\n")

    return 0

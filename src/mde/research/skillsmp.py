"""SkillsMP skill search — CLI entry point using typed client.

Delegates to SkillsMPClient for all API calls. Works with typed models directly.
CLI: uv run mde-py research skill-search <query> [--ai] [--limit N] [--json]

API docs: https://skillsmp.com/docs/api
"""

from __future__ import annotations

import json
import sys

from mde.research.clients.skillsmp_models import (
    AISearchResponse,
    ErrorResponse,
    Skill,
    SkillSearchResponse,
)

__all__ = ["ai_search_typed", "cli_main", "search_typed"]


def search_typed(
    query: str,
    *,
    limit: int = 20,
    sort_by: str = "stars",
) -> SkillSearchResponse | ErrorResponse:
    """Keyword search via typed client. Returns typed response."""
    from mde.research.clients.skillsmp_client import SkillsMPClient

    client = SkillsMPClient()
    return client.search(query, limit=limit, sort_by=sort_by)


def ai_search_typed(query: str) -> AISearchResponse | ErrorResponse:
    """AI semantic search via typed client. Returns typed response."""
    from mde.research.clients.skillsmp_client import SkillsMPClient

    client = SkillsMPClient()
    return client.ai_search(query)


def _print_skills(skills: list[Skill], query: str) -> None:
    """Display keyword search results."""
    print(f"Found {len(skills)} skills for '{query}':\n")
    for i, skill in enumerate(skills, 1):
        print(f"  {i}. {skill.author}/{skill.name} ({skill.stars} stars)")
        if skill.description:
            print(f"     {skill.description[:80]}")


def _print_ai_results(results: list, query: str) -> None:
    """Display AI semantic search results."""
    print(f"Found {len(results)} skills for '{query}':\n")
    for i, item in enumerate(results, 1):
        print(f"  {i}. {item.filename} (score: {item.score:.3f})")


def cli_main(args: list[str] | None = None) -> int:
    """CLI entry point for skill search."""
    import argparse

    parser = argparse.ArgumentParser(description="Search SkillsMP marketplace")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--ai", action="store_true", help="Use AI semantic search")
    parser.add_argument("--limit", type=int, default=10, help="Results per page")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    parsed = parser.parse_args(args)

    if parsed.ai:
        result = ai_search_typed(parsed.query)
    else:
        result = search_typed(parsed.query, limit=parsed.limit)

    if parsed.json:
        print(json.dumps(result.model_dump(), indent=2))
        return 0 if result.success else 1

    if isinstance(result, ErrorResponse):
        err = result.error
        code = err.code if err else "?"
        msg = err.message if err else "Unknown error"
        print(f"Error [{code}]: {msg}", file=sys.stderr)
        return 1

    if isinstance(result, SkillSearchResponse) and result.data:
        if not result.data.skills:
            print(f"No skills found for '{parsed.query}'")
            return 0
        _print_skills(result.data.skills, parsed.query)
    elif isinstance(result, AISearchResponse) and result.data:
        if not result.data.data:
            print(f"No skills found for '{parsed.query}'")
            return 0
        _print_ai_results(result.data.data, parsed.query)
    else:
        print(f"No skills found for '{parsed.query}'")

    return 0

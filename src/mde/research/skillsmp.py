"""SkillsMP skill search — CLI entry point using typed client.

Delegates to SkillsMPClient for all API calls.
CLI: uv run mde-py research skill-search <query> [--ai] [--limit N] [--json]

API docs: https://skillsmp.com/docs/api
"""

from __future__ import annotations

import json
import sys

__all__ = ["ai_search", "cli_main", "search"]


def search(query: str, *, limit: int = 20, sort_by: str = "stars") -> dict:
    """Keyword search via typed client. Returns raw dict for backward compat."""
    from mde.research.clients.skillsmp_client import SkillsMPClient

    client = SkillsMPClient()
    result = client.search(query, limit=limit, sort_by=sort_by)
    return result.model_dump()


def ai_search(query: str) -> dict:
    """AI semantic search via typed client. Returns raw dict for backward compat."""
    from mde.research.clients.skillsmp_client import SkillsMPClient

    client = SkillsMPClient()
    result = client.ai_search(query)
    return result.model_dump()


def _print_skill_search(skills: list[dict], query: str) -> None:
    """Display keyword search results."""
    print(f"Found {len(skills)} skills for '{query}':\n")
    for i, skill in enumerate(skills, 1):
        author = skill.get("author", "?")
        name = skill.get("name", "?")
        stars = skill.get("stars", 0)
        desc = skill.get("description", "")[:80]
        print(f"  {i}. {author}/{name} ({stars} stars)")
        if desc:
            print(f"     {desc}")


def _print_ai_search(results: list[dict], query: str) -> None:
    """Display AI semantic search results."""
    print(f"Found {len(results)} skills for '{query}':\n")
    for i, item in enumerate(results, 1):
        filename = item.get("filename", "?")
        score = item.get("score", 0)
        print(f"  {i}. {filename} (score: {score:.3f})")


def cli_main(args: list[str] | None = None) -> int:
    """CLI entry point for skill search.

    Usage: uv run mde-py research skill-search <query> [--ai] [--limit N]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Search SkillsMP marketplace")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--ai", action="store_true", help="Use AI semantic search")
    parser.add_argument("--limit", type=int, default=10, help="Results per page")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    parsed = parser.parse_args(args)

    result = ai_search(parsed.query) if parsed.ai else search(parsed.query, limit=parsed.limit)

    if parsed.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("success") else 1

    if not result.get("success"):
        err = result.get("error") or {}
        code = err.get("code", "?")
        msg = err.get("message", "Unknown error")
        print(f"Error [{code}]: {msg}", file=sys.stderr)
        return 1

    data = result.get("data") or {}
    if parsed.ai:
        items = data.get("data", [])
        if not items:
            print(f"No skills found for '{parsed.query}'")
            return 0
        _print_ai_search(items, parsed.query)
    else:
        skills = data.get("skills", [])
        if not skills:
            print(f"No skills found for '{parsed.query}'")
            return 0
        _print_skill_search(skills, parsed.query)

    return 0

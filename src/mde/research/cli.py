"""CLI dispatcher for research subcommands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'research' subcommand and its children."""
    research_p = sub.add_parser("research", help="Research pipeline operations")
    research_sub = research_p.add_subparsers(dest="research_cmd")
    research_sub.add_parser("status", help="Show research pipeline status")
    research_sub.add_parser("score", help="Calculate current improvement score")
    research_sub.add_parser("catalog", help="Show source catalog summary")

    # skill-search subcommand — delegates to skillsmp module
    ss = research_sub.add_parser("skill-search", help="Search SkillsMP marketplace")
    ss.add_argument("query", help="Search query")
    ss.add_argument("--ai", action="store_true", help="Use AI semantic search")
    ss.add_argument("--limit", type=int, default=10, help="Results per page")
    ss.add_argument("--json", action="store_true", dest="json_output", help="Output raw JSON")


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct research subcommand handler."""
    cmd = getattr(args, "research_cmd", None)
    if cmd == "catalog":
        return _cmd_catalog()
    if cmd == "score":
        return _cmd_score()
    if cmd == "status":
        return _cmd_status()
    if cmd == "skill-search":
        return _cmd_skill_search(args)
    print("Usage: mde-py research {catalog|score|status|skill-search}", file=sys.stderr)
    return 1


def _cmd_catalog() -> int:
    from mde.research.catalog import read_catalog

    catalog_path = Path("docs/research/source-catalog.md")
    if not catalog_path.exists():
        print("No source catalog found.")
        return 1
    entries = read_catalog(catalog_path)
    reviewed = sum(1 for e in entries if e.status == "full-review")
    skimmed = sum(1 for e in entries if e.status == "skim")
    pending = sum(1 for e in entries if e.status == "not-reviewed")
    print(f"Source Catalog: {len(entries)} total")
    print(f"  Full review: {reviewed}")
    print(f"  Skim only:   {skimmed}")
    print(f"  Not reviewed: {pending}")
    return 0


def _cmd_score() -> int:
    import yaml

    from mde.research.score import ScoreCard, calculate_score

    # Try to load the most recent scorecard from the trail
    scorecards_dir = Path("docs/research/trail/scorecards")
    card = ScoreCard()
    source = "defaults"

    if scorecards_dir.exists():
        yamls = sorted(scorecards_dir.glob("*.yaml"), reverse=True)
        if yamls:
            try:
                data = yaml.safe_load(yamls[0].read_text())
                metrics = data.get("metrics", {})
                card = ScoreCard(
                    validation_pass_rate=metrics.get("validation_pass_rate", 0.0),
                    brew_mise_duplicates=metrics.get("brew_mise_duplicates", 0),
                    total_tools=metrics.get("total_tools", 1),
                    chezmoi_reproducible=metrics.get("chezmoi_reproducible", False),
                    test_coverage=metrics.get("test_coverage", 0.0),
                    lint_violations=metrics.get("lint_violations", 0),
                    stale_sources=metrics.get("stale_sources", 0),
                    total_sources=metrics.get("total_sources", 1),
                    findings_actionable_rate=metrics.get("findings_actionable_rate", 0.0),
                    agent_trigger_accuracy=metrics.get("agent_trigger_accuracy", 0.0),
                    context_efficiency=metrics.get("context_efficiency", 0.0),
                    rewrite_rate=metrics.get("rewrite_rate", 0.0),
                )
                source = yamls[0].name
            except (yaml.YAMLError, KeyError, TypeError):
                pass  # Fall back to defaults

    score = calculate_score(card)
    print(f"Improvement Score: {score:.3f} (from {source})")
    return 0


def _cmd_skill_search(args: argparse.Namespace) -> int:
    from mde.research.skillsmp import cli_main

    # Build args list for the skillsmp CLI
    cli_args = [args.query]
    if getattr(args, "ai", False):
        cli_args.append("--ai")
    if getattr(args, "json_output", False):
        cli_args.append("--json")
    cli_args.extend(["--limit", str(getattr(args, "limit", 10))])
    return cli_main(cli_args)


def _cmd_status() -> int:
    trail_dir = Path("docs/research/trail/findings")
    findings = list(trail_dir.glob("*.yaml")) if trail_dir.exists() else []
    print("Research Pipeline Status")
    print(f"  Findings: {len(findings)}")
    print(f"  Trail dir: {trail_dir}")
    return 0

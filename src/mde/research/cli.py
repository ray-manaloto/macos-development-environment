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


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct research subcommand handler."""
    cmd = getattr(args, "research_cmd", None)
    if cmd == "catalog":
        return _cmd_catalog()
    if cmd == "score":
        return _cmd_score()
    if cmd == "status":
        return _cmd_status()
    print("Usage: mde-py research {catalog|score|status}", file=sys.stderr)
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
    from mde.research.score import ScoreCard, calculate_score

    card = ScoreCard()
    score = calculate_score(card)
    print(f"Improvement Score: {score:.3f}")
    return 0


def _cmd_status() -> int:
    trail_dir = Path("docs/research/trail/findings")
    findings = list(trail_dir.glob("*.yaml")) if trail_dir.exists() else []
    print("Research Pipeline Status")
    print(f"  Findings: {len(findings)}")
    print(f"  Trail dir: {trail_dir}")
    return 0

"""Extract recurring patterns from signal sources.

Scans auto memory, remember files, retro snapshots, and quality gate
output for patterns worth promoting. Updates the pattern inventory
with recurrence counts and timestamps.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from mde.dream.models import DreamState, Pattern, PatternSource
from mde.dream.state import load_state, save_state
from mde.lib.paths import generated_dir, repo_root


def extract_patterns() -> DreamState:
    """Scan all signal sources and update pattern inventory.

    Returns the updated state with new/updated patterns.
    """
    state = load_state()

    sources: list[tuple[PatternSource, list[str]]] = [
        (PatternSource.AUTO_MEMORY, _scan_auto_memory()),
        (PatternSource.REMEMBER, _scan_remember()),
        (PatternSource.RETRO, _scan_retros()),
        (PatternSource.HOOK_FEEDBACK, _scan_hook_feedback()),
        (PatternSource.LEARNINGS, _scan_learnings()),
    ]

    now = datetime.now(tz=UTC)
    new_count = 0

    for source, raw_patterns in sources:
        for key in raw_patterns:
            if key in state.patterns:
                p = state.patterns[key]
                p.recurrence += 1
                p.last_seen = now
            else:
                state.patterns[key] = Pattern(
                    key=key,
                    description=_describe_pattern(key),
                    source=source,
                    first_seen=now,
                    last_seen=now,
                )
                new_count += 1

    state.last_extract = now
    state.extract_count += 1
    save_state(state)

    return state


def _scan_auto_memory() -> list[str]:
    """Extract pattern keys from auto memory feedback entries."""
    memory_dir = Path.home() / ".claude" / "projects"
    patterns: list[str] = []

    for md_file in memory_dir.rglob("memory/feedback_*.md"):
        try:
            text = md_file.read_text()
        except OSError:
            continue
        # Extract pattern from feedback filenames and content
        stem = md_file.stem.removeprefix("feedback_")
        patterns.append(f"feedback.{stem}")

        # Look for repeated correction language
        for match in re.finditer(
            r"(?:never|always|don'?t|must|avoid)\s+(\w[\w\s]{3,30})", text, re.IGNORECASE
        ):
            key = f"correction.{_slugify(match.group(1))}"
            patterns.append(key)

    return patterns


def _scan_remember() -> list[str]:
    """Extract pattern keys from remember plugin files."""
    remember_dir = generated_dir() / "remember"
    patterns: list[str] = []

    for name in ("now.md", "recent.md", "archive.md"):
        path = remember_dir / name
        if not path.exists():
            continue
        try:
            text = path.read_text()
        except OSError:
            continue

        # Count recurring topics by looking for repeated section headers
        min_recurrence = 2
        headers = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
        for header, count in Counter(headers).items():
            if count >= min_recurrence:
                patterns.append(f"remember.recurring.{_slugify(header)}")

        # Look for error/fix patterns (skip git commit message lines)
        for match in re.finditer(
            r"(?:fix|bug|error|broke|failed)[\s:]+(.{10,60})", text, re.IGNORECASE
        ):
            line = match.group(0)
            # Skip commit messages embedded in Stop hook entries
            if re.match(r"^[0-9a-f]{7,}\s+(?:fix|feat|docs|refactor)", line):
                continue
            # Skip lines that are clearly commit log format
            if "Recent commits:" in text[max(0, match.start() - 80) : match.start()]:
                continue
            patterns.append(f"remember.error.{_slugify(match.group(1)[:30])}")

    return patterns


def _scan_retros() -> list[str]:
    """Extract pattern keys from retro snapshots."""
    retro_dir = repo_root() / ".claude-octopus" / "retros"
    patterns: list[str] = []

    if not retro_dir.exists():
        return patterns

    import json

    for json_file in sorted(retro_dir.glob("*.json"))[-5:]:  # last 5 retros
        try:
            data = json.loads(json_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue

        # Extract hotspot patterns (files that keep changing)
        hotspots = data.get("top_hotspots", [])
        for hotspot in hotspots[:5]:
            if isinstance(hotspot, dict):
                path = hotspot.get("file", hotspot.get("path", ""))
            elif isinstance(hotspot, str):
                path = hotspot
            else:
                continue
            if path:
                patterns.append(f"retro.hotspot.{_slugify(Path(path).stem)}")

    return patterns


def _scan_hook_feedback() -> list[str]:
    """Extract pattern keys from hook block events in context snapshot."""
    snapshot_path = generated_dir() / "context-snapshot.json"
    patterns: list[str] = []

    if not snapshot_path.exists():
        return patterns

    import json

    try:
        data = json.loads(snapshot_path.read_text())
    except (OSError, json.JSONDecodeError):
        return patterns

    # Track which files keep appearing in uncommitted changes
    patterns.extend(
        f"uncommitted.{_slugify(Path(f).stem)}" for f in data.get("uncommitted_files", [])
    )

    return patterns


def _scan_learnings() -> list[str]:
    """Extract pattern keys from agent-written .generated/learnings/ files."""
    learnings_dir = generated_dir() / "learnings"
    patterns: list[str] = []

    if not learnings_dir.exists():
        return patterns

    for md_file in learnings_dir.glob("*.md"):
        try:
            text = md_file.read_text()
        except OSError:
            continue

        stem = md_file.stem.lower()  # patterns, errors, decisions

        # Count section headers as pattern signals
        headers = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
        patterns.extend(f"learning.{stem}.{_slugify(header[:40])}" for header in headers)

        # Extract correction language
        patterns.extend(
            f"learning.correction.{_slugify(match.group(1))}"
            for match in re.finditer(
                r"(?:never|always|don'?t|must|avoid)\s+(\w[\w\s]{3,30})", text, re.IGNORECASE
            )
        )

    return patterns


def _slugify(text: str) -> str:
    """Convert text to a valid pattern key segment."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    return slug.strip("_")[:40]


def _describe_pattern(key: str) -> str:
    """Generate a human-readable description from a pattern key."""
    parts = key.split(".")
    _min_parts = 2
    if len(parts) >= _min_parts:
        category = parts[0].replace("_", " ")
        detail = ".".join(parts[1:]).replace("_", " ")
        return f"{category}: {detail}"
    return key.replace("_", " ")

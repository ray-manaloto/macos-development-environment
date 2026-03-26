"""Persist agent transcripts from /private/tmp/ to repo before session end.

Called by Claude Code on PreCompact and Stop events. Scans for agent output
files in the temporary task directory, extracts the final assistant text from
each, and writes markdown files to docs/research/trail/deep-reviews/.

Always exits 0 (never blocks the session).
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)

_TMP_BASE = Path("/private/tmp/claude-501")
_MIN_AGENT_ID_LEN = 10
_MIN_TEXT_LEN = 100


def _repo_root() -> Path:
    """Return the git repository root, falling back to cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.bind(error=str(exc)).debug("repo_root_fallback")
    return Path.cwd()


def _find_task_dirs() -> list[Path]:
    """Find all task output directories under the tmp base."""
    dirs: list[Path] = []
    if not _TMP_BASE.exists():
        return dirs
    for project_dir in _TMP_BASE.iterdir():
        if not project_dir.is_dir():
            continue
        for session_dir in project_dir.iterdir():
            if not session_dir.is_dir():
                continue
            tasks_dir = session_dir / "tasks"
            if tasks_dir.is_dir():
                dirs.append(tasks_dir)
    return dirs


def _extract_final_text(output_file: Path) -> str | None:
    """Extract the last assistant text block from a JSONL agent output file."""
    results: list[str] = []
    try:
        with output_file.open() as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "assistant":
                        content = msg.get("message", {}).get("content", [])
                        results.extend(
                            c["text"]
                            for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        )
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        return None
    return results[-1] if results else None


def _already_persisted(dest_dir: Path, agent_id: str) -> bool:
    """Check if this agent's transcript was already saved."""
    return any(agent_id[:8] in f.name for f in dest_dir.iterdir())


def persist_transcripts() -> int:
    """Scan /private/tmp/ for agent transcripts and persist to repo."""
    with _tracer.start_as_current_span("mde.hook.persist_transcripts") as span:
        span.set_attribute("hook.event", "persist_transcripts")

        repo = _repo_root()
        dest_dir = repo / "docs" / "research" / "trail" / "deep-reviews" / "agent-transcripts"
        dest_dir.mkdir(parents=True, exist_ok=True)

        task_dirs = _find_task_dirs()
        if not task_dirs:
            logger.bind(hook="persist_transcripts").debug("no_task_dirs_found")
            return 0

        persisted = 0
        skipped = 0
        errors = 0
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        for tasks_dir in task_dirs:
            for output_file in tasks_dir.glob("*.output"):
                agent_id = output_file.stem
                # Skip non-agent files (background commands have short IDs)
                if len(agent_id) < _MIN_AGENT_ID_LEN:
                    continue

                if _already_persisted(dest_dir, agent_id):
                    skipped += 1
                    continue

                text = _extract_final_text(output_file)
                if not text or len(text) < _MIN_TEXT_LEN:
                    skipped += 1
                    continue

                dest_file = dest_dir / f"{today}-{agent_id[:8]}.md"
                try:
                    header = (
                        f"# Agent Transcript: {agent_id[:8]}\n\n"
                        f"**Date**: {today}\n"
                        f"**Source**: {output_file}\n\n---\n\n"
                    )
                    dest_file.write_text(header + text)
                    persisted += 1
                except OSError as exc:
                    errors += 1
                    logger.bind(error=str(exc), file=str(dest_file)).warning(
                        "persist_transcript_error"
                    )

        span.set_attribute("transcripts.persisted", persisted)
        span.set_attribute("transcripts.skipped", skipped)
        span.set_attribute("transcripts.errors", errors)

        if persisted > 0:
            logger.bind(
                count=persisted,
                dest=str(dest_dir.relative_to(repo)),
            ).info("transcripts_persisted")

        logger.bind(
            hook="persist_transcripts",
            persisted=persisted,
            skipped=skipped,
            errors=errors,
        ).info("hook_completed")
        return 0

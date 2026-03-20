"""Read and write the research source catalog (docs/research/source-catalog.md)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

STATUS_MAP = {"[ ]": "not-reviewed", "[~]": "skim", "[x]": "full-review"}
STATUS_REVERSE = {v: k for k, v in STATUS_MAP.items()}


@dataclass
class SourceEntry:
    """A single source entry in the research catalog."""

    url: str
    description: str
    category: str = "unknown"
    status: str = "not-reviewed"
    discovered_by: str = ""
    discovered_via: str = ""
    in_notebooklm: bool = False
    priority: str = "MEDIUM"


def read_catalog(path: Path) -> list[SourceEntry]:
    """Parse source entries from the catalog markdown."""
    entries: list[SourceEntry] = []
    text = path.read_text()
    pattern = re.compile(
        r"\|\s*\[([~x ])\]\s*\|([^|]*)\|([^|]*)\|",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        status_char = match.group(1)
        description = match.group(2).strip()
        url = match.group(3).strip()
        status = STATUS_MAP.get(f"[{status_char}]", "not-reviewed")
        entries.append(
            SourceEntry(url=url, description=description, status=status),
        )
    return entries


def add_entry(path: Path, entry: SourceEntry) -> None:
    """Append a source entry to the catalog before the Deep Review Queue."""
    status_md = STATUS_REVERSE.get(entry.status, "[ ]")
    line = (
        f"| {status_md} | {entry.description} | {entry.url} "
        f"| {entry.category} | Discovered by {entry.discovered_by} "
        f"via {entry.discovered_via} | {'Yes' if entry.in_notebooklm else 'No'} |\n"
    )
    content = path.read_text()
    marker = "## Deep Review Queue"
    if marker in content:
        content = content.replace(marker, f"{line}\n{marker}")
    else:
        content += f"\n{line}"
    path.write_text(content)

"""Tests for source catalog reader/writer."""

from __future__ import annotations

from pathlib import Path

from mde.research.catalog import SourceEntry, add_entry, read_catalog


def test_read_catalog_returns_entries(tmp_path: Path) -> None:
    """Verify read_catalog parses markdown table rows into SourceEntry objects."""
    catalog = tmp_path / "source-catalog.md"
    catalog.write_text(
        "| [~] | example repo | https://example.com | github-repo | Skim only | No |\n"
    )
    entries = read_catalog(catalog)
    assert len(entries) >= 1
    assert entries[0].url == "https://example.com"
    assert entries[0].status == "skim"


def test_add_entry_appends_to_catalog(tmp_path: Path) -> None:
    """Verify add_entry inserts a row before the Deep Review Queue marker."""
    catalog = tmp_path / "source-catalog.md"
    catalog.write_text("## Deep Review Queue\n\n")
    entry = SourceEntry(
        url="https://new-tool.dev",
        description="New tool",
        category="github-repo",
        status="not-reviewed",
        discovered_by="test-agent",
        discovered_via="unit test",
    )
    add_entry(catalog, entry)
    content = catalog.read_text()
    assert "https://new-tool.dev" in content
    assert "New tool" in content

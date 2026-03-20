"""Tests for provenance record creation and serialization."""

from __future__ import annotations

from pathlib import Path

from mde.research.provenance import ProvenanceRecord, load_records, save_record


def test_create_record() -> None:
    """ProvenanceRecord populates defaults for status, id, and timestamp."""
    record = ProvenanceRecord(
        source="https://example.com",
        agent="test-agent",
        finding_type="technique",
        confidence="confirmed",
        evidence="Found a better way to do X",
        tool_versions={"python": "3.14"},
    )
    assert record.source == "https://example.com"
    assert record.status == "discovered"
    assert record.timestamp is not None


def test_save_and_load_record(tmp_path: Path) -> None:
    """Round-trip a record through YAML save and load."""
    record = ProvenanceRecord(
        source="https://example.com",
        agent="test-agent",
        finding_type="tool",
        confidence="probable",
        evidence="Tool Y does what we need",
        tool_versions={"python": "3.14"},
    )
    save_record(tmp_path, record)
    loaded = load_records(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].source == "https://example.com"
    assert loaded[0].confidence == "probable"

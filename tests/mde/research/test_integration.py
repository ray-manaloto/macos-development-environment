"""Integration test for a minimal research cycle."""

from __future__ import annotations

from pathlib import Path

from mde.research.catalog import SourceEntry, add_entry, read_catalog
from mde.research.provenance import ProvenanceRecord, load_records, save_record
from mde.research.score import BinaryGate, ScoreCard, calculate_score, check_binary_gates


def test_full_research_cycle(tmp_path: Path) -> None:
    """Simulate: discover source -> create provenance -> check score."""
    # Step 1: Agent discovers a source
    catalog = tmp_path / "catalog.md"
    catalog.write_text("## Deep Review Queue\n")
    entry = SourceEntry(
        url="https://example.com/tool",
        description="A useful tool",
        category="github-repo",
        status="not-reviewed",
        discovered_by="test-agent",
        discovered_via="integration test",
    )
    add_entry(catalog, entry)

    # Step 2: Agent reviews and creates provenance record
    trail = tmp_path / "trail"
    record = ProvenanceRecord(
        source="https://example.com/tool",
        agent="test-agent",
        finding_type="tool",
        confidence="confirmed",
        evidence="This tool replaces our custom implementation",
        tool_versions={"python": "3.14.0"},
    )
    save_record(trail, record)

    # Step 3: Verify artifacts
    entries = read_catalog(catalog)
    assert any(e.url == "https://example.com/tool" for e in entries)
    records = load_records(trail)
    assert len(records) == 1
    assert records[0].confidence == "confirmed"

    # Step 4: Calculate score
    card = ScoreCard(validation_pass_rate=0.87, test_coverage=0.64)
    score = calculate_score(card)
    assert 0.0 <= score <= 1.0

    # Step 5: Check binary gates
    gates = [BinaryGate(name="tests_pass", passed=True)]
    assert check_binary_gates(gates) is True

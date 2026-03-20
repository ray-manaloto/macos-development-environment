"""Provenance records for research findings with YAML serialization."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml


@dataclass
class ProvenanceRecord:
    """A provenance record tracking the origin and confidence of a research finding."""

    source: str
    agent: str
    finding_type: str
    confidence: str
    evidence: str
    tool_versions: dict[str, str]
    status: str = "discovered"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )


def save_record(trail_dir: Path, record: ProvenanceRecord) -> Path:
    """Save a provenance record as a YAML file in *trail_dir*.

    Returns the path to the written file.
    """
    trail_dir.mkdir(parents=True, exist_ok=True)
    dest = trail_dir / f"{record.id}.yaml"
    data = {
        "source": record.source,
        "agent": record.agent,
        "finding_type": record.finding_type,
        "confidence": record.confidence,
        "evidence": record.evidence,
        "tool_versions": record.tool_versions,
        "status": record.status,
        "id": record.id,
        "timestamp": record.timestamp,
    }
    dest.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return dest


def load_records(trail_dir: Path) -> list[ProvenanceRecord]:
    """Load all provenance records from YAML files in *trail_dir*."""
    records: list[ProvenanceRecord] = []
    for path in sorted(trail_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        records.append(
            ProvenanceRecord(
                source=data["source"],
                agent=data["agent"],
                finding_type=data["finding_type"],
                confidence=data["confidence"],
                evidence=data["evidence"],
                tool_versions=data["tool_versions"],
                status=data.get("status", "discovered"),
                id=data["id"],
                timestamp=data["timestamp"],
            ),
        )
    return records

# Self-Improving Research System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the research pipeline (Layer 1 + Layer 2) that discovers, catalogs, and synthesizes improvements for the macos-development-environment project.

**Architecture:** Phase 0 deep-reviews all cataloged sources using `agent-fetch`. Phase 1 builds the research pipeline as `mde-py research` subcommands backed by existing tools (notebooklm CLI, agent-fetch, second-brain skill). No custom frameworks — assemble existing tools per the Primary Mandate.

**Tech Stack:** Python 3.14 (src/mde/), notebooklm CLI, agent-fetch (npx), yt-dlp, Obsidian CLI, existing Claude Code skills

**Spec:** `docs/superpowers/specs/2026-03-20-self-improving-research-system-design.md`
**Source Catalog:** `docs/research/source-catalog.md`

---

## Scope

This plan covers **Phase 0 (Deep Research) + Phase 1 Track B (Research Pipeline)** only.

**NOT in this plan (separate plans later):**
- Track A: Fix known issues (brew/mise duplicates, chezmoi reproducibility, devcontainer)
- Phase 2: Meta Layer (agent evolution), adversarial review, bidirectional sync
- Scheduling: ARIS pipeline integration, launchd outer scheduler

**Rationale:** The research pipeline must exist before the improvement engine can consume its output. Track A fixes are independent and can run in parallel via a separate plan/PR.

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `src/mde/research/__init__.py` | Research subpackage init |
| `src/mde/research/catalog.py` | Read/write/query `docs/research/source-catalog.md` |
| `src/mde/research/fetch.py` | Wrapper for `agent-fetch` + `notebooklm source add` |
| `src/mde/research/provenance.py` | Provenance record creation + YAML serialization |
| `src/mde/research/score.py` | Improvement score calculation (binary gates + magnitude) |
| `src/mde/research/cycle.py` | Research cycle orchestration (spawn agents, collect, dedup) |
| `tests/mde/research/test_catalog.py` | Catalog tests |
| `tests/mde/research/test_provenance.py` | Provenance record tests |
| `tests/mde/research/test_score.py` | Improvement score tests |
| `docs/research/trail/findings/.gitkeep` | Trail findings directory |
| `docs/research/trail/scorecards/.gitkeep` | Scorecard directory |

### Modified files

| File | Change |
|------|--------|
| `src/mde/cli.py` | Add `research` subcommand dispatcher |
| `pyproject.toml` | Add pyyaml dependency (for provenance records) |
| `.mise.toml` | Add `mde:research:*` tasks |

---

## Task 0: Deep Research Round (Pre-Implementation)

**This task is run by research agents, not coded.** It uses existing tools to re-review all high-priority sources with `agent-fetch` full content extraction.

### Files:
- Modify: `docs/research/source-catalog.md` (update status checkmarks)

- [ ] **Step 1: Spawn deep-review agents for top 10 sources**

Launch parallel agents, each using `agent-fetch` for one source:

```
For each source in the Deep Review Queue:
  1. npx agent-fetch "<url>" --json → full content
  2. Analyze: what does it do, key features, what to adopt, gaps
  3. Update source-catalog.md: change [ ] → [x] with notes
  4. Log any discovered URLs per Source Discovery Protocol (Section 4.4)
  5. Add HIGH priority sources to NotebookLM: notebooklm source add "<url>"
```

- [ ] **Step 2: Verify catalog coverage**

Run: `grep -c "\[x\]" docs/research/source-catalog.md`
Expected: >= 10 sources fully reviewed

- [ ] **Step 3: Commit updated catalog**

```
git add docs/research/source-catalog.md
git commit -m "research: deep review round 1 — N sources fully reviewed"
```

---

## Task 1: Research Subpackage Scaffold

### Files:
- Create: `src/mde/research/__init__.py`
- Create: `tests/mde/research/__init__.py`
- Create: `docs/research/trail/findings/.gitkeep`
- Create: `docs/research/trail/scorecards/.gitkeep`

- [ ] **Step 1: Create directory structure**

```python
# src/mde/research/__init__.py
"""Research pipeline for self-improving development environment."""

__all__: list[str] = []
```

```python
# tests/mde/research/__init__.py
```

- [ ] **Step 2: Create trail directories**

```
mkdir -p docs/research/trail/findings
mkdir -p docs/research/trail/scorecards
touch docs/research/trail/findings/.gitkeep
touch docs/research/trail/scorecards/.gitkeep
```

- [ ] **Step 3: Commit scaffold**

```
git add src/mde/research/ tests/mde/research/ docs/research/trail/
git commit -m "feat(research): scaffold research subpackage and trail directories"
```

---

## Task 2: Source Catalog Reader/Writer

### Files:
- Create: `src/mde/research/catalog.py`
- Test: `tests/mde/research/test_catalog.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/mde/research/test_catalog.py
"""Tests for source catalog reader/writer."""

from __future__ import annotations

from pathlib import Path

from mde.research.catalog import SourceEntry, read_catalog, add_entry


def test_read_catalog_returns_entries(tmp_path: Path) -> None:
    catalog = tmp_path / "source-catalog.md"
    catalog.write_text(
        "| [~] | example repo | https://example.com | github-repo | Skim only | No |\n"
    )
    entries = read_catalog(catalog)
    assert len(entries) >= 1
    assert entries[0].url == "https://example.com"
    assert entries[0].status == "skim"


def test_add_entry_appends_to_catalog(tmp_path: Path) -> None:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/mde/research/test_catalog.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mde.research.catalog'`

- [ ] **Step 3: Implement catalog module**

```python
# src/mde/research/catalog.py
"""Read and write the research source catalog (docs/research/source-catalog.md)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


STATUS_MAP = {"[ ]": "not-reviewed", "[~]": "skim", "[x]": "full-review"}
STATUS_REVERSE = {v: k for k, v in STATUS_MAP.items()}


@dataclass
class SourceEntry:
    url: str
    description: str
    category: str = "unknown"
    status: str = "not-reviewed"
    discovered_by: str = ""
    discovered_via: str = ""
    in_notebooklm: bool = False
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW, SKIP


def read_catalog(path: Path) -> list[SourceEntry]:
    """Parse source entries from the catalog markdown."""
    entries: list[SourceEntry] = []
    text = path.read_text()
    # Match table rows with status checkboxes and URLs
    pattern = re.compile(
        r"\|\s*\[([~x ])\]\s*\|([^|]*)\|([^|]*)\|", re.MULTILINE
    )
    for match in pattern.finditer(text):
        status_char = match.group(1)
        description = match.group(2).strip()
        url = match.group(3).strip()
        status = STATUS_MAP.get(f"[{status_char}]", "not-reviewed")
        entries.append(
            SourceEntry(url=url, description=description, status=status)
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
    # Insert before Deep Review Queue if it exists
    marker = "## Deep Review Queue"
    if marker in content:
        content = content.replace(marker, f"{line}\n{marker}")
    else:
        content += f"\n{line}"
    path.write_text(content)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/mde/research/test_catalog.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Run lint**

Run: `uv run ruff check src/mde/research/catalog.py tests/mde/research/test_catalog.py`
Expected: No violations

- [ ] **Step 6: Commit**

```
git add src/mde/research/catalog.py tests/mde/research/test_catalog.py
git commit -m "feat(research): add source catalog reader/writer"
```

---

## Task 3: Provenance Records

### Files:
- Create: `src/mde/research/provenance.py`
- Test: `tests/mde/research/test_provenance.py`
- Modify: `pyproject.toml` (add pyyaml if not already a dependency)

- [ ] **Step 1: Check if pyyaml is already available**

Run: `uv run python -c "import yaml; print(yaml.__version__)"`
If fails, add to pyproject.toml `[dependency-groups]`

- [ ] **Step 2: Write the failing test**

```python
# tests/mde/research/test_provenance.py
"""Tests for provenance record creation and serialization."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from mde.research.provenance import ProvenanceRecord, save_record, load_records


def test_create_record() -> None:
    record = ProvenanceRecord(
        source="https://example.com",
        agent="test-agent",
        finding_type="technique",
        confidence="confirmed",
        evidence="Found a better way to do X",
    )
    assert record.source == "https://example.com"
    assert record.status == "discovered"
    assert record.timestamp is not None


def test_save_and_load_record(tmp_path: Path) -> None:
    record = ProvenanceRecord(
        source="https://example.com",
        agent="test-agent",
        finding_type="tool",
        confidence="probable",
        evidence="Tool Y does what we need",
    )
    save_record(tmp_path, record)
    loaded = load_records(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].source == "https://example.com"
    assert loaded[0].confidence == "probable"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/mde/research/test_provenance.py -v`
Expected: FAIL

- [ ] **Step 4: Implement provenance module**

```python
# src/mde/research/provenance.py
"""Provenance records for research findings with YAML serialization."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml


def _get_tool_versions() -> dict[str, str]:
    """Capture current tool versions for provenance stamping."""
    versions: dict[str, str] = {}
    for cmd, key in [
        (["claude", "--version"], "claude_code"),
        (["mise", "--version"], "mise"),
        (["chezmoi", "--version"], "chezmoi"),
        (["python", "--version"], "python"),
        (["notebooklm", "--version"], "notebooklm"),
    ]:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            versions[key] = result.stdout.strip().split("\n")[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            versions[key] = "unknown"
    return versions


@dataclass
class ProvenanceRecord:
    source: str
    agent: str
    finding_type: str  # technique | tool | config_change | architecture | metric
    confidence: str  # confirmed | probable | speculative
    evidence: str
    status: str = "discovered"  # discovered | synthesized | applied | reverted
    id: str = field(default_factory=lambda: f"finding-{uuid4().hex[:12]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tool_versions: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tool_versions:
            self.tool_versions = _get_tool_versions()


def save_record(trail_dir: Path, record: ProvenanceRecord) -> Path:
    """Save a provenance record as YAML to the trail directory."""
    trail_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{record.id}.yaml"
    path = trail_dir / filename
    data = {
        "id": record.id,
        "timestamp": record.timestamp,
        "source": record.source,
        "agent": record.agent,
        "finding_type": record.finding_type,
        "confidence": record.confidence,
        "evidence": record.evidence,
        "status": record.status,
        "tool_versions": record.tool_versions,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return path


def load_records(trail_dir: Path) -> list[ProvenanceRecord]:
    """Load all provenance records from the trail directory."""
    records: list[ProvenanceRecord] = []
    if not trail_dir.exists():
        return records
    for path in sorted(trail_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        records.append(
            ProvenanceRecord(
                id=data["id"],
                timestamp=data["timestamp"],
                source=data["source"],
                agent=data["agent"],
                finding_type=data["finding_type"],
                confidence=data["confidence"],
                evidence=data["evidence"],
                status=data.get("status", "discovered"),
                tool_versions=data.get("tool_versions", {}),
            )
        )
    return records
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/mde/research/test_provenance.py -v`
Expected: 2 tests PASS

- [ ] **Step 6: Commit**

```
git add src/mde/research/provenance.py tests/mde/research/test_provenance.py
git commit -m "feat(research): add provenance record creation and YAML serialization"
```

---

## Task 4: Improvement Score Calculator

### Files:
- Create: `src/mde/research/score.py`
- Test: `tests/mde/research/test_score.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/mde/research/test_score.py
"""Tests for improvement score calculation."""

from __future__ import annotations

from mde.research.score import (
    BinaryGate,
    ScoreCard,
    check_binary_gates,
    calculate_score,
)


def test_binary_gates_all_pass() -> None:
    gates = [
        BinaryGate(name="no_regressions", passed=True),
        BinaryGate(name="validation_clean", passed=True),
        BinaryGate(name="tests_pass", passed=True),
    ]
    assert check_binary_gates(gates) is True


def test_binary_gates_one_fails() -> None:
    gates = [
        BinaryGate(name="no_regressions", passed=True),
        BinaryGate(name="validation_clean", passed=False),
        BinaryGate(name="tests_pass", passed=True),
    ]
    assert check_binary_gates(gates) is False


def test_calculate_score_returns_0_to_1() -> None:
    card = ScoreCard(
        validation_pass_rate=0.87,
        brew_mise_duplicates=3,
        total_tools=50,
        chezmoi_reproducible=False,
        test_coverage=0.64,
        lint_violations=8,
        stale_sources=14,
        total_sources=127,
        findings_actionable_rate=0.43,
        agent_trigger_accuracy=0.75,
        context_efficiency=0.5,
        rewrite_rate=0.1,
    )
    score = calculate_score(card)
    assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/mde/research/test_score.py -v`
Expected: FAIL

- [ ] **Step 3: Implement score module**

```python
# src/mde/research/score.py
"""Improvement score calculation with binary gates and magnitude metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BinaryGate:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ScoreCard:
    validation_pass_rate: float = 0.0
    brew_mise_duplicates: int = 0
    total_tools: int = 1
    chezmoi_reproducible: bool = False
    test_coverage: float = 0.0
    lint_violations: int = 0
    stale_sources: int = 0
    total_sources: int = 1
    findings_actionable_rate: float = 0.0
    agent_trigger_accuracy: float = 0.0
    context_efficiency: float = 0.0
    rewrite_rate: float = 0.0


def check_binary_gates(gates: list[BinaryGate]) -> bool:
    """All binary gates must pass. Any failure → revert."""
    return all(g.passed for g in gates)


def calculate_score(card: ScoreCard) -> float:
    """Calculate weighted composite improvement score (0.0-1.0)."""
    total_tools = max(card.total_tools, 1)
    total_sources = max(card.total_sources, 1)

    score = (
        card.validation_pass_rate * 0.15
        + (1 - card.brew_mise_duplicates / total_tools) * 0.10
        + (1.0 if card.chezmoi_reproducible else 0.0) * 0.15
        + card.test_coverage * 0.10
        + max(0, 1 - card.lint_violations / 100) * 0.05
        + (1 - card.stale_sources / total_sources) * 0.10
        + card.findings_actionable_rate * 0.10
        + card.agent_trigger_accuracy * 0.10
        + card.context_efficiency * 0.10
        + max(0, 1 - card.rewrite_rate) * 0.05
    )
    return max(0.0, min(1.0, score))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/research/test_score.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```
git add src/mde/research/score.py tests/mde/research/test_score.py
git commit -m "feat(research): add improvement score calculator with binary gates"
```

---

## Task 5: Wire CLI Subcommand

### Files:
- Modify: `src/mde/cli.py`
- Modify: `.mise.toml`

- [ ] **Step 1: Add research subcommand to CLI parser**

In `src/mde/cli.py`, add to `_build_parser()`:

```python
research_p = sub.add_parser("research", help="Research pipeline operations")
research_sub = research_p.add_subparsers(dest="research_cmd")
research_sub.add_parser("status", help="Show research pipeline status")
research_sub.add_parser("score", help="Calculate current improvement score")
research_sub.add_parser("catalog", help="Show source catalog summary")
```

Add dispatcher:

```python
def _cmd_research(args: argparse.Namespace) -> int:
    from mde.research import cli as research_cli
    return research_cli.dispatch(args)
```

- [ ] **Step 2: Create research CLI dispatcher**

```python
# src/mde/research/cli.py
"""CLI dispatcher for research subcommands."""

from __future__ import annotations

import argparse
from pathlib import Path

from mde.research.catalog import read_catalog
from mde.research.score import ScoreCard, calculate_score


def dispatch(args: argparse.Namespace) -> int:
    cmd = getattr(args, "research_cmd", None)
    if cmd == "catalog":
        return _cmd_catalog()
    if cmd == "score":
        return _cmd_score()
    if cmd == "status":
        return _cmd_status()
    print("Usage: mde-py research {catalog|score|status}")
    return 1


def _cmd_catalog() -> int:
    """Show source catalog summary."""
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
    """Calculate and display current improvement score."""
    # Baseline — actual metrics will come from validation output
    card = ScoreCard()
    score = calculate_score(card)
    print(f"Improvement Score: {score:.3f}")
    return 0


def _cmd_status() -> int:
    """Show research pipeline status."""
    trail_dir = Path("docs/research/trail/findings")
    findings = list(trail_dir.glob("*.yaml")) if trail_dir.exists() else []
    print(f"Research Pipeline Status")
    print(f"  Findings: {len(findings)}")
    print(f"  Trail dir: {trail_dir}")
    return 0
```

- [ ] **Step 3: Add mise tasks**

Add to `.mise.toml`:

```toml
[tasks."mde:research:catalog"]
description = "Show research source catalog summary"
run = "uv run mde-py research catalog"

[tasks."mde:research:score"]
description = "Calculate current improvement score"
run = "uv run mde-py research score"

[tasks."mde:research:status"]
description = "Show research pipeline status"
run = "uv run mde-py research status"
```

- [ ] **Step 4: Test CLI**

Run: `uv run mde-py research catalog`
Expected: Source catalog summary with counts

Run: `uv run mde-py research score`
Expected: `Improvement Score: 0.XXX`

- [ ] **Step 5: Commit**

```
git add src/mde/cli.py src/mde/research/cli.py .mise.toml
git commit -m "feat(research): wire research subcommands to mde-py CLI"
```

---

## Task 6: Baseline Scorecard Snapshot

### Files:
- Create: `docs/research/trail/scorecards/baseline.yaml`

- [ ] **Step 1: Run validation and capture baseline metrics**

```
uv run mde-py validate --all 2>&1 | tee /tmp/validate-output.txt
uv run pytest tests/mde/ --cov -q 2>&1 | tee /tmp/coverage-output.txt
uv run ruff check src/mde/ 2>&1 | tee /tmp/lint-output.txt
```

- [ ] **Step 2: Create baseline scorecard**

Parse outputs and create `docs/research/trail/scorecards/baseline.yaml` with actual values.

- [ ] **Step 3: Run improvement score against baseline**

Run: `uv run mde-py research score`
Record the baseline score — this is the number future cycles must exceed.

- [ ] **Step 4: Commit**

```
git add docs/research/trail/scorecards/baseline.yaml
git commit -m "feat(research): capture baseline improvement scorecard"
```

---

## Task 7: Integration Test — Full Research Cycle

### Files:
- Test: `tests/mde/research/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/mde/research/test_integration.py
"""Integration test for a minimal research cycle."""

from __future__ import annotations

from pathlib import Path

from mde.research.catalog import SourceEntry, add_entry, read_catalog
from mde.research.provenance import ProvenanceRecord, save_record, load_records
from mde.research.score import ScoreCard, calculate_score, check_binary_gates, BinaryGate


def test_full_research_cycle(tmp_path: Path) -> None:
    """Simulate: discover source → create provenance → check score."""
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
        tool_versions={"python": "3.14.0"},  # Skip live detection in test
    )
    save_record(trail, record)

    # Step 3: Verify the cycle produced artifacts
    entries = read_catalog(catalog)
    assert any(e.url == "https://example.com/tool" for e in entries)

    records = load_records(trail)
    assert len(records) == 1
    assert records[0].confidence == "confirmed"

    # Step 4: Calculate score (baseline)
    card = ScoreCard(validation_pass_rate=0.87, test_coverage=0.64)
    score = calculate_score(card)
    assert 0.0 <= score <= 1.0

    # Step 5: Check binary gates
    gates = [BinaryGate(name="tests_pass", passed=True)]
    assert check_binary_gates(gates) is True
```

- [ ] **Step 2: Run integration test**

Run: `uv run pytest tests/mde/research/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite to verify no regressions**

Run: `uv run pytest tests/mde/ -v`
Expected: All tests pass

- [ ] **Step 4: Run validation**

Run: `uv run mde-py validate --all`
Expected: 0 errors

- [ ] **Step 5: Commit**

```
git add tests/mde/research/test_integration.py
git commit -m "test(research): add integration test for full research cycle"
```

---

## Task 8: Create PR via /finishing-a-development-branch

- [ ] **Step 1: Verify all tests pass**

Run: `uv run pytest tests/mde/ -v && uv run ruff check src/mde/ && uv run mde-py validate --all`

- [ ] **Step 2: Use the finishing skill**

Invoke `/finishing-a-development-branch` to decide: merge, PR, or cleanup.

---

## Summary

| Task | What | Depends On |
|------|------|-----------|
| 0 | Deep research round (agents) | None |
| 1 | Scaffold subpackage | None |
| 2 | Catalog reader/writer | Task 1 |
| 3 | Provenance records | Task 1 |
| 4 | Improvement score | Task 1 |
| 5 | Wire CLI subcommand | Tasks 2-4 |
| 6 | Baseline scorecard | Task 5 |
| 7 | Integration test | Tasks 2-5 |
| 8 | Create PR | Task 7 |

**Task 0 can run in parallel** with Tasks 1-4 (agents research while we build the pipeline).

**Estimated scope:** Tasks 1-7 are ~30-45 minutes of implementation for an agent using subagent-driven-development. Task 0 depends on agent-fetch performance and source count.

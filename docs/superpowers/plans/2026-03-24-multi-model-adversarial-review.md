# Multi-Model Adversarial Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a multi-model adversarial review module to `src/mde/` that sends specs/code to Claude, Codex (GPT-5.4), and Gemini for independent review, then merges findings with a consensus gate.

**Architecture:** Two external CLI SDKs (`acodex` for Codex, `gemini-cli-sdk` for Gemini) provide typed Python access to external LLM providers. Claude reviews are native — dispatched via `.claude/agents/adversarial-reviewer.md` using the built-in Agent tool. A `ConsensusEngine` in `src/mde/domain/multi_model.py` handles the external SDKs (Codex + Gemini), while a Claude Code skill (`/adversarial-review`) orchestrates all three: it spawns the native Claude agent, calls the ConsensusEngine for external reviews, and merges all findings.

**Tech Stack:** acodex (Codex CLI SDK), gemini-cli-sdk (Gemini CLI SDK), native Claude Code agent definition + skill, Pydantic v2 models.

**How each reviewer runs:**
- **Claude:** Native agent definition at `.claude/agents/adversarial-reviewer.md` — dispatched via Agent tool, no SDK, no subprocess
- **Codex:** `acodex` Python SDK — typed API that spawns codex CLI internally via JSONL over stdin/stdout
- **Gemini:** `gemini-cli-sdk` Python SDK — typed API that spawns gemini CLI internally via subprocess

**Constraints:**
- Subscription-only auth — zero API keys, zero API expense
- External CLIs installed via mise (codex v0.116.0, gemini v0.34.0)
- Claude reviews are native agent dispatches — no SDK, no subprocess
- No new frameworks (no DSPy, no BAML) — just the two external SDKs + Pydantic
- Follow existing domain module patterns (see `src/mde/domain/honcho.py`)

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `.claude/agents/adversarial-reviewer.md` | Native Claude agent for adversarial review |
| Create | `src/mde/domain/multi_model.py` | External reviewer wrappers (Codex + Gemini via SDKs), ConsensusEngine |
| Create | `src/mde/domain/review_models.py` | Pydantic models: ReviewFinding, ReviewResult, ConsolidatedReview |
| Create | `src/mde/domain/review_prompts.py` | Adversarial review prompt templates (shared across all 3 models) |
| Create | `tests/mde/test_multi_model.py` | Unit tests (mocked SDKs) |
| Create | `tests/mde/test_review_models.py` | Model validation tests |
| Create | `docs/schemas/review-finding.schema.json` | JSON Schema for ReviewFinding (codegen source) |
| Modify | `src/mde/cli.py` | Add `review` subcommand (external reviewers only) |
| Modify | `pyproject.toml` | Add acodex + gemini-cli-sdk deps |

---

### Task 1: Add SDK Dependencies

**Files:**
- Modify: `pyproject.toml` (dependencies list)

- [ ] **Step 1: Add acodex and gemini-cli-sdk to pyproject.toml**

```toml
# Add to dependencies list after "honcho-ai>=2.0.0,<3.0.0":
"acodex>=0.116.0",
"gemini-cli-sdk>=0.1.0",
```

- [ ] **Step 2: Run uv sync to install**

Run: `uv sync`
Expected: Both packages install successfully.

- [ ] **Step 3: Verify imports work**

Run: `uv run python -c "import acodex; print(acodex.__version__)"`
Run: `uv run python -c "import gemini_cli_sdk; print('ok')"`
Expected: Version prints for acodex, "ok" for gemini-cli-sdk.

- [ ] **Step 4: Verify external CLIs are available**

Run: `which codex && codex --version`
Run: `which gemini && gemini --version`
Expected: codex 0.116.0, gemini 0.34.0
Note: Claude is not checked here — it's the native host. Claude reviews use `.claude/agents/adversarial-reviewer.md` dispatched via the Agent tool.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add acodex and gemini-cli-sdk dependencies for multi-model review"
```

---

### Task 2: Create ReviewFinding Pydantic Models

**Files:**
- Create: `docs/schemas/review-finding.schema.json`
- Create: `src/mde/domain/review_models.py` (generated from schema)
- Create: `tests/mde/test_review_models.py`

- [ ] **Step 1: Write the JSON Schema**

Create `docs/schemas/review-finding.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReviewFinding",
  "type": "object",
  "required": ["severity", "title", "description", "source_model"],
  "additionalProperties": false,
  "properties": {
    "severity": {
      "type": "string",
      "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
      "description": "Finding severity level."
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "description": "Short finding title."
    },
    "description": {
      "type": "string",
      "minLength": 1,
      "description": "Detailed finding description with evidence."
    },
    "source_model": {
      "type": "string",
      "description": "Which model produced this finding (codex, gemini, claude)."
    },
    "file_path": {
      "type": ["string", "null"],
      "default": null,
      "description": "File path referenced by finding, if any."
    },
    "line_range": {
      "type": ["string", "null"],
      "default": null,
      "description": "Line range (e.g. '42-58'), if applicable."
    },
    "recommendation": {
      "type": ["string", "null"],
      "default": null,
      "description": "Suggested fix or action."
    }
  }
}
```

- [ ] **Step 2: Generate Pydantic model from schema**

Run: `uv run datamodel-codegen --input docs/schemas/review-finding.schema.json --output generated/review_models.py --target-python-version 3.12`
Then: `cp generated/review_models.py src/mde/domain/review_models.py`

Manually add these models to the generated file:

```python
class ReviewResult(BaseModel):
    """Result from a single model's review."""
    model_config = ConfigDict(extra="forbid")
    model_name: str
    findings: list[ReviewFinding]
    raw_output: str = ""
    success: bool = True
    error: str | None = None

class ConsolidatedReview(BaseModel):
    """Merged findings from all models with consensus."""
    model_config = ConfigDict(extra="forbid")
    results: list[ReviewResult]
    consensus_findings: list[ReviewFinding]
    models_agreed: int
    models_total: int
    verdict: Literal["APPROVE", "REJECT", "NEEDS_REVISION"]
```

- [ ] **Step 3: Write model validation tests**

Create `tests/mde/test_review_models.py`:

```python
from mde.domain.review_models import ReviewFinding, ReviewResult, ConsolidatedReview

def test_review_finding_valid():
    f = ReviewFinding(severity="CRITICAL", title="Missing error handling",
                      description="No try/except", source_model="codex")
    assert f.severity == "CRITICAL"

def test_review_finding_invalid_severity():
    import pytest
    with pytest.raises(Exception):
        ReviewFinding(severity="BLOCKER", title="x", description="y", source_model="z")

def test_review_result_with_findings():
    f = ReviewFinding(severity="HIGH", title="t", description="d", source_model="gemini")
    r = ReviewResult(model_name="gemini", findings=[f])
    assert r.success is True
    assert len(r.findings) == 1

def test_consolidated_review_verdict():
    cr = ConsolidatedReview(
        results=[], consensus_findings=[],
        models_agreed=3, models_total=3, verdict="APPROVE"
    )
    assert cr.verdict == "APPROVE"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_review_models.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/schemas/review-finding.schema.json src/mde/domain/review_models.py tests/mde/test_review_models.py
git commit -m "feat: add ReviewFinding/ReviewResult/ConsolidatedReview Pydantic models"
```

---

### Task 3: Create Review Prompt Templates

**Files:**
- Create: `src/mde/domain/review_prompts.py`

- [ ] **Step 1: Write prompt templates**

```python
"""Adversarial review prompt templates for multi-model review."""

from __future__ import annotations

ADVERSARIAL_REVIEW_SYSTEM = """\
You are an adversarial technical reviewer. Your job is to FIND PROBLEMS, not praise.
Rate every finding as CRITICAL, HIGH, MEDIUM, or LOW.
Be specific: cite exact text, line numbers, or sections.
"""

ADVERSARIAL_REVIEW_PROMPT = """\
Review this technical spec/code for ALL problems:

1. Claims without evidence or verification
2. Missing error handling and failure modes
3. Tool/dependency compatibility issues (especially macOS ARM64)
4. Security concerns
5. Missing edge cases
6. Vague specifications that cannot be implemented as-is
7. Missing dependency version pins
8. Incorrect code (wrong imports, fabricated APIs, broken syntax)

For each finding, output a JSON object with these fields:
- severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
- title: short description (one line)
- description: detailed explanation with evidence
- file_path: file referenced (or null)
- line_range: lines referenced (or null)
- recommendation: suggested fix

Output ONLY a JSON array of finding objects. No prose before or after.

---
DOCUMENT TO REVIEW:

{content}
"""

def build_review_prompt(content: str) -> str:
    """Build the full review prompt with document content."""
    return ADVERSARIAL_REVIEW_PROMPT.format(content=content)
```

- [ ] **Step 2: Commit**

```bash
git add src/mde/domain/review_prompts.py
git commit -m "feat: add adversarial review prompt templates"
```

---

### Task 4: Create Multi-Model Review Module

**Files:**
- Create: `src/mde/domain/multi_model.py`
- Create: `tests/mde/test_multi_model.py`

- [ ] **Step 1: Write failing tests for reviewer wrappers**

Create `tests/mde/test_multi_model.py`:

```python
"""Tests for multi-model adversarial review module."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mde.domain.multi_model import (
    CodexReviewer,
    GeminiReviewer,
    ConsensusEngine,
    detect_available_reviewers,
)
from mde.domain.review_models import ReviewFinding, ReviewResult


SAMPLE_FINDINGS_JSON = json.dumps([
    {"severity": "HIGH", "title": "Missing validation",
     "description": "No input validation", "source_model": "test",
     "file_path": None, "line_range": None, "recommendation": "Add validation"}
])


class TestDetectAvailableReviewers:
    def test_detect_with_no_clis(self):
        with patch("shutil.which", return_value=None):
            reviewers = detect_available_reviewers()
            assert len(reviewers) == 0

    def test_detect_with_all_external_clis(self):
        with patch("shutil.which", return_value="/usr/bin/fake"):
            reviewers = detect_available_reviewers()
            # Only Codex + Gemini (Claude is native, not detected here)
            assert len(reviewers) == 2


class TestCodexReviewer:
    def test_parse_findings_from_json(self):
        reviewer = CodexReviewer()
        findings = reviewer._parse_findings(SAMPLE_FINDINGS_JSON, "codex")
        assert len(findings) == 1
        assert findings[0].severity == "HIGH"
        assert findings[0].source_model == "codex"

    def test_parse_findings_bad_json(self):
        reviewer = CodexReviewer()
        findings = reviewer._parse_findings("not json at all", "codex")
        assert len(findings) == 1
        assert findings[0].severity == "MEDIUM"
        assert "parse" in findings[0].title.lower()


class TestConsensusEngine:
    def test_deduplicate_findings(self):
        engine = ConsensusEngine(reviewers=[])
        f1 = ReviewFinding(severity="HIGH", title="Missing validation",
                          description="No input validation", source_model="codex")
        f2 = ReviewFinding(severity="HIGH", title="Missing validation",
                          description="Input not validated", source_model="gemini")
        f3 = ReviewFinding(severity="LOW", title="Style issue",
                          description="Inconsistent naming", source_model="claude")
        deduped = engine._deduplicate([f1, f2, f3])
        # f1 and f2 should merge (same title), f3 stays separate
        assert len(deduped) == 2

    def test_verdict_all_clean(self):
        engine = ConsensusEngine(reviewers=[])
        r1 = ReviewResult(model_name="codex", findings=[])
        r2 = ReviewResult(model_name="gemini", findings=[])
        verdict = engine._compute_verdict([r1, r2], [])
        assert verdict == "APPROVE"

    def test_verdict_critical_findings(self):
        engine = ConsensusEngine(reviewers=[])
        f = ReviewFinding(severity="CRITICAL", title="Broken",
                         description="Everything broken", source_model="codex")
        r1 = ReviewResult(model_name="codex", findings=[f])
        r2 = ReviewResult(model_name="gemini", findings=[f])
        verdict = engine._compute_verdict([r1, r2], [f])
        assert verdict == "REJECT"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_multi_model.py -v`
Expected: FAIL — `ImportError: cannot import name 'CodexReviewer' from 'mde.domain.multi_model'`

- [ ] **Step 3: Write the multi_model.py implementation**

Create `src/mde/domain/multi_model.py`:

```python
"""Multi-model adversarial review via subscription CLI SDKs.

Wraps acodex (Codex CLI), gemini-cli-sdk (Gemini CLI), and
claude-agent-sdk (Claude Code) behind a common Reviewer protocol.
ConsensusEngine fans out reviews and merges with 2/3 agreement.

All three SDKs use subscription auth — zero API keys required.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import ValidationError

from mde.domain.review_models import (
    ConsolidatedReview,
    ReviewFinding,
    ReviewResult,
)
from mde.domain.review_prompts import ADVERSARIAL_REVIEW_SYSTEM, build_review_prompt
from mde.log import logger

if TYPE_CHECKING:
    pass


@runtime_checkable
class Reviewer(Protocol):
    """Protocol for model-specific reviewers."""

    name: str

    async def review(self, content: str) -> ReviewResult: ...


class CodexReviewer:
    """Review via Codex CLI using acodex SDK."""

    name: str = "codex"

    async def review(self, content: str) -> ReviewResult:
        try:
            from acodex import AsyncCodex

            client = AsyncCodex()
            prompt = f"{ADVERSARIAL_REVIEW_SYSTEM}\n\n{build_review_prompt(content)}"
            thread = client.thread(instructions=prompt)
            result = await thread.run(prompt)
            raw = result.output if hasattr(result, "output") else str(result)
            findings = self._parse_findings(raw, self.name)
            return ReviewResult(model_name=self.name, findings=findings, raw_output=raw)
        except ImportError:
            return ReviewResult(
                model_name=self.name, findings=[], success=False,
                error="acodex not installed",
            )
        except Exception as e:  # noqa: BLE001
            logger.bind(reviewer=self.name).warning(f"review_failed: {e}")
            return ReviewResult(
                model_name=self.name, findings=[], success=False, error=str(e),
            )

    def _parse_findings(self, raw: str, source: str) -> list[ReviewFinding]:
        return _parse_json_findings(raw, source)


class GeminiReviewer:
    """Review via Gemini CLI using gemini-cli-sdk."""

    name: str = "gemini"

    async def review(self, content: str) -> ReviewResult:
        try:
            from gemini_cli_sdk import query, GeminiOptions

            prompt = f"{ADVERSARIAL_REVIEW_SYSTEM}\n\n{build_review_prompt(content)}"
            raw_parts: list[str] = []
            async for message in query(
                prompt=prompt,
                options=GeminiOptions(max_turns=1),
            ):
                if hasattr(message, "result"):
                    raw_parts.append(message.result)
                elif hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            raw_parts.append(block.text)
            raw = "\n".join(raw_parts)
            findings = self._parse_findings(raw, self.name)
            return ReviewResult(model_name=self.name, findings=findings, raw_output=raw)
        except ImportError:
            return ReviewResult(
                model_name=self.name, findings=[], success=False,
                error="gemini-cli-sdk not installed",
            )
        except Exception as e:  # noqa: BLE001
            logger.bind(reviewer=self.name).warning(f"review_failed: {e}")
            return ReviewResult(
                model_name=self.name, findings=[], success=False, error=str(e),
            )

    def _parse_findings(self, raw: str, source: str) -> list[ReviewFinding]:
        return _parse_json_findings(raw, source)


# NOTE: No ClaudeReviewer class needed.
# Claude reviews are dispatched natively via:
#   Agent(subagent_type="adversarial-reviewer", prompt=..., run_in_background=True)
# The agent definition lives at .claude/agents/adversarial-reviewer.md
# The ConsensusEngine only handles external reviewers (Codex + Gemini).
# Claude's findings are collected by the orchestrating skill/session and
# merged into the ConsolidatedReview alongside external results.


def _parse_json_findings(raw: str, source: str) -> list[ReviewFinding]:
    """Extract ReviewFinding objects from model output (expects JSON array)."""
    # Try to find a JSON array in the output
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        return [
            ReviewFinding(
                severity="MEDIUM",
                title="Could not parse structured findings",
                description=f"Model output did not contain a JSON array. Raw length: {len(raw)}",
                source_model=source,
            )
        ]
    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return [
            ReviewFinding(
                severity="MEDIUM",
                title="Could not parse JSON findings",
                description=f"JSON parse error on extracted array. Raw length: {len(raw)}",
                source_model=source,
            )
        ]

    findings: list[ReviewFinding] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item["source_model"] = source  # override with actual source
        try:
            findings.append(ReviewFinding.model_validate(item))
        except ValidationError:
            continue  # skip malformed findings
    return findings


def detect_available_reviewers() -> list[Reviewer]:
    """Detect which external CLI tools are installed and return available reviewers.

    Note: Claude is NOT included here — it's dispatched natively via the
    Agent tool from .claude/agents/adversarial-reviewer.md. This function
    only detects EXTERNAL reviewers (Codex, Gemini).
    """
    reviewers: list[Reviewer] = []
    if shutil.which("codex"):
        reviewers.append(CodexReviewer())
    if shutil.which("gemini"):
        reviewers.append(GeminiReviewer())
    return reviewers


class ConsensusEngine:
    """Fan-out review to multiple models, merge with consensus gate."""

    def __init__(self, reviewers: list[Reviewer]) -> None:
        self.reviewers = reviewers

    async def review(self, content: str) -> ConsolidatedReview:
        """Run all reviewers in parallel and merge findings."""
        results = await asyncio.gather(
            *(r.review(content) for r in self.reviewers),
            return_exceptions=True,
        )

        valid_results: list[ReviewResult] = []
        for r in results:
            if isinstance(r, ReviewResult):
                valid_results.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"reviewer_exception: {r}")

        all_findings = [f for r in valid_results for f in r.findings]
        consensus = self._deduplicate(all_findings)
        verdict = self._compute_verdict(valid_results, consensus)
        successful = [r for r in valid_results if r.success]

        return ConsolidatedReview(
            results=valid_results,
            consensus_findings=consensus,
            models_agreed=len(successful),
            models_total=len(self.reviewers),
            verdict=verdict,
        )

    def _deduplicate(self, findings: list[ReviewFinding]) -> list[ReviewFinding]:
        """Merge findings with similar titles (cross-model agreement)."""
        seen: dict[str, ReviewFinding] = {}
        for f in findings:
            key = f.title.lower().strip()
            if key in seen:
                existing = seen[key]
                # Escalate severity if multiple models agree
                severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                if severities.index(f.severity) > severities.index(existing.severity):
                    seen[key] = f
            else:
                seen[key] = f
        return list(seen.values())

    def _compute_verdict(
        self,
        results: list[ReviewResult],
        consensus: list[ReviewFinding],
    ) -> str:
        """Determine overall verdict based on findings."""
        critical = [f for f in consensus if f.severity == "CRITICAL"]
        high = [f for f in consensus if f.severity == "HIGH"]
        if critical:
            return "REJECT"
        if len(high) >= 3:
            return "REJECT"
        if high:
            return "NEEDS_REVISION"
        return "APPROVE"


async def run_adversarial_review(spec_path: Path) -> ConsolidatedReview:
    """Entry point: review a spec file with all available models."""
    content = spec_path.read_text()
    reviewers = detect_available_reviewers()
    if not reviewers:
        msg = "No review CLIs found. Install codex, gemini, or claude."
        raise RuntimeError(msg)
    engine = ConsensusEngine(reviewers)
    return await engine.review(content)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_multi_model.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/mde/domain/multi_model.py tests/mde/test_multi_model.py
git commit -m "feat: add multi-model adversarial review module with consensus engine"
```

---

### Task 5: Add CLI Subcommand

**Files:**
- Modify: `src/mde/cli.py`

- [ ] **Step 1: Add `review` subcommand to CLI parser**

In `src/mde/cli.py`, add after the last `add_parser` call:

```python
review_p = sub.add_parser("review", help="Adversarial multi-model review")
review_p.add_argument("spec", help="Path to spec/document to review")
review_p.add_argument("--models", default="all", help="Models to use: all, codex, gemini, claude")
```

- [ ] **Step 2: Add the command handler**

```python
def _cmd_review(args: argparse.Namespace) -> int:
    """Run adversarial multi-model review on a spec file."""
    import asyncio
    from pathlib import Path

    from mde.domain.multi_model import run_adversarial_review

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"File not found: {spec_path}", file=sys.stderr)
        return 1

    try:
        result = asyncio.run(run_adversarial_review(spec_path))
    except RuntimeError as e:
        print(f"Review failed: {e}", file=sys.stderr)
        return 1

    # Print results
    print(f"\n{'='*60}")
    print(f"ADVERSARIAL REVIEW: {result.verdict}")
    print(f"Models: {result.models_agreed}/{result.models_total} responded")
    print(f"{'='*60}\n")

    for finding in result.consensus_findings:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
        print(f"{icon.get(finding.severity, '⚪')} [{finding.severity}] {finding.title}")
        print(f"  Source: {finding.source_model}")
        print(f"  {finding.description[:200]}")
        if finding.recommendation:
            print(f"  → {finding.recommendation[:200]}")
        print()

    return 0 if result.verdict == "APPROVE" else 1
```

- [ ] **Step 3: Wire the subcommand**

Add `"review": _cmd_review` to the command dispatch dict.

- [ ] **Step 4: Test manually**

Run: `uv run mde-py review docs/research/trail/deep-reviews/youtube-agent-pipeline-synthesis.md`
Expected: Reviews fan out to available CLIs, findings printed, verdict shown.

- [ ] **Step 5: Commit**

```bash
git add src/mde/cli.py
git commit -m "feat: add 'review' CLI subcommand for multi-model adversarial review"
```

---

### Task 6: Integration Test

**Files:**
- Create: `tests/mde/test_review_integration.py`

- [ ] **Step 1: Write integration test with mocked SDKs**

```python
"""Integration test for multi-model review pipeline."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from mde.domain.multi_model import ConsensusEngine, CodexReviewer, GeminiReviewer


MOCK_FINDINGS = json.dumps([
    {"severity": "HIGH", "title": "Missing error handling",
     "description": "No try/except around network calls",
     "source_model": "test", "file_path": "src/main.py",
     "line_range": "42-58", "recommendation": "Add error handling"}
])


@pytest.mark.asyncio
async def test_full_review_pipeline():
    """Test complete fan-out → merge → verdict pipeline."""
    codex = CodexReviewer()
    gemini = GeminiReviewer()

    with patch.object(codex, "review", new_callable=AsyncMock) as mock_codex, \
         patch.object(gemini, "review", new_callable=AsyncMock) as mock_gemini:

        from mde.domain.review_models import ReviewFinding, ReviewResult

        finding = ReviewFinding(
            severity="HIGH", title="Missing error handling",
            description="No try/except", source_model="codex",
        )
        mock_codex.return_value = ReviewResult(
            model_name="codex", findings=[finding], raw_output=MOCK_FINDINGS,
        )
        mock_gemini.return_value = ReviewResult(
            model_name="gemini", findings=[finding], raw_output=MOCK_FINDINGS,
        )

        engine = ConsensusEngine(reviewers=[codex, gemini])
        result = await engine.review("test content")

        assert result.models_agreed == 2
        assert result.verdict == "NEEDS_REVISION"
        assert len(result.consensus_findings) >= 1
```

- [ ] **Step 2: Run integration test**

Run: `uv run pytest tests/mde/test_review_integration.py -v`
Expected: PASS.

- [ ] **Step 3: Run full quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/mde/test_review_integration.py
git commit -m "test: add integration test for multi-model review pipeline"
```

---

### Task 7: Documentation & Memory Update

**Files:**
- Modify: auto-memory files

- [ ] **Step 1: Update project memory**

Update `~/.claude/projects/.../memory/project_adversarial_review.md` to reflect implementation status.

- [ ] **Step 2: Run final quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "docs: update memory for multi-model adversarial review implementation"
```

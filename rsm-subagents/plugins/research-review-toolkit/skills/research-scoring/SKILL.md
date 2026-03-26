---
name: research-scoring
description: >
  This skill should be used when the user asks to "score research", "check research
  quality", "evaluate coverage", "measure improvement", "assess research completeness",
  or mentions research scoring, quality metrics, coverage gaps, improvement baseline,
  or research pipeline status.
---

# Research Scoring

## Scoring CLI

Use the built-in research CLI:
```bash
uv run mde-py research score    # Calculate improvement score
uv run mde-py research status   # Show pipeline status
uv run mde-py research catalog  # List source catalog entries
```

## Baseline

- Current improvement score baseline: **0.450**
- Future research cycles must exceed this threshold
- Score measures: source coverage, finding quality, provenance completeness

## Quality Dimensions

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Source coverage | 30% | Number and diversity of sources cataloged |
| Finding quality | 25% | Confidence levels, evidence citations |
| Provenance completeness | 20% | All required YAML fields populated |
| Synthesis depth | 15% | Deep reviews written, contradictions flagged |
| Actionability | 10% | Findings lead to concrete recommendations |

## Gap Analysis

To identify coverage gaps:
1. List all finding tags across provenance records
2. Compare against expected topic areas for the research domain
3. Flag topics with zero or low-confidence-only findings
4. Recommend specific sources or searches to fill gaps

## Rules

- Score must be calculated against the 0.450 baseline
- Report both absolute score and delta from baseline
- Identify top 3 gaps by impact potential
- Never inflate scores — conservative scoring prevents false confidence

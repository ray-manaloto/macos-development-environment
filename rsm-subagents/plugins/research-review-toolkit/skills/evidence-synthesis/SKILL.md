---
name: evidence-synthesis
description: >
  This skill should be used when the user asks to "synthesize findings", "combine
  research", "cross-reference sources", "summarize evidence", "write a deep review",
  or mentions evidence synthesis, finding consolidation, cross-source analysis, or
  research summarization.
---

# Evidence Synthesis

## Synthesis Workflow

1. **Gather** — Read relevant YAML provenance records from docs/research/trail/findings/
2. **Group** — Cluster findings by topic, tool, or theme
3. **Cross-reference** — Identify agreements, contradictions, and gaps across sources
4. **Synthesize** — Write deep review combining insights
5. **Score** — Assess confidence level of synthesized conclusions

## Progressive Disclosure Retrieval

Use 3-layer approach to avoid context bloat:
- **Layer 1 (index)**: file paths, titles, confidence — ~100 tokens/result
- **Layer 2 (context)**: finding summary, implication — ~500 tokens
- **Layer 3 (full detail)**: complete provenance record — ~500-1000 tokens

Search index FIRST, load context for relevant hits, full detail only when needed.

## Deep Review Format

Write to `docs/research/trail/deep-reviews/<topic>.md`:
```markdown
# <Topic> Deep Review

## Summary
<1-3 sentence executive summary>

## Key Findings
- Finding 1 (source: finding-<slug>.yaml, confidence: confirmed)
- Finding 2 (source: finding-<slug>.yaml, confidence: probable)

## Contradictions
<Where sources disagree and why>

## Gaps
<What remains unknown>

## Recommendations
<Actionable next steps>
```

## Rules

- Never load all findings into context at once — use progressive disclosure
- Always cite source provenance records by filename
- Flag contradictions explicitly — do not silently favor one source
- Write synthesis to disk immediately, not at session end

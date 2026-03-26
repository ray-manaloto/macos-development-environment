---
name: review-synthesis
description: >
  This skill should be used when the user asks to "summarize review findings",
  "prioritize fixes", "rank review issues", "combine reviewer feedback", "create
  action items from review", or mentions review synthesis, finding prioritization,
  severity ranking, or review result summarization.
---

# Review Synthesis

## Synthesis Workflow

1. **Collect** — Read structured JSON review results from all models
2. **Deduplicate** — Merge equivalent findings across models
3. **Rank** — Sort by severity weight (CRITICAL > SUGGESTION > NITPICK > GOOD)
4. **Group** — Categorize by type (security, performance, correctness, style)
5. **Prioritize** — Order by consensus strength and severity
6. **Report** — Generate actionable summary

## Severity Weights (from src/mde/consensus.py)

| Severity | Weight | Action |
|----------|--------|--------|
| CRITICAL | Highest | Must fix before merge |
| SUGGESTION | Medium | Should fix, may defer with justification |
| NITPICK | Low | Optional improvement |
| GOOD | Positive | Acknowledge good patterns |

## Output Format

Write synthesis to structured JSON:
```json
{
  "summary": {
    "total_findings": 0,
    "critical": 0,
    "suggestion": 0,
    "nitpick": 0,
    "good": 0,
    "consensus_rate": 0.0
  },
  "findings": [
    {
      "id": "finding-001",
      "severity": "critical",
      "category": "security",
      "description": "...",
      "models_agreeing": ["codex", "gemini", "claude"],
      "consensus": true,
      "suggested_fix": "..."
    }
  ],
  "action_items": [
    {
      "priority": 1,
      "finding_ids": ["finding-001"],
      "description": "...",
      "estimated_effort": "small|medium|large"
    }
  ]
}
```

## Rules

- Deduplicate before counting — same issue from 3 models is 1 finding
- Critical findings always generate action items
- Include consensus percentage for each finding
- Write results to JSON (not markdown) — models corrupt markdown less
- Never dismiss findings as "pre-existing" without verification
- Fix ALL findings — zero tolerance for skipped warnings

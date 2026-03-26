# Evaluation JSON Schema

## Top-Level Structure

```json
{
  "version": 1,
  "last_scanned": "2026-03-26T10:00:00Z",
  "total_screened": 828,
  "run_history": [
    {
      "timestamp": "2026-03-26T10:00:00Z",
      "marketplaces_scanned": ["claude-community", "claude-code-workflows"],
      "plugins_screened": 828,
      "finalists": 45,
      "verdicts": {"INSTALL": 8, "EXTRACT": 7, "REJECT": 30},
      "models_used": {"screener": "haiku", "reviewer": "opus", "codex": true},
      "goals_active": ["agent-improvement", "adversarial-review"]
    }
  ],
  "evaluations": {
    "plugin-name": {
      "name": "plugin-name",
      "marketplace": "claude-community",
      "source_url": "https://github.com/author/repo",
      "description": "Plugin description from marketplace",
      "last_evaluated": "2026-03-26T10:00:00Z",
      "verdict": "INSTALL",
      "confidence": 0.85,
      "goals_matched": ["agent-improvement", "memory-research"],
      "rationale": "Brief rationale for verdict",
      "components": {
        "skills": 3,
        "agents": 2,
        "commands": 1,
        "hooks": 0,
        "mcp": false,
        "shell_scripts": 0
      },
      "policy_violations": [],
      "codex_verdict": {
        "agrees": true,
        "rationale": "Codex assessment",
        "timestamp": "2026-03-26T10:05:00Z"
      },
      "overridden_by_user": false,
      "override_reason": null,
      "review_file": "docs/research/trail/deep-reviews/marketplace/plugin-name.md"
    }
  }
}
```

## Verdict Values

- `INSTALL` — No overlap, adds value, no policy conflicts. Install it.
- `EXTRACT` — Useful patterns but overlaps existing tooling. Document what to extract.
- `REJECT` — Conflicts with policies or low actual value. Document why.

## Confidence Scoring

0.0 to 1.0 scale based on:
- Policy compliance check (0.3 weight)
- Goal alignment strength (0.3 weight)
- Overlap with existing tooling (0.2 weight)
- Component quality assessment (0.2 weight)

## Multi-Model Verdict Merging

When codex review is enabled:
- Both agree INSTALL → INSTALL (high confidence)
- Both agree REJECT → REJECT (high confidence)
- Disagree → Flag for human review, include both rationales

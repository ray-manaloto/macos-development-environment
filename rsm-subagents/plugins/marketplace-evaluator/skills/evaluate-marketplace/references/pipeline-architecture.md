# Pipeline Architecture

## Flow Diagram

```
Discovery → Screen (haiku) → Deep Review (opus) → Codex Follow-Up → Persist → Summary
    ↓            ↓                  ↓                    ↓              ↓
marketplace  screening.json    review/*.md          codex verdicts   evaluations.json
   JSON      (HIGH/MED/LOW)    verdict.json         (agree/disagree)  source-catalog.md
```

## Error Handling

### Stage failures

- **Discovery fails** (marketplace JSON missing): Skip marketplace, log warning, continue
- **Screening agent fails**: Retry once with fresh context. If still fails, skip marketplace.
- **Deep review agent fails**: Log the plugin as SKIPPED with error. Do not block other reviews.
- **Codex review fails**: Mark codex_verdict as null, proceed without multi-model consensus.
- **Persist fails**: Write to fallback path `/tmp/marketplace-eval-emergency.json` and alert user.

### Incremental mode

When `--incremental` is set:
1. Read `last_scanned` from evaluations JSON
2. For each marketplace, check git log for commits since `last_scanned`
3. If marketplace has new commits, re-scan it fully (marketplace-level granularity)
4. Merge new results with existing evaluations (new verdicts override old for same plugin)

### Concurrency

- Screening: 1 agent per marketplace (sequential — each reads different JSON)
- Deep review: 4-6 parallel agents (each reviews one plugin independently)
- Codex review: Sequential (codex exec is single-threaded)

### Rate limits

- Agent spawning: Max 6 concurrent background agents
- Git cloning: Max 4 concurrent clones to avoid network saturation
- Codex exec: 1 at a time, 60s timeout per review

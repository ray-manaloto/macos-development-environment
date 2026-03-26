---
name: evaluate-marketplace
description: >
  This skill should be used when the user asks to "evaluate plugins", "scan marketplace",
  "audit community plugins", "find plugins for X", "screen marketplace", "plugin audit",
  "what plugins should we install", or "review marketplace plugins".
  Orchestrates full marketplace evaluation pipeline: screen all plugins, deep-review finalists,
  persist findings to repo, and optionally run multi-model review rounds.
argument-hint: "[--goals <goal-ids>] [--marketplace <name>] [--top <N>] [--incremental] [--models <screener:haiku,reviewer:opus>]"
allowed-tools: [Read, Write, Glob, Grep, Bash, Agent]
---

# Evaluate Marketplace Plugins

Orchestrate a full evaluation pipeline across all configured Claude Code plugin marketplaces.

## Configuration

Read goals and settings from `${CLAUDE_PLUGIN_ROOT}/config/goals.yaml`. All goals, models,
policies, and output paths are configurable — never hardcode them.

## Arguments

Parse `$ARGUMENTS` for filter options:

| Flag | Default | Effect |
|------|---------|--------|
| `--goals <ids>` | all | Comma-separated goal IDs from config |
| `--marketplace <name>` | all | Specific marketplace to scan |
| `--top <N>` | 10 | Max finalists per goal for deep review |
| `--incremental` | false | Only scan plugins updated since last run |
| `--models <overrides>` | from config | Override model for screener/reviewer/meta |
| `--skip-codex` | false | Skip the codex follow-up review round |

## Pipeline Stages

### Stage 1: Load State

1. Read `config/goals.yaml` for goals, models, policies
2. Read existing evaluations from the configured `evaluations_json` path
3. If `--incremental`, compute delta (new/updated plugins since last `last_scanned` timestamp)

### Stage 2: Discover Plugins

1. Find all marketplace JSON files: `~/.claude/plugins/marketplaces/*/. claude-plugin/marketplace.json`
2. Parse each marketplace and collect all plugins with name, description, source URL
3. If `--marketplace` specified, filter to that marketplace only
4. Log total plugin count

### Stage 3: Screen (Fast Pass)

1. Spawn **plugin-screener** agent (model from config, default haiku)
2. Pass the full plugin list and active goals
3. Agent classifies each plugin as HIGH/MEDIUM/LOW per goal
4. Collect HIGH-relevance plugins as finalists (capped at `--top` per goal, de-duplicated)

### Stage 4: Deep Review

1. For each finalist, spawn **plugin-deep-reviewer** agent (model from config, default opus)
2. Agent clones the repo to `/tmp/marketplace-eval/`, reads all files
3. Agent writes:
   - JSON verdict to evaluations file (INSTALL/EXTRACT/REJECT + rationale)
   - Detailed markdown review to `reviews_dir/<plugin-name>.md`
4. Run reviews in parallel batches (4-6 concurrent agents)

### Stage 5: Multi-Model Follow-Up (if enabled)

1. If `codex_reviewer: true` in config and `--skip-codex` not set:
   - For each INSTALL verdict, run `codex exec` with the review markdown as input
   - Codex provides independent assessment — agree/disagree with rationale
   - Append codex verdict to the evaluation JSON entry
2. Merge multi-model verdicts: flag disagreements for human review

### Stage 6: Persist Results

1. Write updated evaluations JSON to configured path
2. Write/update detailed review markdown files
3. Update source catalog with new plugin URLs
4. Write run metadata (timestamp, plugins scanned, verdicts, model versions)

### Stage 7: Summary

Present a summary table:

```
Marketplace Evaluation Complete
================================
Screened: 828 plugins across 5 marketplaces
Finalists: 45 (deep-reviewed)
Verdicts: 8 INSTALL, 7 EXTRACT, 30 REJECT
Multi-model disagreements: 2 (flagged for human review)
New since last scan: 12 plugins

INSTALL recommendations:
| Plugin | Goals | Confidence | Codex Agrees |
|--------|-------|------------|--------------|
```

## Output Paths

All paths read from `config/goals.yaml`:
- Evaluations: `docs/research/trail/findings/marketplace-evaluations.json`
- Reviews: `docs/research/trail/deep-reviews/marketplace/<plugin-name>.md`
- Meta-learning: `docs/research/trail/findings/evaluator-meta-learning.json`
- Source catalog: `docs/research/source-catalog.md`

## Additional Resources

### Reference Files

- **`references/evaluation-schema.md`** — JSON schema for evaluation entries
- **`references/pipeline-architecture.md`** — Detailed pipeline flow and error handling

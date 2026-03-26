---
name: debate-orchestration
description: >
  This skill should be used when the user asks to "run a multi-model review", "debate
  code changes", "invoke reviewd", "get multiple model opinions", "run adversarial
  review", or mentions multi-model review, debate orchestration, reviewd CLI, codex
  review, gemini review, or adversarial code analysis.
---

# Debate Orchestration

## Multi-Model Review via reviewd

The reviewd CLI (>=0.6.0) orchestrates reviews across subscription-based LLM CLIs.

### CLI Invocation Patterns

```bash
# Run reviewd with default model config
reviewd review --diff <diff-file> --config reviewd.toml

# Individual model CLIs (subscription auth, zero API keys)
codex exec "Review this diff for issues: $(cat diff.txt)"
echo "Review this diff for issues: $(cat diff.txt)" | gemini -p
claude --print "Review this diff for issues: $(cat diff.txt)"
```

### Review Workflow

1. **Prepare** — Generate diff: `git diff main...HEAD > /tmp/review-diff.txt`
2. **Distribute** — Send diff to each model CLI
3. **Collect** — Parse structured JSON review results from each model
4. **Validate** — Check debate integrity rules before consensus
5. **Forward** — Pass validated results to consensus-validation skill

### Model Configuration

All models use subscription auth (zero API keys):
- **codex**: `codex exec` or `codex review` — OpenAI subscription
- **gemini**: `gemini -p` or stdin pipe — Google subscription
- **claude**: `claude --print` — Anthropic subscription

### Debate Integrity Rules (from claude-octopus)

Before accepting review results, verify:
- No circular reasoning between models
- No severity inflation (escalating without evidence)
- No rubber-stamping (all models agreeing without analysis)
- Each model provides independent evidence for findings

## Rules

- All LLM calls go through subscription CLIs — never use API keys
- Never improvise CLI flags — use exact syntax documented above
- Parse review output as structured JSON, not free text
- Validate debate integrity before forwarding to consensus
- Write raw review results to JSON files for audit trail

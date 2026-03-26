---
name: notebooklm-integration
description: >
  This skill should be used when the user asks to "ingest into NotebookLM", "query
  NotebookLM", "add sources to notebook", "cross-source synthesis", "check stale
  sources", or mentions NotebookLM, notebook integration, source ingestion, or
  knowledge consolidation.
---

# NotebookLM Integration

## CLI Tool

Use `notebooklm` CLI only (teng-lin/notebooklm-py):
- Auth config at `$NOTEBOOKLM_HOME`
- One notebook per research DOMAIN, not per session

## Commands

```bash
# Add a file or URL as a source
notebooklm source add <file-or-url>

# Add broad topic research
notebooklm source add-research "query"

# Query with citations
notebooklm ask "question" --citations

# Find outdated sources
notebooklm source stale
```

## Consolidation Flow

1. Agent writes findings to repo files (YAML provenance or markdown deep reviews)
2. Consolidation step ingests into NotebookLM: `notebooklm source add <file>`
3. Cross-source synthesis: `notebooklm ask --citations`

## Notebook Organization

| Domain | Notebook | Purpose |
|--------|----------|---------|
| Research pipeline | research-pipeline | Source discovery, provenance, scoring |
| Multi-model review | autonomous-review | reviewd, consensus, debate integrity |
| Tool ecosystem | tool-ecosystem | mise, chezmoi, hk, devcontainer |

## Rules

- Use `notebooklm` CLI only — never build custom NotebookLM tooling
- One notebook per domain — do not create per-session notebooks
- Always use `--citations` when querying for synthesis
- Check `notebooklm source stale` periodically to refresh outdated sources
- Ingest YAML provenance records, not raw markdown notes

# Second-Brain Integration Policy

- NotebookLM: one notebook per research DOMAIN, not per session
  - Use `notebooklm source add <file-or-url>` for ingestion
  - Use `notebooklm ask "question" --citations` for cross-source synthesis
  - Use `notebooklm source add-research "query"` for broad topic surveys
  - Use `notebooklm source stale` to find outdated sources
- Obsidian vault: GTD/Zettelkasten for long-term knowledge
- /second-brain skill: capture -> process-inbox -> daily-plan -> closeout
- Consolidation flow:
  1. Agent writes findings to repo files (YAML provenance or markdown deep reviews)
  2. Consolidation step ingests into NotebookLM: `notebooklm source add <file>`
  3. Cross-source synthesis: `notebooklm ask --citations`

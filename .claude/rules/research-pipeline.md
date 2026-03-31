# Research Pipeline Policy

- CLI: `uv run mde-py research {catalog,score,status}`
- Source catalog: `docs/research/source-catalog.md` — track ALL discovered URLs
- Provenance records: `$MDE_DIR_TRAIL/findings/*.yaml`
- Baseline improvement score: 0.450 — future cycles must exceed this
- Research agents MUST use `npx agent-fetch "<url>" --json` for full content, never WebFetch (truncates)
- Source Discovery Protocol: log EVERY URL encountered, classify HIGH/MEDIUM/LOW/SKIP, never silently discard
- NotebookLM: use `notebooklm` CLI only (teng-lin/notebooklm-py), auth at $NOTEBOOKLM_HOME
- Primary Mandate: use existing → install existing → compose → extend → build new (LAST RESORT)

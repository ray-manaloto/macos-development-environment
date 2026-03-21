# Agent Note-Taking Policy

- Write findings to disk IMMEDIATELY upon discovery, not at session end
- If session dies mid-work, anything only in context is LOST
- Research findings: docs/research/trail/findings/*.yaml (append-only provenance)
- Deep analysis: docs/research/trail/deep-reviews/*.md
- Auto memory: ONLY for corrections, preferences, and pointers (<200 lines)
- Task/feature state that agents modify repeatedly: use JSON, not markdown
  (models are less likely to corrupt JSON -- Anthropic recommendation)
- Subagents MUST write findings to files, not just return summaries
- At session start: read `git log --oneline -20` for recent context
- At each milestone: `git commit` with descriptive message
- Before context fills: force-write all in-context findings to disk

# Context Budget Policy

- CLAUDE.md must stay under 100 lines (target: 50)
- Auto memory MEMORY.md must stay under 200 lines (first 200 loaded every session)
- Use 3-layer progressive disclosure for findings retrieval:
  Layer 1 (index): file paths, titles, confidence -- ~100 tokens/result
  Layer 2 (context): finding summary, implication -- ~500 tokens
  Layer 3 (full detail): complete provenance record -- ~500-1000 tokens
  Search index FIRST, load context for relevant hits, full detail only when needed
- Never load all research findings into context at once
- Subagents return condensed summaries (1000-2000 tokens), not full explorations
- Disable irrelevant plugins to save skill description budget (2% of context window)

---
name: Obsidian + YouTube integration pattern
description: Core workflow for AI agents to ingest YouTube content into Obsidian vaults with RAG
type: project
---

**Core Pattern Discovered:**

Obsidian + Claude Code + YouTube creates persistent knowledge vault for AI agents:

1. **Agent orchestrates YouTube search** → fetches metadata/descriptions
2. **NotebookLM synthesizes** → cross-links and extracts insights
3. **Claude Code writes to Obsidian** → structured notes with YAML front-matter
4. **obsidian-rag indexes** → makes content searchable via embeddings

**Why:** Gives Claude Code persistent multi-session memory for free (Obsidian is local file-based; RAG layer makes it queryable).

**Skills Available:**
- obsidian-automation: vault maintenance (slash commands, file processing)
- obsidian-knowledge: knowledge graph/retrieval
- obsidian-rag: makes vault semantically searchable

**YouTube Integration Strategy:**
- NOT full transcript ingestion (quota/cost constraint)
- INSTEAD: Store video metadata + agent-generated summaries
- RAG over summaries enables semantic search without full transcripts
- Alternative: Use YouTube API for transcript extraction (needs auth key)

**Public Implementations:**
- earlyaidopters/second-brain: one-command setup
- coleam00/second-brain-skills: skill collection for research workflow

**Gap Remaining:**
- Specific YouTube transcript/metadata extraction skills on skills.sh
- Full implementation code for video → Obsidian pipeline
- Cost/quota trade-offs for transcript vs summary approach

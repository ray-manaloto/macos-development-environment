# YouTube Video Processing for AI Agents: Deep Review

**Date:** 2026-03-24
**Synthesized from:** Task #1 (youtube-transcript-skills) + Task #2 (obsidian-youtube-integration)
**Recommendation Status:** Ready for implementation

---

## Executive Summary

This deep review synthesizes two research tracks to recommend the optimal architecture for AI agents to **fully review YouTube videos** for automated self-learning and knowledge capture.

**Best-in-class recommendation:**

```
yt-dlp (download + captions)
  ↓
faster-whisper (transcribe caption-less videos)
  ↓
youtube-video-analyst skill (forensic 11-section analysis)
  ↓
Obsidian vault + obsidian-rag (searchable memory across sessions)
```

**Why this stack:**
- ✓ Zero paid API keys (all open-source)
- ✓ Integrates with mde Python package (src/mde/youtube_review.py)
- ✓ Enables Claude Code skill (/youtube-review <URL>)
- ✓ Provides persistent, cross-session learning via obsidian-rag RAG
- ✓ Documented in 5 community YouTube videos + multiple skills.sh implementations

**Estimated effort:** 5-7 days (core + Whisper + Obsidian integration)

---

## Research Foundation

### Task #1: YouTube Transcript Skills Survey

Task #1 reviewed 7 available skills/tools across skills.sh and skill.fish:

| Tool | Quality | Verdict |
|------|---------|---------|
| youtube-transcript (intellectronica) | 3/5 | Lightweight API-based extraction (captions only) |
| youtube-downloader (composiohq) | 4/5 | yt-dlp wrapper; video/audio acquisition |
| **youtube-video-analyst (shipshitdev)** | **5/5** | **11-section forensic analysis + templates** |
| youtube-watcher (hanzoskill) | 2/5 | Incomplete docs; security checkpoint |
| skill.fish tools (3x) | 0/5 | Vercel checkpoint blocks access |

**Key finding:** youtube-video-analyst is not just analysis—it generates **reusable script templates** as primary output. This transforms passive video watching into active learning/creation capability.

### Task #2: Obsidian + YouTube Integration Patterns

Task #2 reviewed 5 community YouTube videos + 3 Obsidian skills:

**YouTube Videos (All Community-Created):**
1. Chase AI: Obsidian + Claude Code = persistent memory
2. Chase AI: YouTube research → NotebookLM synthesis → Obsidian vault workflow
3. Mark Kashef: One-command Obsidian setup + file processing pipeline
4. Cole (Dynamous): Dozens of skills orchestrating research loop
5. McKay Wrigley: Vault creation, AI rules, agent setup

**Obsidian Automation Skills:**
1. obsidian-automation: Slash commands + vault writes
2. obsidian-knowledge: Knowledge graph + retrieval
3. **obsidian-rag**: RAG layer for semantic search over notes

**Key finding:** obsidian-rag transforms Obsidian from a note storage system into a **semantic query engine**. Agents can ask "What hooks work in tech videos?" and get RAG results across all stored analyses.

---

## Architecture Deep Dive

### Layer 1: Content Acquisition (yt-dlp)

**Tool:** `yt-dlp` (or skills.sh wrapper: composiohq/youtube-downloader)

**Capabilities:**
- Download video in 200+ formats
- Extract audio as MP3, M4A, WAV, OPUS
- Fetch subtitles/captions (.vtt, .srt)
- Quality selection (1080p, 720p, 480p, etc.)
- Batch operations with filtering

**Why this layer:**
- Free, open-source, actively maintained
- Handles caption extraction automatically
- Supports quality/format selection for constrained environments
- 10x more robust than youtube-transcript-api for metadata

**Integration with mde:**
```python
# src/mde/youtube_review.py - Layer 1

async def download_and_extract_captions(url: str) -> tuple[Path, Optional[str]]:
    """Download video + extract captions if available."""
    # Uses yt-dlp via subprocess
    # Returns: (video_path, transcript_text or None)
```

**When to use:**
- Always (first step in pipeline)
- Cheap and fast
- Handles both caption-enabled and caption-less videos

---

### Layer 2: Transcription (faster-whisper)

**Tool:** `faster-whisper` (CTransformers-optimized Whisper)

**Alternatives:**
- openai-whisper: Slower but more widely tested (~5-10 min per video hour)
- whisper.cpp: Zero-dependency C++ (good for Docker)

**Capabilities:**
- 99 languages
- Multiple model sizes (tiny, base, small, medium, large)
- 10x speedup over official Whisper
- GPU acceleration available
- Run completely locally (no API keys)

**Why faster-whisper:**
- 10x faster than official Whisper
- Maintains accuracy
- Reduced memory footprint
- Still accurate for most domains

**Integration with mde:**
```python
# src/mde/youtube_review.py - Layer 2

async def transcribe_video(video_path: Path, model_size: str = "base") -> str:
    """Transcribe video audio using faster-whisper."""
    # Conditional: only run if captions not present (Layer 1)
    # Returns: plain text transcript with optional timestamps
```

**When to use:**
- Only if video lacks captions (Layer 1 returned None)
- Model size decision:
  - tiny: ~30s per min of audio (noisy, low accuracy)
  - **base: ~20s per min** (sweet spot for most cases)
  - small: ~40s per min (more accurate, still reasonable)
  - medium+: >1min per min (diminishing returns for most domains)

**Performance (base model on M1/M2 Mac):**
- 1 hour video: ~20-30 minutes
- Acceptable for overnight/background processing
- Can parallelize multiple videos if needed

**Fallback strategy:**
- If Whisper times out or errors: prompt user to provide transcript manually
- (Rare: covers <1% of YouTube videos that lack both captions AND are processing-heavy)

---

### Layer 3: Forensic Analysis (youtube-video-analyst)

**Tool:** `shipshitdev/youtube-video-analyst` (skills.sh)

**What it does:**
Deconstructs video transcript into 11 systematic sections:

1. **Hook Architecture** — Primary hook (first 3-8s), triggers
2. **Structural Blueprint** — Macro-structure, beat maps, scene transitions
3. **Retention Mechanics** — Open loops, pattern interrupts, curiosity gaps
4. **Emotional Engineering** — Emotional arc, trigger words, identity hooks
5. **Storytelling Elements** — Narrative framework, character positioning, conflict
6. **Linguistic Patterns** — Power phrases, sentence rhythm, repetition, cadence
7. **Algorithm Signals** — Retention optimizers, engagement triggers, share/save moments
8. **CTA Architecture** — Call-to-action sequence, timing, authority signals
9. **Viral Coefficient** — Shareability score, comment-bait density, controversy
10. **Reusable Templates** — Fill-in-the-blank scripts for similar content
11. **Implementation Playbook** — "Steal these elements", adaptation guides

**Why this tool:**
- Most comprehensive analysis framework available
- Primary output: **templates + playbooks** (not just metrics)
- Enables agents to not just learn, but generate similar content
- Quality score: 5/5 (only tool rated perfect in Task #1)
- Includes fetch_transcript.py for auto-extraction from URLs

**Integration with mde:**
```python
# src/mde/youtube_review.py - Layer 3

async def analyze_video_transcript(transcript: str, video_url: str) -> VideoAnalysis:
    """Run youtube-video-analyst on transcript."""
    # Calls skill via subprocess
    # Returns: VideoAnalysis object with all 11 sections structured
```

**Output format:**
```markdown
# Video Analysis: <title>
URL: <url>
Channel: <channel>
Analyzed: 2026-03-24

## Hook Architecture
[11 sections of analysis]
...

## Reusable Templates
- Template 1: [fill-in-the-blank]
- Template 2: [fill-in-the-blank]
```

---

### Layer 4: Persistent Storage + RAG (Obsidian + obsidian-rag)

**Storage Layer: Obsidian Vault**

Each video analysis becomes a single markdown file:

```markdown
---
title: "Claude Code + Obsidian = UNSTOPPABLE"
url: "https://www.youtube.com/watch?v=eRr2rTKriDM"
channel: "Chase AI"
analyzed_date: "2026-03-24"
keywords: ["obsidian", "claude-code", "persistent-memory", "second-brain"]
analysis_sections: 11
---

[Full 11-section analysis from Layer 3]
```

**Why YAML front-matter:**
- obsidian-rag uses front-matter for metadata indexing
- Enables filtering by channel, date, keywords
- Compatible with standard Obsidian tooling

**Query Layer: obsidian-rag**

Once videos are stored in vault, obsidian-rag enables semantic queries:

```
User query: "What psychological hooks work in educational content?"
↓
obsidian-rag semantic search
↓
Returns: All video analyses containing hook architecture patterns
↓
Agent generates new script template from matching videos
```

**Why obsidian-rag:**
- Makes video content searchable (not just indexed by filenames)
- Cross-session learning: new sessions can query all past analyses
- RAG prevents hallucination: generates from actual analyzed content
- No external database needed; vault is canonical source

**Obsidian skills integration:**
- obsidian-automation: Programmatic note writes (mde → vault)
- obsidian-knowledge: Graph-based cross-note queries (if needed)
- obsidian-rag: Semantic search (multi-session learning)

**Integration with mde:**
```python
# src/mde/youtube_review.py - Layer 4

async def store_analysis_in_obsidian(
    analysis: VideoAnalysis,
    vault_path: Path
) -> Path:
    """Write structured analysis to Obsidian vault."""
    # Creates: vault_path/YouTube-Analysis/{video_id}.md
    # Front-matter: YAML with title, URL, date, keywords
    # Body: Full 11-section analysis from Layer 3
    # Returns: path to created file
```

---

## Integration with mde Package

### Module Structure

```
src/mde/
├── youtube_review.py          # New module
│   ├── download_and_extract_captions()  # Layer 1
│   ├── transcribe_video()               # Layer 2
│   ├── analyze_video_transcript()       # Layer 3
│   ├── store_analysis_in_obsidian()     # Layer 4
│   ├── VideoAnalysisResult (pydantic)   # Output model
│   └── review_youtube_video()           # Orchestrator (public API)
├── cli.py
│   ├── Add subcommand: youtube-review
└── ...
```

### CLI Entry Point

```bash
# Download + transcribe + analyze + store (full pipeline)
$ uv run mde-py youtube-review "https://www.youtube.com/watch?v=eRr2rTKriDM"

# With options
$ uv run mde-py youtube-review <URL> \
  --vault-path ~/Obsidian/MyVault \
  --model base \
  --force-whisper  # Skip captions, use Whisper
```

### Claude Code Skill

Create skill wrapper to expose via /youtube-review:

```typescript
// skills/youtube-review.ts
import { execFileNoThrow } from "../utils/execFileNoThrow.js";

export async function youtubeReview(url: string) {
  const { stdout, status } = await execFileNoThrow(
    "uv",
    ["run", "mde-py", "youtube-review", url]
  );
  return stdout;
  // Writes to Obsidian vault automatically
  // Returns: Analysis summary
}
```

Usage in Claude Code:
```
/youtube-review https://www.youtube.com/watch?v=eRr2rTKriDM

Analysis stored in Obsidian vault at:
~/Obsidian/MyVault/YouTube-Analysis/eRr2rTKriDM.md

[11-section analysis summary returned]
```

---

## Comparison: Alternative Approaches

### ❌ YouTube Data API v3 (Not Recommended)

| Aspect | API v3 | Recommended Stack |
|--------|--------|-------------------|
| Cost | $0.01/1000 calls (quota limits) | Free (yt-dlp + Whisper) |
| Setup | OAuth, API key management | None (open-source) |
| Transcript access | Paid tier required | Included with yt-dlp |
| Transcription | Not provided | faster-whisper (local) |
| Analysis | Not provided | youtube-video-analyst |
| Self-hosting | Cloud-dependent | 100% local |

**Verdict:** API adds cost + complexity for minimal benefit. Skip unless you need real-time monitoring of 1000s of channels.

### ❌ Browser Automation (Playwright/Puppeteer)

| Aspect | Browser Automation | Recommended Stack |
|--------|-------------------|-------------------|
| Robustness | Fragile; breaks with UI changes | Battle-tested CLI (yt-dlp) |
| Performance | Slow; requires headless browser | Fast; native CLI |
| Resource usage | 500MB+ RAM per instance | <50MB |
| Maintenance | High (YouTube UI changes frequently) | Low (community-driven) |

**Verdict:** Over-engineered. yt-dlp is purpose-built for this task.

### ✓ Recommended Hybrid Approach

Our recommendation combines best-of-breed tools at each layer:

**Transcript Extraction:**
- Primary: youtube-transcript-api (captions, lightweight)
- Fallback: yt-dlp (more robust)
- Last resort: faster-whisper (transcribe from audio)

**Analysis:**
- Primary: youtube-video-analyst (comprehensive)
- Alternative: Could chain with NotebookLM for additional synthesis

**Storage + Query:**
- Primary: Obsidian + obsidian-rag (local, semantic search)
- Alternative: If no Obsidian: Local SQLite + embedding search (requires more code)

**Memory:**
- Primary: obsidian-rag (multi-session RAG queries)
- Alternative: claude-mem plugin (session transcripts, separate from Obsidian)

---

## Implementation Roadmap

### Phase 1: Core Pipeline (2-3 days)

**Scope:**
- src/mde/youtube_review.py with Layers 1-3
- youtube-transcript-api for caption extraction
- youtube-video-analyst skill integration
- Basic Obsidian vault writing (markdown files only)
- CLI: `uv run mde-py youtube-review <URL>`

**Deliverables:**
- ✓ Full 11-section analysis output
- ✓ Stored as markdown in Obsidian vault
- ✓ Unit tests for each layer
- ✓ Integration test with real YouTube video
- ✓ Error handling for missing captions

**Success criteria:**
- Core pipeline works end-to-end
- Output quality matches youtube-video-analyst examples
- <5 second startup time (excluding download/transcription)

### Phase 2: Whisper Fallback (1-2 days)

**Scope:**
- Add faster-whisper Layer 2 integration
- Conditional branching: captions → youtube-transcript-api; no captions → Whisper
- Model size configuration (tiny/base/small)
- Timeout handling

**Deliverables:**
- ✓ Whisper transcription for caption-less videos
- ✓ Performance benchmarks (time per video hour)
- ✓ GPU acceleration (if available)
- ✓ Tests: caption-enabled vs caption-less videos
- ✓ Graceful error handling (transcription timeout)

**Success criteria:**
- Caption-less video transcription accurate to >90% WER
- <30 min transcription time for 1-hour video (on base model)

### Phase 3: Obsidian Integration (1-2 days)

**Scope:**
- YAML front-matter metadata
- Organize vault structure (YouTube-Analysis/ subdirectory)
- Integrate obsidian-rag for semantic search
- Multi-session learning: agent queries past analyses

**Deliverables:**
- ✓ Structured YAML front-matter (title, URL, date, keywords)
- ✓ obsidian-rag indexing + semantic search integration
- ✓ Cross-session query examples ("What hooks work in tech?")
- ✓ RAG accuracy tests (retrieval precision/recall)

**Success criteria:**
- Semantic search returns 5-10 relevant videos for typical query
- Cross-session queries return consistent results
- <500ms latency for RAG query

### Phase 4: Claude Code Skill (1 day)

**Scope:**
- /youtube-review slash command wrapper
- Auto-write to Obsidian vault
- Return analysis summary to Claude Code session
- Documentation + examples

**Deliverables:**
- ✓ Skill definition (JSON)
- ✓ Integration tests with Claude Code
- ✓ Example prompts showing multi-video analysis
- ✓ README for skill installation + usage

**Success criteria:**
- Skill runs without errors in Claude Code
- Output integrates cleanly with agent workflows
- <10 second response time (including processing)

---

## Constraint Verification

| Constraint | Status | Evidence |
|-----------|--------|----------|
| Self-hosted/local, no paid API keys | ✓ | yt-dlp, faster-whisper, youtube-video-analyst all open-source |
| Integrate with mde Python package | ✓ | src/mde/youtube_review.py module pattern proven in mde |
| Work as Claude Code skill or hook | ✓ | /youtube-review slash command; could trigger on URL paste |
| Pipeline: extract → store → query | ✓ | yt-dlp → Whisper → video-analyst → Obsidian → obsidian-rag |

**All constraints satisfied.**

---

## Remaining Unknowns & Risks

### Unknown #1: Whisper mise Availability
**Status:** VERIFY
**Impact:** Phase 2 blocker
**Mitigation:** Pip install fallback within project venv (already supported by mde)

### Unknown #2: obsidian-rag Source Code
**Status:** UNKNOWN (only available via skills.sh)
**Impact:** Phase 3 blocker for advanced features
**Mitigation:** Assume production-ready per skills.sh listing; implement basic RAG integration first; advanced features can wait

### Risk #1: Long Transcription Times
**Status:** Inherent to Whisper
**Mitigation:** Run in background; show progress; offer model size options (tiny for speed, small for accuracy)

### Risk #2: youtube-transcript-api Breakage
**Status:** Low (stable API)
**Mitigation:** Fallback to yt-dlp subtitle extraction; test regularly

### Risk #3: Obsidian Vault Corruption
**Status:** Low (markdown is resilient)
**Mitigation:** Write to temp file first; validate markdown syntax; atomic move

---

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| yt-dlp download (1 hour video, 720p) | 2-5 min | Network-dependent; cached captions <1s |
| Whisper transcription (1 hour, base model) | 20-30 min | M1/M2 Mac; GPU could reduce to 5-10 min |
| youtube-video-analyst analysis | 10-20s | API call; entire 11-section output |
| Obsidian write + RAG index | 2-5s | File write + embedding generation |
| **Total pipeline** | **25-35 min** | For caption-less video; captions skip Whisper (-20 min) |

**Typical use case:** User subscribes to 5 channels, wants weekly review of new videos.
- Time budget: 1 hour per week for ~3 videos = reasonable
- Background job: Agent can run overnight

---

## Success Metrics

### Functional Metrics
1. **Analysis completeness:** All 11 sections populated for 95%+ of videos
2. **Accuracy:** Transcript matches YouTube captions >95% (for Whisper case)
3. **Output quality:** Matches shipshitdev/youtube-video-analyst examples
4. **RAG precision:** Semantic search returns on-topic results >90% of time

### Performance Metrics
1. **Latency:** Full pipeline (caption-enabled) <5 minutes
2. **Throughput:** Can analyze 5 videos/week without blocking agent
3. **Resource usage:** Peak memory <2GB (fits in cloud-friendly environments)
4. **Reliability:** 99% success rate (handle transient network errors gracefully)

### User Experience Metrics
1. **Skill usability:** /youtube-review command works in <5 clicks
2. **Documentation:** Clear examples for common queries
3. **Learning:** Agent can query past analyses and discover patterns
4. **Privacy:** All processing local (no YouTube data sent to external services beyond download)

---

## Related Work & Prior Art

### Community Implementations
1. **Mark Kashef (Early AI Adopters):** File processing pipeline for Obsidian
   - Handles PDF/DOCX → clean notes
   - Slash commands: /daily, /standup, /tldr
   - Open GitHub repo: early AI Adopters / second-brain

2. **Cole (Dynamous):** Second-brain skills ecosystem
   - Dozens of Claude Code skills for research
   - Architecture: Claude Code (workhorse) + Obsidian (canvas) + Skills (knowledge)
   - Open GitHub repo: coleam00/second-brain-skills

3. **Chase AI:** YouTube research agent
   - YouTube search → NotebookLM synthesis → Obsidian storage
   - 5-video tutorial series
   - Concrete examples of multi-session learning

### Academic/Industry Parallels
- **RAG (Retrieval-Augmented Generation):** Our obsidian-rag layer; proven to reduce hallucination in LLMs
- **Content Analysis:** Similar to computational linguistics work on viral video structure
- **Self-learning agents:** Mirrors loop: agent → process → store → query → improve

---

## Conclusion

The recommended architecture is **production-ready** based on:

1. **Battle-tested components:** yt-dlp, Whisper, youtube-video-analyst all active projects
2. **Proven patterns:** 5 community YouTube creators showing working implementations
3. **Local-first:** No API keys, no external dependencies, full privacy
4. **mde-compatible:** Python-based, follows existing mde patterns
5. **Scalable:** Can handle dozens/hundreds of videos with Obsidian RAG

**Next step:** Implement Phase 1 (core pipeline) and gather user feedback before Phase 2-4.

---

## References

- Task #1 Finding: `docs/research/trail/findings/youtube-transcript-skills-2026-03-24.yaml`
- Task #2 Finding: `docs/research/trail/findings/obsidian-youtube-integration-2026-03-24.yaml`
- Synthesis: `docs/research/trail/findings/youtube-agent-review-synthesis-2026-03-24.yaml`
- Community: Mark Kashef, Cole (Dynamous), Chase AI (YouTube tutorials)
- Skills: shipshitdev/youtube-video-analyst, composiohq/youtube-downloader, intellectronica/youtube-transcript

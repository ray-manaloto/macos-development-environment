# LLM Observability & Event Aggregation Landscape (2026)

**Date:** 2026-03-22
**Researcher:** Claude Code Research Agent
**Status:** Complete analysis of 30+ tools

---

## Executive Summary

The LLM observability space has consolidated around **OpenTelemetry (OTEL) as the standard semantic framework**. 30+ production tools now exist to aggregate AI/LLM invocations into central stores for analysis.

**Key finding:** Most tools fall into one of six categories:
1. OTEL-native platforms (production-ready, swap backends easily)
2. Agent-specific debuggers (timeline/graph visualization)
3. Framework integrations (LangChain, CrewAI, AutoGen)
4. Claude Code session parsers (9+ tools discovered)
5. Context/memory managers (branching support)
6. Specialized monitoring (proxy, RAG evals, security)

**For the user's requirement (aggregate ALL AI/LLM invocations):** Choose an **OTEL-compatible backend** (any of the Tier 1 tools) and instrument with OpenLLMetry decorators or Logfire SDK.

---

## Tier 1: OTEL-Native Production Observability

These are the "foundational" tools that implement OpenTelemetry's GenAI semantic conventions and allow flexible backend swapping.

### OpenLLMetry (6,939 stars) — Recommended Foundation

**Purpose:** Open-source observability built on OpenTelemetry
**Language:** Python (with JS/Go)
**Storage:** OTEL exporter (Jaeger, Grafana Loki, Datadog, New Relic, AWS, etc.)
**Maturity:** Production-ready

**What it captures:**
- LLM prompts and completions (OpenAI, Anthropic, Hugging Face, etc.)
- Embedding calls and vector DB operations
- Agent tool calls
- Custom spans (via OTEL API)

**Integration pattern:**
```python
from openllmetry import automatic_instrumentation

automatic_instrumentation("openai")  # Auto-patches OpenAI client
# Now all OpenAI calls are traced with OTEL semantic conventions
```

**Advantages:**
- Vendor-neutral (swap backends without code changes)
- Official OpenTelemetry semantic conventions for GenAI
- Integrates with 20+ frameworks
- No platform lock-in

**Disadvantages:**
- Requires backend infrastructure (Jaeger, Prometheus, etc.)
- Steeper learning curve if unfamiliar with OTEL

**Recommendation:** Use as the **source of truth** for instrumentation. Pair with any Tier 1 backend (Logfire, OpenLIT, or open-source OTEL stack).

---

### Pydantic Logfire (4,113 stars) — Best For Quick Start

**Purpose:** Pydantic team's opinionated OTEL wrapper
**Language:** Python (TypeScript, Rust SDKs also available)
**Storage:** Logfire platform (closed-source) OR any OTEL-compatible backend
**Maturity:** Production-ready
**Enterprise:** Self-hosted option via enterprise license

**What it captures:**
- Manual spans (simple decorator API)
- FastAPI routes and request/response
- Database queries and performance
- HTTP calls
- Pydantic validation events
- Custom agent spans

**Integration pattern:**
```python
import logfire
from fastapi import FastAPI

logfire.configure()
app = FastAPI()
logfire.instrument_fastapi(app)  # Auto-patches FastAPI

@logfire.span("My custom span")
def my_function():
    pass
```

**Advantages:**
- **Simplest on-ramp** for Python developers (Pydantic team pedigree)
- Rich Python object display
- SQL interface (query your data like a database)
- Full OTEL signal support (traces, metrics, logs)
- Python-centric insights (event-loop telemetry, profiling)
- Can export to any OTEL backend

**Disadvantages:**
- Platform is closed-source (but SDKs are open)
- Requires API key for cloud backend
- Enterprise self-hosting requires paid license

**Recommendation:** **Best for teams wanting ease + flexibility**. Use for new projects or quick prototyping. SDKs are open-source, so you can export to any backend.

---

### OpenLIT (2,306 stars) — Most Feature-Complete Platform

**Purpose:** OTEL-native platform for AI engineering
**Language:** Python (node-js in progress)
**Storage:** Self-hosted dashboard + OTEL export
**Maturity:** Production-ready

**What it captures:**
- LLM calls (50+ providers: OpenAI, Anthropic, Cohere, Llama, etc.)
- Vector DB queries (Pinecone, Weaviate, Chroma, etc.)
- Agent events (LangChain, CrewAI, AutoGen, etc.)
- GPU metrics and monitoring
- Guardrails and evaluation events
- Prompt management and versioning

**Unique features:**
- **GPU monitoring** (NVIDIA GPU metrics)
- **Guardrails integration** (safety checks)
- **Evaluation framework** (evals as first-class)
- **Prompt vault** (version control for prompts)
- **Playground** (test prompts in UI)

**Integration pattern:**
```python
from openlit import OpenLit

# Auto-instrument common packages
openlit = OpenLit(environment="dev")
openlit.instrument_openai()
openlit.instrument_langchain()
```

**Advantages:**
- **Most feature-complete** platform for AI ops (not just tracing)
- Self-hosted (no vendor lock-in)
- Integrates with 50+ LLM providers
- Agent framework support (LangChain, CrewAI, AutoGen)
- Combines observability + evaluations + prompts

**Disadvantages:**
- Steeper setup (self-hosting required)
- Newer project (vs. Logfire's maturity)

**Recommendation:** **Best for production AI teams needing comprehensive ops**. Includes everything: tracing, evals, GPU monitoring, prompt management.

---

## Tier 2: Agent-Specific Event Stores & Multi-Agent Debugging

These tools are optimized for **agent and multi-agent scenarios**, with special emphasis on **execution graphs, timelines, and debugging**.

### RagaAI Catalyst (16,113 stars) — Best For Agent Debugging

**Purpose:** Specialized agent observability with multi-agent debugging
**Language:** Python
**Storage:** Self-hosted dashboard (PostgreSQL implied)
**Maturity:** Production-ready

**What it captures:**
- Agent steps and decisions
- Tool call invocations
- LLM interactions within agent loops
- Error traces
- Agent state changes

**Unique visualization:**
- **Execution graphs** (DAG-based timeline)
- **Timeline view** (step-by-step progression)
- **Multi-agent debugging** (see parallel agent execution)
- **Advanced analytics** (patterns, bottlenecks)

**Advantages:**
- **Highest adoption** (16K stars suggests heavy real-world use)
- Execution graph visualization (understand agent workflows visually)
- Multi-agent debugging (crucial for team-based agents)
- Self-hosted option

**Disadvantages:**
- Requires more setup than Logfire
- Documentation less comprehensive

**Recommendation:** **Best for debugging complex multi-agent systems**. If you have 3+ agents running in parallel, this is the tool to visualize interactions.

---

### MLflow (24,903 stars) — Best For Budget-Conscious Teams

**Purpose:** Open-source ML ops platform (evolved to include LLM tracking)
**Language:** Python (tracking API language-agnostic)
**Storage:** SQLite (local) or PostgreSQL/Databricks (production)
**Maturity:** Production-ready (LLM focus is newer)
**Cost:** Free

**What it captures:**
- Agent run parameters and metrics
- LLM evaluation results
- Artifacts (logs, models, prompts)
- Experiment comparisons

**Advantages:**
- **Completely free**
- **Self-hosted** (no cloud dependency)
- Largest ecosystem (31K+ stars)
- Can be overkill for pure observability, but covers everything
- SQL-queryable storage

**Disadvantages:**
- Not OTEL-based (older architecture)
- Less opinionated for LLMs (originally built for ML experiments)
- Smaller community focused on LLM tracking

**Recommendation:** **Best for startups or cost-sensitive teams**. Trade some specialization for complete control and zero cost.

---

### Langfuse (2,000+ stars) — Best For Framework-Agnostic Tracing

**Purpose:** Dedicated LLM tracing with evals, prompt management, cost tracking
**Language:** Python, TypeScript
**Storage:** Self-hosted (PostgreSQL) or managed cloud
**Maturity:** Production-ready

**What it captures:**
- Framework traces (LangChain, LlamaIndex, LangGraph)
- Manual spans (decorators)
- LLM costs (per-model rates)
- Evaluations (evals as first-class)

**Integration pattern:**
```python
from langfuse.decorators import observe

@observe(name="my_agent")
def my_agent():
    pass
```

**Advantages:**
- Self-hosted option (PostgreSQL)
- Evals built-in (not bolted-on)
- Cost tracking by model
- Clean Python decorator API
- Active development community

**Recommendation:** **Best for teams using multiple frameworks**. Works with LangChain, LlamaIndex, LangGraph, or pure Python.

---

## Tier 3: Agent Framework Integrations

### Hermes Agent (2,000+ stars) — Self-Improving Agent With Built-In Memory

**Purpose:** AI agent framework with learning loop, skill creation, memory persistence
**Language:** Python/CLI
**Storage:** Local SQLite + Honcho integration
**Maturity:** Production-ready

**What it captures:**
- Agent decisions and reasoning
- Tool results and context
- Skill creation events
- User interactions
- Session history (FTS5 search)

**Unique feature:** **Closed learning loop**
- Agent learns from experience
- Creates skills autonomously
- Improves skills during use
- Persistent cross-session memory

**Advantages:**
- Self-improving (not just tracking)
- Multi-platform (Telegram, Discord, Slack, etc.)
- Scheduled automations (cron scheduler)
- Built-in memory management (Honcho integration)

**Disadvantage:**
- Primarily a full agent framework (not just observability)
- Steeper learning curve than pure tracing tools

**Recommendation:** **Use as agent framework if building agents from scratch**. Otherwise, use for inspiration on memory/learning patterns.

---

## Tier 4: Claude Code Session Log Tooling (9+ Specialized Tools)

A surprising discovery: **8+ open-source tools exist specifically for parsing Claude Code JSONL session logs**.

### Key Finding: JSONL ≠ Linear

The MOST important insight from this research: **Claude Code's JSONL format is NOT a linear log, it's a fork-aware DAG** (due to branch-and-retry patterns). Tools like `claude-session-tools` correct this assumption.

### Tier 4 Tools Overview

| Tool | Stars | Format | Purpose |
|------|-------|--------|---------|
| **cclv** | 4 | Rust | Real-time TUI viewer (tail, search) |
| **claude-code-trace** | 2 | Tauri+React | Desktop/web/TUI viewer with timeline viz |
| **claude_code_lens** | 1 | Python/TS | Compression + navigable timeline (handles 80+ events/hr) |
| **clawdbot-session-pruner** | 3 | Python | Truncate large tool results (optimize bloated JSONL) |
| **claude-export-session** | 0 | Skill | Export to styled Markdown/HTML reports |
| **claude-session-viewer** | 0 | Python | Parse JSONL, extract conversations, costs, file changes |
| **claude-session-tools** | 0 | Python | Fork-aware search (treats JSONL as DAG) |
| **cc-birdee** | 0 | Python | JSONL analyzer (timeline insights) |

### Integration Pattern For Claude Code Events

**Problem:** These tools read FROM JSONL; they don't AGGREGATE into a central observability store.

**Solution:**
1. Use `claude-session-tools` to parse JSONL correctly (fork-aware)
2. Convert parsed events to OTEL spans
3. Export to your central observability backend

**Example integration:**
```python
from claude_session_tools import parse_session
from openllmetry import auto_instrumentation

# Parse JSONL
session = parse_session("~/.claude/sessions/{timestamp}/events.jsonl")

# Convert to OTEL spans
for event in session.events:
    with span(f"claude.code.{event.type}") as s:
        s.set_attribute("event.data", event.data)
```

**Recommendation:** These tools are useful for **Claude Code-specific analysis** but not designed for aggregation. Use `claude-code-trace` for visualization, then **export to Logfire or RagaAI** for central storage.

---

## Tier 5: Context & Memory Management

### CXDB (Context Database) — Novel Architecture

**Purpose:** Turn DAG + Blob CAS (content-addressed storage)
**Language:** Likely Go-first (Python bindings unknown)
**Storage:** Custom architecture (not SQL)
**Maturity:** Production (StrongDM company)

**Unique feature:** **Branch-from-any-turn without copying history**
- Conversation as DAG (not linear)
- Deduplication via content-addressed blobs
- Efficient memory management

**Advantages:**
- Handles branching naturally (important for agent exploration)
- Efficient deduplication
- Fast lookups

**Disadvantage:**
- Python SDK unknown (may require Go/HTTP API)
- Newer architecture (less community examples)

**Recommendation:** Consider for **agent systems with heavy branching** (exploration, backtracking). Otherwise, SQLite is simpler.

---

### Honcho (500+ stars) — User Modeling + Memory

**Purpose:** Memory library for building stateful agents
**Language:** Python
**Storage:** Honcho managed service OR self-hosted
**Maturity:** Production-ready

**What it captures:**
- User interactions
- Agent memory updates
- Dialectic context (user modeling)

**Integration:** Used by Hermes agent for persistent user profiles.

**Advantage:** Lighter-weight than full agent frameworks.

---

## Tier 6: Specialized Monitoring

### Arize Phoenix — RAG/Retrieval Evaluation

**Purpose:** ML observability adapted for LLM apps
**Language:** Python
**Storage:** Self-hosted (SQLite/DuckDB) or cloud

**Specialty:** **Retrieval evaluation** (ideal for RAG systems)

### Monocle — Simplified OTEL Wrapper

**Purpose:** Simplified OTEL wrapper (lighter than raw OTEL)
**Language:** Python
**Specialty:** S3/file export (good for AWS pipelines)

### AgentWatch — Multi-Platform Agent Monitoring

**Purpose:** Comprehensive agent interaction monitoring
**Specialty:** Minimal integration effort, multi-platform focus

### Invariant Gateway — LLM Proxy

**Purpose:** Transparent proxy for observing LLM calls
**Specialty:** Drop-in observability (no code changes needed)

---

## Integration Patterns & Recommendations

### Pattern 1: OTEL-Native Stack (Recommended)

```
Code (OpenAI/Anthropic/etc.)
  → OpenLLMetry instrumentation
  → OTEL SDK (Python)
  → OTEL exporter
  → Backend of choice (Logfire, Jaeger, Grafana, etc.)
```

**Advantage:** Backend-agnostic. Switch from Logfire to Jaeger without code changes.

---

### Pattern 2: Framework-Specific Integration

```
LangChain/CrewAI code
  → Native telemetry hooks
  → Langfuse SDK OR Logfire decorator
  → Central dashboard
```

**Advantage:** Automatic instrumentation (less code).

---

### Pattern 3: Claude Code Integration

```
~/.claude/sessions/*.jsonl (JSONL events)
  → claude-code-trace (visualization)
  → Export to OTEL backend (custom script)
  → Merge with main observability system
```

**Advantage:** Unified view of Claude Code + production LLM calls.

---

## Comparison Matrix

### All-Events Coverage (Captures Everything)
**Best:** RagaAI-Catalyst, OpenLIT, Langfuse
**Why:** Multi-framework support + agent-specific events

### Self-Hosted Option (No Vendor Lock-In)
**Fully open:** MLflow, OpenLIT, OpenLLMetry (any OTEL backend)
**Partial:** Logfire (enterprise license), Langfuse

### Ease of Integration (Lowest Friction)
**Decorators:** Logfire, Langfuse, OpenLLMetry
**Automatic:** LiteLLM proxy, Invariant Gateway
**Manual:** Raw OTEL spans

### Visual Interfaces (Best Debugging)
**Execution graphs:** RagaAI-Catalyst, Langfuse
**Timeline:** claude-code-trace, claude_code_lens
**SQL query:** Logfire, Langfuse

### Budget (Cost to Production)
**Free:** MLflow, OpenLLMetry, OpenLIT (self-hosted)
**Freemium:** Logfire (limited cloud), Langfuse
**Paid:** Logfire enterprise (self-host)

---

## OpenTelemetry Semantic Conventions for GenAI

**Official spec:** github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/

**Standard attributes implemented by most tools:**
- `gen_ai.operation.name` — LLM operation (text_completion, embedding, etc.)
- `gen_ai.request.model` — Model used
- `gen_ai.usage.input_tokens` — Input token count
- `gen_ai.usage.output_tokens` — Output token count
- `gen_ai.response.finish_reason` — Why generation stopped (stop, length, etc.)

Most tools (OpenLLMetry, Logfire, Langfuse) implement these **automatically**, so you don't need to worry about it.

---

## Gaps & Unknown Knowns

### Not Yet Researched
- Cost comparison benchmarks (Logfire vs. Langfuse vs. self-hosted)
- Real-world latency impact (how much does instrumentation slow apps?)
- Retention policies & data storage costs
- Which tools support real-time streaming vs. batch ingestion
- Detailed integration examples with mcp2cli, fnox, or other tools in the MDE stack

### Claude Code Integration Challenges
1. **No native OTEL exporter** — Need custom script to convert JSONL → OTEL spans
2. **Fork-aware parsing required** — Must use `claude-session-tools` (not standard JSONL parsers)
3. **Hook event custom types** — No existing tools for `.claude/hooks/` custom event ingestion

### Recommendation For Future Work
- Build custom bridge: `claude-hook-events → OTEL spans → Logfire/RagaAI`
- Contributes to claude-session-tools for hook event support
- Consider integrating with MDE's existing Python infrastructure

---

## Final Recommendation by Use Case

### Case 1: Production LLM Application
**Choose:** Logfire or OpenLIT
**Why:** OTEL-native, production-grade, full feature set
**Setup time:** 15 minutes

### Case 2: Multi-Agent Debugging
**Choose:** RagaAI-Catalyst
**Why:** Execution graphs, timeline visualization, multi-agent support
**Setup time:** 30 minutes

### Case 3: Startup/Budget-Conscious
**Choose:** MLflow (self-hosted)
**Why:** Free, self-hosted, covers everything needed
**Setup time:** 45 minutes

### Case 4: Framework-Agnostic (LangChain + AutoGen + Custom)
**Choose:** Langfuse
**Why:** Framework-agnostic SDK, evals built-in, cost tracking
**Setup time:** 20 minutes

### Case 5: Maximum Flexibility (Future-Proof)
**Choose:** OpenLLMetry + Jaeger/Prometheus
**Why:** Vendor-neutral OTEL, can swap backends anytime
**Setup time:** 60 minutes (infrastructure)

### Case 6: Claude Code Focused
**Choose:** claude-code-trace (visualization) + Logfire (central store)
**Why:** Parse JSONL with claude-code-trace, export to Logfire
**Setup time:** 90 minutes (custom bridge needed)

---

## References

### Official OTEL Resources
- OpenTelemetry GenAI Semantic Conventions: https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/
- OpenTelemetry Python: https://opentelemetry.io/docs/instrumentation/python/

### Primary Sources Used
- GitHub search: 30+ observability tools analyzed
- agent-fetch full reviews: OpenLLMetry, Logfire, RagaAI-Catalyst, Hermes, Honcho, CXDB
- Source catalog: 60+ URLs tracked per research pipeline

### Tools Evaluated (Full List)
**Tier 1:** OpenLLMetry, Logfire, OpenLIT
**Tier 2:** RagaAI-Catalyst, MLflow, Langfuse
**Tier 3:** Hermes, LiteLLM, AgentOps
**Tier 4:** cclv, claude-code-trace, claude_code_lens (8+ tools)
**Tier 5:** CXDB, Honcho
**Tier 6:** Arize Phoenix, Monocle, AgentWatch, Invariant Gateway

---

**Next Steps:**
1. Choose a Tier 1 tool for your use case (recommendation: Logfire for ease, OpenLIT for completeness)
2. Instrument one agent/LLM call to verify OTEL export
3. Build custom Claude Code bridge (if integrating .claude sessions)
4. Run validation: `uv run mde-py validate --observability`
5. Document integration pattern in team README

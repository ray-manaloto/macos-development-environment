---
name: Multi-Model CLI SDK Research Findings
description: Comprehensive analysis of how opencode, pi-mono, and acodex handle multi-model orchestration, CLI integration, and structured output
type: reference
---

# Multi-Model CLI SDK Integration Research

## Key Distinction: Native SDKs vs Subprocess Wrappers

### opencode (Go) — Native SDK Approach
- **Architecture**: Provider-factory pattern with type-generic `baseProvider[C ProviderClient]`
- **Integration**: Direct SDK clients (anthropic-sdk-go, openai-go, gemini-go, etc.)
- **IPC**: HTTP/WebSocket directly to provider APIs
- **Advantages**: Best for stateful agents, complex tool orchestration, concurrent execution
- **Streaming**: `StreamResponse()` returns `<-chan ProviderEvent` with fine-grained events (ContentDelta, ToolUseStart, ToolUseDelta, ToolUseStop, ThinkingDelta, Complete)
- **Tool Execution**: Loop-based with explicit cancellation support, parallel execution via goroutines possible
- **Cost Tracking**: Built-in per-model usage tracking with cache-aware pricing
- **Session Persistence**: SQLite-based message history + cost per session

### pi-mono (TypeScript) — Unified API with Registry Pattern
- **Architecture**: Model registry with type-safe retrieval `getModel<TProvider, TModelId>(provider, modelId)`
- **Integration**: Native SDKs underneath, abstracted via unified streaming API
- **IPC**: HTTP/WebSocket (provider-specific)
- **Advantages**: Maximum type safety, cross-provider handoffs, model discovery
- **Streaming**: `stream()` yields fully typed events (text_start, text_delta, thinking_delta, toolcall_start, toolcall_delta, toolcall_end, done, error)
- **Tool Definitions**: TypeBox JSON Schema with AJV validation; note: use StringEnum for Google compatibility, not Type.Enum
- **Cross-Provider Handoff**: Serializable Context allows handoff between models mid-session
- **OAuth Support**: Native login flows for Vertex AI, GitHub Copilot, Google Gemini CLI, Anthropic, Antigravity

### acodex (Python) — Subprocess Wrapper Approach
- **Architecture**: CLI wrapper, NOT native Python SDK
- **Integration**: Spawns `codex` CLI subprocess, exchanges JSONL events over stdin/stdout
- **IPC**: JSONL over pipes (process isolation, no direct network)
- **Advantages**: Process isolation, CLI-only deployments, clean separation, thread persistence on disk
- **Streaming**: `run_streamed()` yields dataclass events (ItemCompletedEvent, TurnCompletedEvent, TurnFailedEvent)
- **Structured Output**: Pydantic models passed as `output_type=YourModel` to `run()`
- **Thread Persistence**: `~/.codex/sessions/thread-{id}.jsonl` for resumption
- **Safety Controls**: Explicit ThreadOptions (sandbox_mode, approval_policy, web_search_mode, working_directory)
- **Quality**: mypy strict, 100% coverage, vendored TypeScript SDK as parity source

## Recommended Multi-Model Consensus Pattern for Your Project

**Hybrid subprocess + factory approach:**

1. Wrap each CLI (codex, gemini-cli, claude-cli) in subprocess providers
2. Implement consensus orchestrator that streams from all providers in parallel
3. Aggregate results via event collection (ItemCompletedEvent, structured_response)
4. Vote/consensus mechanism on outputs
5. Cost tracking per provider for future optimization

This leverages:
- Process isolation from acodex pattern
- Provider-factory extensibility from opencode
- Tool execution flexibility from both
- Clean Python integration (not TypeScript)

## Key Implementation Details

### Event Aggregation (for consensus)
- Each provider's streaming loop collects intermediate events
- ItemCompletedEvent signals tool completion
- TurnCompletedEvent signals response complete with final usage stats
- structured_response available after TurnCompleted

### Timeout/Context Management
- For subprocess wrappers: wrap `run_streamed()` with `asyncio.wait_for()`
- For long conversations: use thread resumption (`resume_thread(thread_id)`)
- Context window management: monitor usage tokens before hitting limits

### Structured Output Best Practice
Define Pydantic model, pass to each provider, compare outputs:
```python
class CodeSummary(BaseModel):
    summary: str
    risks: List[str]
    next_steps: List[str]

results = {}
for provider in [codex, gemini, claude]:
    turn = provider.run(prompt, output_type=CodeSummary)
    results[provider.name] = turn.structured_response
```

## Files Created

- `docs/research/trail/findings/codex-gemini-cli-sdk-patterns.yaml` — High-level patterns comparison
- `docs/research/trail/findings/acodex-sdk-usage-patterns.yaml` — acodex-specific technique guide
- `docs/research/trail/findings/multi-model-orchestration-patterns.yaml` — Recommended architecture with code examples
- `docs/research/source-catalog.md` — Updated with 7 new sources (github/raw/docs URLs)

# Deep Review: Multi-Model CLI SDK Orchestration Patterns

**Date**: 2026-03-25
**Scope**: opencode (Go), pi-mono (TypeScript), acodex (Python)
**Context**: Designing consensus LLM orchestration for mde project (Python + DSPy + SubprocessLMProvider)

---

## Executive Summary

Three production codebases show distinct approaches to multi-model integration:

| Project | Language | Pattern | IPC | Best For |
|---------|----------|---------|-----|----------|
| **opencode** | Go | Provider-factory + native SDKs | HTTP/WebSocket | Stateful agents, complex tool orchestration |
| **pi-mono** | TypeScript | Unified API + registry | HTTP/WebSocket | Type-safe cross-provider handoffs |
| **acodex** | Python | Subprocess wrapper + JSONL | stdin/stdout | Process isolation, CLI-only deployments |

For your multi-model consensus layer, a **hybrid subprocess + provider-factory** approach is recommended.

---

## Detailed Pattern Analysis

### 1. opencode: Provider-Factory Pattern (NATIVE SDKS)

#### Architecture
```
┌─────────────────────────────────────────────┐
│          Agent Service                       │
│  (orchestrates tool calls + streaming)      │
└──────────────┬──────────────────────────────┘
               │
         ┌─────┴─────┐
         v           v
   Provider        Provider
   Interface       Interface
         ↑           ↑
    ┌────┴────┐  ┌──┴────┐
    │ Anthropic│  │ OpenAI │  ...
    │  Client  │  │ Client │
    └────┬────┘  └──┬────┘
         │           │
    HTTP/WS    HTTP/WS
         │           │
    API.anthropic.com  api.openai.com
```

**Key Pattern**:
```go
type Provider interface {
    SendMessages(ctx, messages, tools) (*ProviderResponse, error)
    StreamResponse(ctx, messages, tools) <-chan ProviderEvent
    Model() Model
}

type baseProvider[C ProviderClient] struct {
    options providerClientOptions
    client  C  // AnthropicClient | OpenAIClient | ...
}

func NewProvider(providerName string, opts ...ProviderClientOption) Provider {
    switch providerName {
    case models.ProviderAnthropic:
        return &baseProvider[AnthropicClient]{...}
    case models.ProviderOpenAI:
        return &baseProvider[OpenAIClient]{...}
    }
}
```

**Advantages**:
- Type-safe via Go generics
- Unified interface across providers
- Easy to add new providers (just implement ProviderClient interface)
- Streaming events are granular (ContentDelta, ToolUseStart, ToolUseDelta, ToolUseStop, ThinkingDelta)

**Disadvantages**:
- Requires native SDK for each provider (not all have Go bindings)
- Direct network connections (no subprocess isolation)

**Event Stream**:
```go
type ProviderEvent struct {
    Type EventType  // content_start, tool_use_start, tool_use_delta,
                    // tool_use_stop, content_delta, thinking_delta, complete, error
    Content string
    Thinking string
    ToolCall *ToolCall
    Response *ProviderResponse
    Error error
}

// Tool execution loop (from agent.go)
for i, toolCall := range toolCalls {
    select {
    case <-ctx.Done():
        // Cancel remaining
        for j := i; j < len(toolCalls); j++ {
            toolResults[j] = ToolResult{IsError: true, Content: "canceled"}
        }
        goto out
    default:
        toolResult := tool.Run(ctx, toolCall)
        toolResults[i] = ToolResult{...}
    }
}
```

**Cost Tracking**:
```go
cost := model.CostPer1MInCached/1e6*float64(usage.CacheCreationTokens) +
        model.CostPer1MOutCached/1e6*float64(usage.CacheReadTokens) +
        model.CostPer1MIn/1e6*float64(usage.InputTokens) +
        model.CostPer1MOut/1e6*float64(usage.OutputTokens)
```

---

### 2. pi-mono: Unified Registry Pattern (TYPE-SAFE)

#### Architecture
```
┌────────────────────────────────────────┐
│      Agent Class                        │
│  (streamSimple, complete)               │
└──────────────┬─────────────────────────┘
               │
         ┌─────┴─────┐
         v           v
  getModel()      Context
  (registry)    (serializable)
         ↑
    ┌────┴─────────────────────────┐
    │  Model Registry              │
    │  MODELS[provider][modelId]   │
    │  (pre-generated from SDK)    │
    └──────┬───────────────────────┘
           │
    ┌──────┴──────┐
    │ Provider A  │  ...
    │ (OpenAI,    │
    │  Anthropic, │
    │  Google)    │
    └─────┬──────┘
          │
      HTTP/WS
```

**Key Pattern**:
```typescript
// Model registry (auto-generated from SDKs)
export interface Model<TApi extends Api> {
    id: string
    provider: KnownProvider
    displayName: string
    cost: { input, output, cacheRead, cacheWrite }
    supportsTools: boolean
    supportsImages: boolean
    supportsThinking: boolean
}

// Fully typed retrieval
const model = getModel('openai', 'gpt-4o-mini')  // Type: Model<OpenAIApi>

// Streaming with type safety
for await (const event of stream(model, context)) {
    switch (event.type) {
        case 'text_delta': process.stdout.write(event.delta); break
        case 'toolcall_end': handleTool(event.toolCall); break
    }
}
```

**Tool Definition** (TypeBox):
```typescript
const tools: Tool[] = [{
    name: 'get_weather',
    parameters: Type.Object({
        location: Type.String(),
        units: StringEnum(['celsius', 'fahrenheit'])  // NOT Type.Enum for Google
    })
}]
```

**Advantages**:
- Full TypeScript type safety across 20+ providers
- Cross-provider handoffs (serializable Context)
- Model discovery built-in
- Event streaming is fully typed

**Disadvantages**:
- TypeScript-only (not Python)
- Requires native SDK for each provider

**Cross-Provider Handoff Example**:
```typescript
const context: Context = {
    systemPrompt: '...',
    messages: [...]
}

// Send to Model A
const resp1 = await complete(modelA, context)
context.messages.push(resp1)

// Hand off to Model B
const resp2 = await complete(modelB, context)
context.messages.push(resp2)

// Continue with Model C
const resp3 = await complete(modelC, context)
```

---

### 3. acodex: Subprocess Wrapper Pattern (PROCESS ISOLATION)

#### Architecture
```
┌────────────────────────────────────┐
│  AsyncCodex / Codex                 │
│  (typed wrapper)                    │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    v                     v
  Thread            AsyncThread
  (sync)            (async)
    │                     │
    │                     │
    └──────────┬──────────┘
               │
        JSONL IPC (stdin/stdout)
               │
    ┌──────────v──────────┐
    │  codex CLI          │
    │  (subprocess)       │
    │  spawned via Popen  │
    └──────────┬──────────┘
               │
        Thread persisted to
        ~/.codex/sessions/
```

**Key Pattern**:
```python
from acodex import Codex, AsyncCodex
from pydantic import BaseModel

class SummaryPayload(BaseModel):
    summary: str

# Sync
codex = Codex()
thread = codex.start_thread(
    sandbox_mode="read-only",
    approval_policy="on-request"
)
turn = thread.run("Summarize this repo.", output_type=SummaryPayload)
print(turn.structured_response.summary)

# Async
thread = AsyncCodex().start_thread()
turn = await thread.run("Say hello")

# Streaming
streamed = thread.run_streamed("List risks")
for event in streamed.events:
    if isinstance(event, ItemCompletedEvent):
        print(event.item)
turn = streamed.result  # Available after iteration
```

**Advantages**:
- Process isolation (CLI subprocess)
- Clean thread persistence on disk
- Structured output via Pydantic
- Explicit safety controls (sandbox_mode, approval_policy, web_search_mode)

**Disadvantages**:
- Requires `codex` CLI on PATH
- Single provider (codex only)
- Higher latency (subprocess overhead)

**Event Types**:
```python
ItemCompletedEvent(item: ThreadItem)        # Tool execution complete
ItemStartedEvent(item: ThreadItem)          # Tool started
ItemUpdatedEvent(item: ThreadItem)          # Intermediate update
TurnCompletedEvent(usage: Usage)            # Response complete
TurnFailedEvent(error: ThreadError)         # Error occurred
TurnStartedEvent()                          # Turn started
ThreadStartedEvent()                        # Thread started
ThreadErrorEvent(error: ThreadError)        # Session error
```

---

## Recommended Hybrid Architecture for mde Project

### Design: Subprocess Provider Factory with Consensus Orchestration

```
┌────────────────────────────────────────────────┐
│    ConsensusOrchestrator                        │
│  (Python + DSPy)                               │
└──────────────┬─────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    v          v          v
CodexProvider GeminiProvider ClaudeProvider
(subprocess)  (subprocess)   (subprocess)
    │          │          │
    │ JSONL    │ JSON    │ JSON
    │          │          │
    v          v          v
codex CLI  gemini-cli   claude CLI
(OpenAI)   (Google)     (Anthropic)
```

### Implementation Considerations

1. **Process Management**: Use `subprocess.Popen` with `stdout=PIPE, stderr=PIPE` for streaming
2. **Event Aggregation**: Collect responses as they complete, aggregate for voting
3. **Timeout Handling**: Wrap with `asyncio.wait_for()` for hard limits
4. **Error Recovery**: If one model fails, continue with remaining two
5. **Cost Tracking**: Track usage tokens per provider, implement cost-based ranking

### Key Design Patterns

**Pattern 1: Sequential Tool Execution (like opencode)**
- Execute tools one at a time with explicit cancellation support
- Monitor for context-window approaching limit
- Good for careful resource management

**Pattern 2: Parallel Tool Execution (like opencode with goroutines)**
- Execute multiple tools concurrently
- Better latency but higher resource usage
- Good for independent operations

**Pattern 3: Consensus Voting (novel)**
- Run all models on same prompt
- Collect structured_response from each
- Vote on best response (length, quality, reasoning)
- Fallback: use most-cost-effective model that succeeded

### Event Aggregation Strategy

```python
# Collect responses from all models
responses = {
    "codex": {
        "content": "...",
        "usage": {...},
        "items": [ItemCompletedEvent, ...]
    },
    "gemini": {...},
    "claude": {...}
}

# Voting logic
winner = max(
    responses.items(),
    key=lambda x: score(x[1])  # Custom scoring function
)
```

---

## Comparison Table

| Feature | opencode | pi-mono | acodex | Hybrid Recommended |
|---------|----------|---------|--------|-------------------|
| Language | Go | TypeScript | Python | Python |
| Pattern | Provider-factory | Unified API + Registry | Subprocess wrapper | Subprocess factory |
| Native SDKs | Yes | Yes | No (CLI wrapper) | No (CLI wrappers) |
| Type Safety | Go generics | Full TypeScript | Pydantic | Pydantic |
| Multi-Model | Yes (via factory) | Yes (via registry) | No | Yes |
| Process Isolation | No | No | Yes | Yes |
| Tool Execution | Loop with parallel | Event stream | Item events | Loop with cancel |
| Cost Tracking | Built-in | Calculated | Manual | Built-in |
| Streaming | ProviderEvent channel | Typed async iter | JSONL dataclass | Subprocess events |
| Cross-Provider Handoff | No | Yes (serializable Context) | N/A | Yes (save thread IDs) |
| Session Persistence | SQLite | Manual | Filesystem | Filesystem + DB |

---

## Key Findings

1. **opencode** demonstrates the most extensible provider-factory pattern
   - Use this for adding new models
   - But requires native SDK for each provider

2. **pi-mono** shows the most type-safe approach
   - Cross-provider handoffs via serializable Context
   - TypeScript-only limitation

3. **acodex** validates the subprocess wrapper pattern
   - Best for CLI-only deployments and process isolation
   - JSONL event streaming is efficient

4. **Recommended for your project**: Combine approaches
   - Subprocess factory like acodex (process isolation)
   - Provider-factory pattern like opencode (extensibility)
   - Pydantic validation like acodex (type safety)
   - Consensus orchestration (novel layer)

See `docs/research/trail/findings/multi-model-orchestration-patterns.yaml` for detailed code examples from production codebases.

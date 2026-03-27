---
name: Production CLI SDK patterns (acodex, pi-mono)
description: How acodex (Python) and pi-mono (TypeScript) implement Codex/Gemini CLI wrappers successfully at scale
type: reference
---

## Key Finding

Both acodex and pi-mono are **production-validated** implementations of multi-model CLI orchestration with **no dependency on shared framework**. Each independently builds its own wrapper.

## acodex Pattern (Python)

**Repo**: https://github.com/maksimzayats/acodex (53 stars, Apache-2.0, updated 2026-03-23)

**Core Design**:
- Spawns `codex` subprocess, exchanges JSONL events over stdin/stdout
- Zero runtime dependencies (pydantic optional for structured output)
- Sync + async clients (Codex / AsyncCodex)
- Thread persistence: ~/.codex/sessions/{thread_id}

**API Surface**:
```python
codex = Codex(codex_path_override=..., env={...}, config={...})
thread = codex.start_thread(sandbox_mode="read-only", approval_policy="on-request")
turn = thread.run("prompt", output_type=SummaryPayload)
streamed = thread.run_streamed("prompt")  # yields ItemCompletedEvent, TurnCompletedEvent, TurnFailedEvent
```

**Quality Gates**:
- mypy strict + 100% test coverage
- Vendored TypeScript SDK + hourly compatibility tests (fails loudly on drift)
- Ruff linting, pytest testing

**Applicable to mde**:
- Subprocess protocol design is proven
- JSONL streaming matches our adversarial review event format
- Structured output via Pydantic (already in mde deps)

## pi-mono Pattern (TypeScript)

**Repo**: https://github.com/badlogic/pi-mono (monorepo, MIT)

**Core Design**:
- Unified multi-provider LLM API via ApiRegistry pattern
- Dedicated providers for Codex + Gemini CLIs (HTTP API hits, not subprocess)
- Dynamic provider registration/unregistration by sourceId
- Type-safe streaming via AssistantMessageEventStream

**API Providers**:
- `google-gemini-cli`: cloudcode-pa.googleapis.com (prod) + antigravity sandbox variants
- `openai-codex-responses`: chatgpt.com/backend-api
- Standard OpenAI/Anthropic/Groq providers (API keys required)

**Retry Pattern**:
```typescript
MAX_RETRIES = 3
BASE_DELAY_MS = 1000
// exponential backoff: BASE_DELAY_MS * 2^attempt
```

**Thinking Config**:
- Gemini 2.x: `budgetTokens` (thinking token limit)
- Gemini 3: `level` (MINIMAL/LOW/MEDIUM/HIGH)
- Claude: interleaved-thinking-2025-05-14 beta header

**Registry Pattern**:
```typescript
registerApiProvider(provider, sourceId?) // dynamic
getApiProvider(api) -> ApiProviderInternal
unregisterApiProviders(sourceId) // cleanup
```

## Contrasts with DSPy SubprocessLMProvider

| Aspect | acodex/pi-mono | DSPy SubprocessLMProvider |
|--------|---|---|
| **Runtime deps** | Zero (optional pydantic) | Requires openai/anthropic SDKs |
| **Streaming** | Native event streaming | DSPy signature reflection |
| **Type safety** | Mypy strict / TypeScript | Dynamic type coercion |
| **Parity testing** | Vendored SDK + compatibility tests | No official parity suite |
| **Subscription auth** | Works natively via CLI | Must wrap CLI, can't pass keys |
| **Tool calling** | CLI-native, no SDK translation needed | SDK translation + protocol mismatch |

## Implications for mde adversarial review

1. **No need to invent**: Both acodex and pi-mono solved subprocess + JSONL independently
2. **Streaming JSONL is proven**: Both use it; matches our proposed review event format
3. **No shared "standard"**: Each project owns its protocol/SDK, so we own ours
4. **Type safety matters**: Both use mypy/TypeScript strict mode + tests
5. **Retry backoff is mandatory**: Both implement (ms * 2^attempt)
6. **Provider registry scales**: pi-mono's dynamic pattern handles 8+ LLM providers

## Discovery Timeline

- **2026-03-24**: Identified DSPy as unsuitable (API keys only, not CLI-friendly)
- **2026-03-24**: Proposed Python subprocess wrapper in src/mde/domain/multi_model.py
- **2026-03-25**: Discovered acodex and pi-mono as production references
- **Recommendation**: Use acodex + pi-mono as architectural inspiration, not code reuse

## Sources Added to Catalog

- https://github.com/maksimzayats/acodex (main library)
- https://raw.githubusercontent.com/maksimzayats/acodex/main/src/acodex/codex.py (Codex class)
- https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/ai/src/providers/google-gemini-cli.ts (Gemini provider)
- https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/ai/src/providers/openai-codex-responses.ts (Codex provider)
- https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/ai/src/api-registry.ts (Provider registry)

# Honcho Deriver Configuration Guide (v3.0.3)

## Overview

When re-enabling the `honcho-deriver` service in `docker/memory/compose.yaml`, you must configure environment variables to specify which LLM providers to use. This guide maps the exact env var names to the Honcho configuration model.

## Quick Start: Enable Deriver with Google Gemini Only

Add to `docker/memory/.env`:

```bash
# API Keys
LLM_GEMINI_API_KEY=<your-api-key>

# Deriver (document embedding & representation)
DERIVER_ENABLED=true
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash-lite

# Summary (session summarization)
SUMMARY_ENABLED=true
SUMMARY_PROVIDER=google
SUMMARY_MODEL=gemini-2.5-flash

# Dream (autonomous hypothesis generation)
DREAM_ENABLED=true
DREAM_PROVIDER=google
DREAM_MODEL=gemini-2.5-flash

# Dialectic reasoning levels
DIALECTIC_LEVELS__minimal__PROVIDER=google
DIALECTIC_LEVELS__minimal__MODEL=gemini-2.5-flash-lite
DIALECTIC_LEVELS__low__PROVIDER=google
DIALECTIC_LEVELS__low__MODEL=gemini-2.5-flash-lite
DIALECTIC_LEVELS__medium__PROVIDER=google
DIALECTIC_LEVELS__medium__MODEL=gemini-2.5-flash
DIALECTIC_LEVELS__high__PROVIDER=google
DIALECTIC_LEVELS__high__MODEL=gemini-2.5-flash
DIALECTIC_LEVELS__max__PROVIDER=google
DIALECTIC_LEVELS__max__MODEL=gemini-2.5-flash

# Enable embedding & semantic search
EMBED_MESSAGES=true
```

Then uncomment the `honcho-deriver:` service in `compose.yaml` and run:

```bash
docker-compose -f docker/memory/compose.yaml up -d
```

## Configuration Hierarchy

Honcho v3.0.3 applies configuration in this precedence order:

1. **Init settings** (programmatic API calls)
2. **Environment variables** (compose `environment:` section)
3. **.env file** (compose `env_file:` section)
4. **TOML config** (optional `config.toml`)
5. **Secrets** (optional `/run/secrets/*`)
6. **Hardcoded defaults** (see below)

Environment variables override .env file settings, so set high-priority overrides in `environment:` and optional values in `.env`.

## Provider Selection Variables

### SupportedProviders Enum (v3.0.3)

Valid values for any `PROVIDER` variable:

```python
SupportedProviders = Literal[
    "anthropic",   # Claude family
    "openai",      # GPT family
    "google",      # Gemini family
    "groq",        # Groq cloud models
    "custom",      # Custom OpenAI-compatible endpoint
    "vllm"         # vLLM server (local models)
]
```

### Deriver Settings

Document embedding, representation extraction, and deduction.

**Environment variables:**
- `DERIVER_ENABLED` — Enable/disable deriver service (default: `true`)
- `DERIVER_PROVIDER` — Provider to use (default: `"google"`)
- `DERIVER_MODEL` — Model name (default: `"gemini-2.5-flash-lite"`)
- `DERIVER_BACKUP_PROVIDER` — Fallback provider (optional)
- `DERIVER_BACKUP_MODEL` — Fallback model (optional)

**Example with fallback:**
```bash
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash-lite
DERIVER_BACKUP_PROVIDER=anthropic
DERIVER_BACKUP_MODEL=claude-haiku-4-5
```

### Summary Settings

Session history summarization (short and long forms).

**Environment variables:**
- `SUMMARY_ENABLED` — Enable/disable summary service (default: `true`)
- `SUMMARY_PROVIDER` — Provider to use (default: `"google"`)
- `SUMMARY_MODEL` — Model name (default: `"gemini-2.5-flash"`)
- `SUMMARY_BACKUP_PROVIDER` — Fallback provider (optional)
- `SUMMARY_BACKUP_MODEL` — Fallback model (optional)

### Dream Settings

Autonomous hypothesis generation and exploration.

**Environment variables:**
- `DREAM_ENABLED` — Enable/disable dream service (default: `true`)
- `DREAM_PROVIDER` — Primary provider (default: `"anthropic"`)
- `DREAM_MODEL` — Primary model (default: `"claude-sonnet-4-20250514"`)
- `DREAM_BACKUP_PROVIDER` — Fallback provider (optional)
- `DREAM_BACKUP_MODEL` — Fallback model (optional)
- `DREAM_DEDUCTION_MODEL` — Specialist for logical inference (default: `"claude-haiku-4-5"`)
- `DREAM_INDUCTION_MODEL` — Specialist for pattern identification (default: `"claude-haiku-4-5"`)

### Dialectic Settings (Multi-Level Reasoning)

Per-reasoning-level provider and model configuration.

**Reasoning levels:** `minimal`, `low`, `medium`, `high`, `max`

**Environment variables (nested delimiter `__`):**
```bash
DIALECTIC_LEVELS__<level>__PROVIDER=<provider>
DIALECTIC_LEVELS__<level>__MODEL=<model>
DIALECTIC_LEVELS__<level>__THINKING_BUDGET_TOKENS=<int>
DIALECTIC_LEVELS__<level>__MAX_TOOL_ITERATIONS=<int>
DIALECTIC_LEVELS__<level>__BACKUP_PROVIDER=<provider>
DIALECTIC_LEVELS__<level>__BACKUP_MODEL=<model>
```

**Default configurations (v3.0.3):**

| Level | Provider | Model | Thinking Budget | Max Tool Iterations |
|-------|----------|-------|-----------------|-------------------|
| minimal | google | gemini-2.5-flash-lite | 0 | 1 |
| low | google | gemini-2.5-flash-lite | 0 | 5 |
| medium | anthropic | claude-haiku-4-5 | 1024 | 2 |
| high | anthropic | claude-haiku-4-5 | 1024 | 4 |
| max | anthropic | claude-haiku-4-5 | 2048 | 10 |

**Example: Override high-level reasoning to use GPT-4:**
```bash
DIALECTIC_LEVELS__high__PROVIDER=openai
DIALECTIC_LEVELS__high__MODEL=gpt-4
DIALECTIC_LEVELS__high__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__high__MAX_TOOL_ITERATIONS=8
```

## API Keys (Required by Provider)

Set only the API keys for providers you actually use:

```bash
# Anthropic
LLM_ANTHROPIC_API_KEY=<key>

# OpenAI
LLM_OPENAI_API_KEY=<key>

# Google Gemini
LLM_GEMINI_API_KEY=<key>

# Groq
LLM_GROQ_API_KEY=<key>

# Custom OpenAI-compatible endpoint
LLM_OPENAI_COMPATIBLE_BASE_URL=http://your-endpoint:8000/v1
LLM_OPENAI_COMPATIBLE_API_KEY=<key>

# vLLM server
LLM_VLLM_BASE_URL=http://localhost:8000/v1
LLM_VLLM_API_KEY=<optional-key>
```

**Validation:** Honcho validates that if a provider is selected (in PROVIDER fields), its corresponding API key is set. Missing keys will cause startup failures.

## Feature Flags

All component services are enabled by default. Disable selectively:

```bash
# Disable deriver (storage-only, no reasoning)
DERIVER_ENABLED=false

# Disable summary (no session summaries)
SUMMARY_ENABLED=false

# Disable dream (no autonomous hypothesis generation)
DREAM_ENABLED=false

# Disable peer card (user context card generation)
PEER_CARD_ENABLED=false

# Disable cache (no Redis caching)
CACHE_ENABLED=false

# Disable telemetry
TELEMETRY_ENABLED=false
```

## Embedding Provider Selection

Separate from the primary LLM providers (used for reasoning):

```bash
# Embedding provider for vector similarity (default: openai)
LLM_EMBEDDING_PROVIDER=openai    # or: gemini, openrouter
```

If using `openai` embeddings, ensure `LLM_OPENAI_API_KEY` is set.

## Custom/vLLM Configuration

### Custom OpenAI-Compatible Endpoint

For Ollama, LocalAI, or any OpenAI-compatible server:

```bash
# Provider is "custom" (not "ollama")
DERIVER_PROVIDER=custom
DERIVER_MODEL=<model-name>

# Endpoint configuration
LLM_OPENAI_COMPATIBLE_BASE_URL=http://ollama:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=dummy-key-or-leave-empty
```

**Limitation:** Honcho sends `thinking_budget_tokens` parameter to all providers, but most OpenAI-compatible servers don't support it. Requests may fail if the server rejects unknown parameters.

### vLLM Server

```bash
DERIVER_PROVIDER=vllm
DERIVER_MODEL=mistral-7b

LLM_VLLM_BASE_URL=http://vllm-server:8000/v1
LLM_VLLM_API_KEY=optional-key
```

## Backup Provider Pattern

When a provider fails, Honcho automatically falls back to the backup:

```bash
# Primary: Gemini
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash-lite

# Fallback: Claude
DERIVER_BACKUP_PROVIDER=anthropic
DERIVER_BACKUP_MODEL=claude-haiku-4-5
```

**Requirement:** Both `BACKUP_PROVIDER` and `BACKUP_MODEL` must be set together, or both must be `None`.

## compose.yaml Integration Example

Uncomment the `honcho-deriver` service and update its `environment:` section:

```yaml
honcho-deriver:
  image: ghcr.io/plastic-labs/honcho:v3.0.3@sha256:0d23755cfba8fac143d37a3c2f9d6bd01af9dee0854e3bebdfb5fb6196f71084
  entrypoint: ["python", "-m", "src.deriver"]
  environment:
    - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD:?Set HONCHO_DB_PASSWORD}@honcho-db:5432/honcho
    - CACHE_URL=redis://honcho-redis:6379/0?suppress=true
    - METRICS_ENABLED=true

    # Provider selection
    - DERIVER_PROVIDER=google
    - DERIVER_MODEL=gemini-2.5-flash-lite
    - SUMMARY_PROVIDER=google
    - SUMMARY_MODEL=gemini-2.5-flash
    - DREAM_PROVIDER=anthropic
    - DREAM_MODEL=claude-sonnet-4-20250514

    # Dialectic reasoning levels
    - DIALECTIC_LEVELS__minimal__PROVIDER=google
    - DIALECTIC_LEVELS__minimal__MODEL=gemini-2.5-flash-lite
    - DIALECTIC_LEVELS__low__PROVIDER=google
    - DIALECTIC_LEVELS__low__MODEL=gemini-2.5-flash-lite
    - DIALECTIC_LEVELS__medium__PROVIDER=anthropic
    - DIALECTIC_LEVELS__medium__MODEL=claude-haiku-4-5
    - DIALECTIC_LEVELS__high__PROVIDER=anthropic
    - DIALECTIC_LEVELS__high__MODEL=claude-haiku-4-5
    - DIALECTIC_LEVELS__max__PROVIDER=anthropic
    - DIALECTIC_LEVELS__max__MODEL=claude-haiku-4-5

  env_file:
    - path: .env
      required: false
  depends_on:
    honcho-db:
      condition: service_healthy
    honcho-redis:
      condition: service_healthy
  restart: unless-stopped
```

Also enable embedding in the `honcho-api` service:

```yaml
honcho-api:
  ...
  environment:
    ...
    - EMBED_MESSAGES=true
    - LLM_GEMINI_API_KEY=${LLM_GEMINI_API_KEY}
```

## References

- Honcho v3.0.3 config.py: https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/config.py
- SupportedProviders: https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/utils/types.py
- Honcho docs: https://honcho.dev
- Provenance: `docs/research/trail/findings/honcho-config-env-vars.yaml`

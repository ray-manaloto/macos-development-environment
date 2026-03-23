
| [x] | Honcho Setup Migration (OpenClaw Skills) | https://github.com/dvcrn/openclaw-skills-marketplace | Skills Marketplace | PRODUCTION — Plugins: ajspig/honcho-setup, vvoruganti/honcho. Install @honcho-ai/openclaw-honcho and migrate legacy file-based memory (USER.md, MEMORY.md, IDENTITY.md, etc.) to managed Honcho or self-hosted instances. Uploads to api.honcho.dev or HONCHO_BASE_URL with user confirmation. |
| [x] | Osaurus Honcho Plugin | https://github.com/VibeDeez/Honcho-Osaurus-Plugin | macOS Osaurus | COMMUNITY — Native macOS plugin for Honcho v3 REST API. Provides persistent cross-session memory for AI agents on Osaurus. |
| [x] | Discord Bot with Honcho | https://github.com/vintrocode/simple-honcho-discord-bot | Discord | COMMUNITY — Demo Discord AI bot with Honcho user context management. Built with Langchain using OpenAI LLM. Shows Honcho's applicability to chat platforms. |
| [x] | Honcho Memory Agent | https://github.com/plastic-labs/honcho-memory-agent | Standalone | PRODUCTION — Agent-focused memory system (plastic-labs). Updated 2026-03-09. |
| [x] | Nanobot Honcho | https://github.com/plastic-labs/nanobot-honcho-archive | Standalone | ARCHIVED — Ultra-lightweight AI assistant with Honcho-powered persistent memory. Historical reference for minimal agent setup. |
| [x] | Reachy Mini Honcho | https://github.com/plastic-labs/reachy-mini-honcho | Robotics | PRODUCTION — Realtime chat integration with gpt-realtime + Honcho memory for embodied agents. Shows memory integration with streaming APIs. |

### Key Insights from Plugin Ecosystem

1. **Multi-Platform Strategy**: Honcho maintains consistent plugins across Claude Code, Cursor, OpenClaw, and community platforms. Same config file works everywhere.

2. **Session Flexibility**: Three strategies (per-directory default, git-branch, chat-instance) accommodate different workflows without code changes.

3. **Cross-Tool Context Linking**: Claude Code can read Cursor's memory and vice versa via `linkedHosts` config. Enables team and multi-tool workflows.

4. **Team Memory**: Built-in multi-user support via shared workspaces with automatic session namespacing (peerName-project). No custom orchestration needed.

5. **MCP Tool Access**: All memory operations exposed via MCP (search, chat, create_conclusion) — agents can query memory mid-conversation without file reads.

6. **No Anthropic Official Registry**: anthropics/claude-code-plugins and anthropics/awesome-claude-code repos return 404. Honcho plugins are published in plastic-labs/claude-honcho marketplace, not Anthropic's registry.

---

## Docker Infrastructure — Honcho Memory Stack

| Status | Source | URL | Verdict | In NB |
|--------|--------|-----|---------|-------|
| [x] | plastic-labs/honcho GitHub | https://github.com/plastic-labs/honcho | CRITICAL — Spec adversarial review found 3 failures: missing docker/ COPY, pgrep unavailable, pgvector tag mismatch | No |
| [x] | plastic-labs/honcho Dockerfile | https://raw.githubusercontent.com/plastic-labs/honcho/main/Dockerfile | FAILURE — No COPY docker/ statement; entrypoint ["sh", "docker/entrypoint.sh"] will fail at runtime | No |
| [x] | plastic-labs/honcho entrypoint.sh | https://raw.githubusercontent.com/plastic-labs/honcho/main/docker/entrypoint.sh | EXISTS but not copied into image by Dockerfile | No |
| [x] | plastic-labs/honcho docker-compose.yml.example | https://raw.githubusercontent.com/plastic-labs/honcho/main/docker-compose.yml.example | Uses entrypoint: ["sh", "docker/entrypoint.sh"] (upstream works via build context; our image will not) | No |
| [x] | pgvector/pgvector Docker Hub | https://registry.hub.docker.com/v2/repositories/pgvector/pgvector/tags | Tag mismatch: spec uses pg15 (doesn't exist); actual: pg15-trixie, 0.8.2-pg15-trixie | No |
| [x] | redis Docker Hub | https://hub.docker.com/_/redis/tags | PASS: redis:8.2 exists (8.2.5 latest patch) | No |
| [x] | python:3.13-slim-bookworm base image | https://hub.docker.com/_/python/tags | FAILURE: Does not include procps; pgrep healthcheck will fail | No |

---

## Memory System Alternatives Survey (2026-03-23)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | mem0 README | https://github.com/mem0ai/mem0 | Y Combinator S24; requires paid LLM APIs (OpenAI/Anthropic/Groq default); supports Ollama for embeddings only, not primary LLM | HIGH |
| [x] | mem0 pyproject.toml | https://raw.githubusercontent.com/mem0ai/mem0/main/pyproject.toml | Dependencies: `openai>=1.90.0`, `groq>=0.3.0`, `ollama>=0.3.0`; LLM is non-negotiable in config | HIGH |
| [x] | Letta README | https://github.com/letta-ai/letta | Formerly MemGPT; stateful agents with memory blocks; self-hosted FastAPI backend available | HIGH |
| [x] | Letta pyproject.toml | https://raw.githubusercontent.com/letta-ai/letta/main/pyproject.toml | Dependencies: `anthropic>=0.75.0`, `openai>=2.11.0`, `mistralai>=1.8.1`; examples assume paid LLM endpoints | HIGH |
| [x] | Zep README | https://github.com/getzep/zep | Community edition deprecated; cloud-only SaaS now; temporal knowledge graphs abandoned for open-source | HIGH |
| [x] | Zep legacy status | https://github.com/getzep/zep/blob/main/README.md#community-edition-legacy | "Zep Community Edition is no longer supported and has been deprecated" — official statement | HIGH |
| [x] | ChromaDB README | https://github.com/chroma-core/chroma | Apache 2.0; embedded + client-server modes; sentence-transformers for local embeddings (no API needed) | MEDIUM |
| [x] | ChromaDB pyproject.toml | https://raw.githubusercontent.com/chroma-core/chroma/main/pyproject.toml | Core deps: `onnxruntime`, `numpy`, `tokenizers` (all local); zero cloud dependencies | MEDIUM |

---

---

## Honcho Pricing & Managed SaaS

| Status | Source | URL | Verdict | Finding ID |
|--------|--------|-----|---------|------------|
| [x] | Honcho GitHub README | https://github.com/plastic-labs/honcho | CONFIRMED — Free tier: $100 credits on app.honcho.dev; paid tier details not public; self-hosting available | honcho-pricing-saas |
| [x] | Honcho Homepage | https://honcho.dev | NO PRICING PAGE — 404 on /pricing route; homepage mentions SDK/docs/chat but no tier info | honcho-pricing-saas |
| [x] | Honcho Managed SaaS | https://app.honcho.dev | STUB PAGE — 200 status but insufficient content; authentication/signup required | honcho-pricing-saas |

---

## Docker Security & Container Isolation (Adversarial Review — 2026-03-23)

| Status | Source | URL | Verdict | Finding ID |
|--------|--------|-----|---------|------------|
| [x] | Docker Engine Security Docs | https://docs.docker.com/engine/security/ | CONFIRMED — Namespaces, cgroups, cap_drop guidance; notes cross-daemon isolation limits | adversarial-security-review |
| [x] | Docker Resource Constraints | https://docs.docker.com/engine/containers/resource_constraints/ | CONFIRMED — mem_limit/cpus best practices; OOM kill behavior; 1g memory adequate for containment | adversarial-security-review |
| [x] | Docker Secrets (Swarm) | https://docs.docker.com/engine/swarm/secrets/ | REFERENCE — /run/secrets mount point; limitation: Swarm-only (not Compose); alternative to env vars | adversarial-security-review |
| [x] | Docker Base Images & Pinning | https://docs.docker.com/build/building/base-images/ | CONFIRMED — Digest pinning critical for supply chain security; tag re-push risk documented | adversarial-security-review |
| [x] | plastic-labs/honcho config.py | https://github.com/plastic-labs/honcho/blob/main/src/config.py | CRITICAL — USE_AUTH defaults False; model validator requires JWT_SECRET when enabled; NO enforcement on disabled | adversarial-security-review |
| [x] | plastic-labs/honcho docker-compose.yml.example | https://github.com/plastic-labs/honcho/blob/main/docker-compose.yml.example | CRITICAL — Uses POSTGRES_HOST_AUTH_METHOD=trust in dev; password=postgres (unversioned); no requirepass on Redis | adversarial-security-review |

---

## Honcho v3.0.3 OpenAI-Compatible Integration (2026-03-23)

| Status | Source | URL | Verdict | Finding ID |
|--------|--------|-----|---------|------------|
| [x] | Honcho v3.0.3 config.py | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/config.py | CONFIRMED — LLM_OPENAI_COMPATIBLE_BASE_URL and LLM_OPENAI_COMPATIBLE_API_KEY fully implemented | honcho-ollama-viability |
| [x] | Honcho v3.0.3 clients.py | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/utils/clients.py | CRITICAL — Thinking budget tokens sent to custom provider (unsupported by Ollama); structured output incompatible | honcho-ollama-viability |
| [x] | Honcho v3.0.3 types.py | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/utils/types.py | CONFIRMED — "custom" provider in SupportedProviders literal; routed to AsyncOpenAI client | honcho-ollama-viability |
| [x] | Honcho v3.0.3 embedding_client.py | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/embedding_client.py | LIMITATION — Embedding providers hardcoded by name (openai/gemini/openrouter); no custom URL support | honcho-ollama-viability |

---

## Python Standalone Packaging for Docker (2026-03-23)

| Status | Source | URL | Verdict | Finding ID |
|--------|--------|-----|---------|------------|
| [x] | Python zipapp module | https://docs.python.org/3/library/zipapp.html | CONFIRMED — Built-in PEP 441; creates .pyz files; no automatic dependency bundling | finding-python-zipapp-standalone |
| [x] | shiv (LinkedIn) GitHub | https://github.com/linkedin/shiv | **RECOMMENDED** — Automatic zipapp + pip dependency bundling; single .pyz with all deps included | finding-shiv-dependencies |
| [x] | shiv README | https://raw.githubusercontent.com/linkedin/shiv/master/README.md | CONFIRMED — shiv supports -c (console script), -r (requirements), all pip install options | finding-shiv-dependencies |
| [x] | PyInstaller | https://github.com/pyinstaller/pyinstaller | EVALUATED — Bundles interpreter + code (100-200MB), overkill for Docker, better for standalone CLI distribution | finding-pyinstaller-tradeoffs |
| [x] | Nuitka | https://nuitka.net/ | NOT RECOMMENDED — Python-to-C compiler; adds C build dependency; not designed for packaging, only performance | finding-nuitka-c-compilation |
| [x] | PEP 441 (Python ZIP Application Support) | https://www.python.org/dev/peps/pep-0441/ | REFERENCE — Spec for zipapp format; shiv implements PEP 441 + dependency bundling | finding-python-zipapp-standalone |
| [x] | Docker Python Containerization | https://docs.docker.com/language/python/build-images/ | REFERENCE — Best practices for Python in Docker; multi-stage builds recommended | finding-wheel-pip-approach |
| [x] | mde pyproject.toml (local) | file:///Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/pyproject.toml | CONFIRMED — mde has 7 dependencies: pydantic, httpx, loguru, openlit, claude-agent-sdk, claude-code-analytics, orjson | finding-shiv-dependencies |

### Decision Outcome: shiv for healthcheck packaging

**Recommendation:** Use shiv in multi-stage Dockerfile to bundle healthcheck.py + mde dependencies into standalone .pyz
- Build stage: installs shiv, creates .pyz with all dependencies
- Runtime stage: COPY .pyz into python:3.13-slim-bookworm, execute with Python
- Quality gates: healthcheck.py source passes ruff/ty/pytest before shiv packages it
- Result: No pip/uv/venv in runtime container, all deps included in single file

See deep review: `docs/research/trail/deep-reviews/python-docker-packaging-strategies.md`

| [x] | codex CLI v0.116.0 (OpenAI) | https://openai.com/codex/ | CLI Tool | INSTALLED — Non-interactive exec via `codex exec` and `codex review` commands. Subscription auth (no API keys). Available at /Users/rmanaloto/.local/share/mise/installs/codex/0.116.0/codex |
| [x] | gemini CLI v0.34.0 (Google) | https://github.com/google-gemini/gemini-cli | CLI Tool | INSTALLED — Headless mode via `-p/--prompt` flag and stdin support. Subscription auth. Available at /Users/rmanaloto/.local/share/mise/installs/gemini-cli/0.34.0/bin/gemini |
| [x] | claude CLI v2.1.81 (Anthropic) | https://github.com/anthropics/claude-code | CLI Tool | INSTALLED — Non-interactive mode via `--print` and `--p` flags. Subscription auth. Available at /Users/rmanaloto/.local/share/mise/installs/npm-anthropic-ai-claude-code/2.1.81/bin/claude |
| [x] | claude-code-skills Plugin Suite | https://github.com/levnikolaevich/claude-code-skills | Claude Code Plugin | EVALUATION — 7 plugins + 128 skills with native multi-model review (ln-310, ln-510, ln-813). Requires @anthropic/codex-cli + @google/gemini-cli + API authentication. MIT license. VERDICT: SKIP — Codex requires OpenAI API key (gpt-5.4); Gemini requires Google auth (gemini-3-flash-preview). Both incompatible with zero-API-keys constraint. See finding-claude-code-skills-integration-eval.yaml for detailed evaluation. |
| [x] | DSPy Framework | https://github.com/stanfordnlp/dspy | Python Framework | EVALUATION — Stanford NLP framework for composable LLM pipelines. FINDING: Requires API keys, not subscription auth. Not suitable for CLI orchestration of subscription-based tools. |
| [x] | BAML Framework | https://github.com/boundaryml/baml | Python Framework | EVALUATION — Declarative markup for LLM calls with type safety. FINDING: SDK-first design, requires API keys. Not CLI-first. |
| [x] | LiteLLM Proxy | https://github.com/BerriAI/litellm | Python Framework | EVALUATION — API abstraction layer for multi-model routing. FINDING: API key wrapper, not subscription-friendly. Has CLI but primarily SDK-based. |
| [x] | Instructor Library | https://github.com/jxnl/instructor | Python Framework | EVALUATION — Structured output generation via Pydantic. FINDING: SDK-only, requires direct API access. Not CLI-compatible. |
| [x] | PydanticAI Framework | https://github.com/pydantic/pydantic-ai | Python Framework | EVALUATION — Agentic workflows with tool integration. FINDING: SDK-based, requires API keys. Not CLI-oriented. |
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

## Claude Code Hooks Reference (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | Claude Code hooks reference | https://code.claude.com/docs/en/hooks | Complete inventory of 22 hook events: 5 lifecycle, 5 interaction, 4 agent/team, 2 security, 2 filesystem, 3 notification/elicitation. Blocking behavior varies by event. Matcher field matches tool names, permission types, config keys, agent names. | BASELINE |
| [x] | Claude Code overview | https://code.claude.com/docs/en/overview | General Claude Code documentation; includes hook lifecycle diagrams and execution model | SUPPORT |
| [x] | Claude Agent SDK Python docs | https://platform.claude.com/docs/en/agent-sdk/python | Agent SDK provides types for subset of hook events (12 events documented in SDK types module); CLI adds 10 additional events not in SDK | SUPPORT |

---

## Multi-Model Orchestration Frameworks (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | DSPy GitHub | https://github.com/stanfordnlp/dspy | Framework for "programming rather than prompting" LMs; pip installable; supports modular composition; critical unknown: CLI backend support | MEDIUM |
| [x] | DSPy Docs | https://dspy.ai | Declarative framework for building optimized AI systems; recent research (GEPA Jul'25); supports RAG/agents/classifiers | SUPPORT |
| [x] | BAML GitHub | https://github.com/BoundaryML/baml | Schema-first language compiling to Python/TS/Ruby/Go; hardcoded OpenAI backends in docs; supports tool-calling, streaming, retries | MEDIUM |
| [x] | Instructor GitHub | https://github.com/jxnl/instructor | Structured output extraction using Pydantic; not full orchestration; requires provider client (OpenAI pattern) | LOW |
| [x] | LiteLLM GitHub | https://github.com/BerriAI/litellm | Unified API wrapper for multiple LLM providers; unknown: CLI provider support | MEDIUM |

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
| [x] | Honcho v3.0.3 SELECTED_PROVIDERS validation | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/utils/clients.py | CRITICAL — LLM provider validation happens at module load; doesn't check ENABLED flags; blocks API startup without keys | honcho-api-only-mode |
| [x] | Honcho v3.0.3 EmbeddingClient lazy loading | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/embedding_client.py | CONFIRMED — Singleton with double-checked locking; client created on first use, not at module load; no startup blocker | honcho-api-only-mode |
| [x] | Honcho v3.0.3 messages router | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/routers/messages.py | CONFIRMED — Router imports deriver.enqueue (which chains to clients.py import and validation) | honcho-api-only-mode |

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
| [x] | Honcho v3.0.3 API startup analysis | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/main.py | VERIFIED: API startup does not instantiate LLM clients; no module-level imports of embedding_client | ADVERSARIAL |
| [x] | Honcho v3.0.3 EmbeddingClient lazy init | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/embedding_client.py | VERIFIED: Uses singleton with deferred loading; _instance stays None until first embed() call | ADVERSARIAL |
| [x] | Honcho v3.0.3 message creation flow | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/crud/message.py | VERIFIED: Embedding only triggered if settings.EMBED_MESSAGES=true; can be disabled via env var | ADVERSARIAL |
| [x] | Honcho v3.0.3 SupportedProviders enum | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/utils/types.py | REFERENCE — SupportedProviders literal: "anthropic", "openai", "google", "groq", "custom", "vllm" | honcho-config-env-vars |
| [x] | Honcho v3.0.3 config env vars | https://raw.githubusercontent.com/plastic-labs/honcho/v3.0.3/src/config.py | REFERENCE — Comprehensive mapping: DERIVER_*, SUMMARY_*, DIALECTIC_LEVELS__*, DREAM_*, LLM_* API keys, ENABLED flags | honcho-config-env-vars |
| [x] | honcho-ai v2.0.1 PyPI | https://pypi.org/project/honcho-ai/ | BASELINE — Complete SDK API documentation extracted via package introspection; 32 API-safe operations, 11 LLM-dependent operations | honcho-sdk-api-baseline-v2.0.1 |
| [x] | honcho-ai GitHub repository | https://github.com/plastic-labs/honcho | SOURCE — Primary Honcho development repository (plastic-labs); used for API reference and Docker specs | honcho-sdk-api-baseline-v2.0.1 |
| [x] | honcho-ai 2.0.1 package introspection | local:honcho-ai==2.0.1 | VERIFIED — Installed via pip; examined all class methods for Honcho, HonchoAio, Peer, PeerAio, Session, SessionAio | honcho-sdk-api-baseline-v2.0.1 |

---

## Claude Code Dream Memory Consolidation & Telemetry Alternatives (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | Claude Code dream memory consolidation | https://raw.githubusercontent.com/Piebald-AI/claude-code-system-prompts/main/system-prompts/agent-prompt-dream-memory-consolidation.md | CONFIRMED — System prompt (ccVersion 2.1.78+) implements 4-phase memory consolidation: Orient > Gather > Consolidate > Prune. Operates on file-based memory directory, not session transcripts. Target: local session memory hygiene, not durable persistence. | memory-consolidation-alternatives |
| [x] | Piebald-AI Claude Code system prompts | https://github.com/Piebald-AI/claude-code-system-prompts | SOURCE — Complete inventory of Claude Code system prompts for each version; includes dream, plan, explore, and utility prompts; updated per release | memory-consolidation-alternatives |
| [x] | cxdb: Cypher eXchange Graph Database | https://github.com/dexterpratt/cxdb | CONFIRMED — Lightweight in-memory graph DB with Cypher operations; backed by CX2 format; NOT related to AI memory or telemetry consolidation | memory-consolidation-alternatives |
| [x] | OpenLIT: OpenTelemetry-native AI observability | https://github.com/openlit/openlit | RECOMMENDED PRIMARY — Stars: 2,319; Python; self-hostable; OTEL-native; zero LLM key requirement; supports 50+ LLM providers, GPU monitoring, evals, prompt management, vault, playground. Best fit for user's "self-hosted + no LLM keys" constraint. | memory-consolidation-alternatives |
| [x] | Langfuse: Open source LLM engineering platform | https://github.com/langfuse/langfuse | RECOMMENDED SECONDARY — Stars: 23,679; TypeScript; self-hostable (Docker Compose); OTEL compatible; most mature ecosystem; YC W23; best trace UI + session storage. Requires Docker Compose setup effort similar to OpenLIT. | memory-consolidation-alternatives |
| [x] | Helicone: Open source LLM observability | https://github.com/helicone/helicone | EVALUATED — Stars: 5,302; TypeScript; unknown self-host capability; one-line integration; YC W23. Status: NEEDS INVESTIGATION on OTEL compatibility and Claude Code telemetry support. | memory-consolidation-alternatives |
| [x] | Arize Phoenix: AI observability and evaluation | https://github.com/arize-ai/phoenix | EVALUATED — Stars: 9,013; Jupyter Notebook primary; local ML observability possible; Arize is commercial backing (Phoenix status ambiguous). Status: DEFER pending OTEL compatibility + self-host story verification. | memory-consolidation-alternatives |
| [x] | Braintrust: Tracing & evals for AI apps | https://github.com/Braintrustdata/braintrust-sdk-javascript | EVALUATED — SDKs: Java (17 stars), JS (11 stars); appears SaaS-first; proprietary SDK integration (not OTEL). Status: REJECT for user's "no LLM keys + self-hosted" constraint. | memory-consolidation-alternatives |
| [x] | Lunary: Python SDK for AI analytics | https://github.com/lunary-ai/lunary-py | EVALUATED — Stars: 20; Python client available; appears SaaS-first; unknown OTEL support. Status: REJECT for user's constraint set; low ecosystem maturity. | memory-consolidation-alternatives |
| [x] | Literal AI: Status unknown | (reference only in example projects) | NOT FOUND — Mentioned in maritalk-chat example but no primary GitHub repo located. Status: SKIP; insufficient evidence of active project; possibly defunct or renamed. | memory-consolidation-alternatives |

---

## Obsidian + YouTube Integration Patterns (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | Claude Code + Obsidian = UNSTOPPABLE | https://www.youtube.com/watch?v=eRr2rTKriDM | CONFIRMED — Obsidian provides free persistent memory across Claude Code sessions. Symbiotic relationship: Obsidian vault as persistent canvas, Claude Code as automation engine. Setup demo covers personal assistant workflow. | obsidian-youtube-integration |
| [x] | Claude Code + NotebookLM + Obsidian = GOD MODE | https://www.youtube.com/watch?v=kU3qYQ7ACMA | CONFIRMED — 3-layer workflow: YouTube search → NotebookLM synthesis → Obsidian vault storage. Claude Code orchestrates entire research pipeline. Setup <30 minutes. Demonstrated use case: custom research agent with deliverables. | obsidian-youtube-integration |
| [x] | Claude Code Turned Obsidian Into My Dream Second Brain | https://www.youtube.com/watch?v=2kbINqpluM0 | CONFIRMED — One-command vault setup; slash commands (/daily, /standup, /tldr) maintain vault; file processing pipeline (PDF/DOCX → clean notes). Solves Obsidian adoption friction via Claude Code integration. Public GitHub repo. | obsidian-youtube-integration |
| [x] | I Built My Second Brain with Claude Code + Obsidian + Skills | https://www.youtube.com/watch?v=jYMhDEzNAN0 | CONFIRMED — Dozens of Claude Code skills powering research loop. Architecture: Claude Code (workhorse) + Obsidian (canvas) + Skills (knowledge download). Enables research → ideate → organize workflow. Public GitHub repo (second-brain-skills). | obsidian-youtube-integration |
| [x] | How To 10x Your Notes: Obsidian + Claude AI Agents | https://www.youtube.com/watch?v=d7Pb73dbcIM | CONFIRMED — Vault creation, AI rules, agent setup. Tool stack: Obsidian CLI + Claude Code + WisprFlow + Cursor. References Claude Code documentation for agent patterns. | obsidian-youtube-integration |
| [x] | obsidian-automation skill | https://skills.sh/claude-office-skills/skills/obsidian-automation | CONFIRMED — Claude Code skill for Obsidian vault automation. Slash commands integrated with Claude Code. Direct note creation, file processing, templating. | obsidian-skills-registry |
| [x] | obsidian-knowledge skill | https://skills.sh/zhuxining/skills/obsidian-knowledge | CONFIRMED — Knowledge base management + retrieval. Likely RAG-adjacent (knowledge graph or note network). Cross-vault querying and knowledge synthesis. | obsidian-skills-registry |
| [x] | obsidian-rag skill | https://skills.sh/derekhsu/obsidian-rag/obsidian-rag | CONFIRMED — Retrieval-Augmented Generation with Obsidian vault as source. Makes video content searchable via embeddings over notes. Critical for RAG-querying video transcripts/metadata. | obsidian-skills-registry |
| [x] | Early AI Adopters second-brain repo | https://github.com/earlyaidopters/second-brain | SOURCE — Public GitHub repo with one-command Obsidian vault setup. Contains slash commands and file processing pipeline implementation. | obsidian-youtube-integration |
| [x] | Cole second-brain-skills repo | https://github.com/coleam00/second-brain-skills | SOURCE — Claude Code skills for second brain research workflow. Catalog of dozens of skills. | obsidian-youtube-integration |

---

## YouTube Transcript & Video Analysis Skills Survey (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | intellectronica youtube-transcript | https://skills.sh/intellectronica/agent-skills/youtube-transcript | LIGHTWEIGHT — Extracts transcripts from caption-enabled videos via youtube-transcript-api; no audio transcription fallback; quality 3/5 | youtube-transcript-skills |
| [x] | composiohq youtube-downloader | https://skills.sh/composiohq/awesome-claude-skills/youtube-downloader | ROBUST DOWNLOADER — yt-dlp wrapper for video/audio; quality/format control; quality 4/5; primary use: acquire content for Whisper transcription | youtube-transcript-skills |
| [x] | shipshitdev youtube-video-analyst | https://skills.sh/shipshitdev/library/youtube-video-analyst | FORENSIC ANALYSIS — 11-section viral mechanics analysis (hooks, structure, retention, emotion, storytelling, linguistics, algorithm signals, CTA, viral coefficient, templates, playbook); quality 5/5; highest-value analysis tool | youtube-transcript-skills |
| [x] | hanzoskill youtube-watcher | https://skills.sh/hanzoskill/youtube-watcher/youtube-watcher | INCOMPLETE — Video summarization skill; documentation incomplete; Vercel checkpoint blocked full access; quality 2/5 | youtube-transcript-skills |
| [x] | skill.fish youtube-transcript-extractor | https://www.skill.fish/skill/youtube-transcript-extractor | BLOCKED — Vercel security checkpoint prevents access; no documentation available | youtube-transcript-skills |
| [x] | skill.fish youtube-feed-monitor | https://www.skill.fish/skill/youtube-feed-monitor | BLOCKED — Vercel security checkpoint prevents access; appears to be feed monitoring, not transcript extraction | youtube-transcript-skills |
| [x] | skill.fish youtube-topic-researcher | https://www.skill.fish/skill/youtube-topic-researcher | BLOCKED — Vercel security checkpoint prevents access; likely content research tool | youtube-transcript-skills |

---

## Chezmoi Plugin Agent Design Research (2026-03-25)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | chezmoi-specialist agent | .claude/agents/chezmoi-specialist.md | CURRENT IMPLEMENTATION — Minimal agent (haiku model, 4 tools: Read/Glob/Grep/Bash, 2 skills: chezmoi-config + chezmoi-workflows). Lacks explicit when-to-use examples and proactive triggers. Pattern reference for enhancement. | chezmoi-plugin-design |
| [x] | mise-specialist agent | rsm-subagents/plugins/mise-toolkit/agents/mise-specialist.md | PATTERN REFERENCE — Mature agent with 4 explicit <example> blocks, <commentary> lines explaining skill triggers, 8 skills, "inherit" model for complex work. Template for chezmoi-specialist enhancement. | chezmoi-plugin-design |
| [x] | chezmoi-config skill | .agents/skills/chezmoi-config/SKILL.md | PRODUCTION READY — Read-only mode with 6 reference docs (template-syntax, external-files, ignore-files, password-managers, scripts, advanced-configuration). Safety constraints forbid `chezmoi apply/update`, allow `chezmoi diff/dry-run/doctor/data/verify/execute-template`. | chezmoi-plugin-design |
| [x] | chezmoi-workflows skill | .agents/skills/chezmoi-workflows/SKILL.md | PRODUCTION READY — 14 workflow sections: status check, track changes, sync, push, setup, config, merge conflicts, validation, forget, templates, safe update, doctor. Comprehensive task reference. | chezmoi-plugin-design |
| [x] | chezmoi drift detection validation | src/mde/validate/chezmoi.py | INTEGRATED — Runs `chezmoi verify --exclude=scripts` on validation. Detects drift (returncode != 0), reports as Severity.WARNING. Already part of `uv run mde-py validate --all`. | chezmoi-plugin-design |
| [x] | chezmoi ecosystem skills analysis | docs/research/trail/findings/finding-chezmoi-mise-skills-ecosystem.yaml | RESEARCH CONFIRMED — No external chezmoi agents in wshobson/agents (31.7K⭐), affaan-m/everything-claude-code (78.8K⭐), or VoltAgent awesome-claude-code-subagents (14.4K⭐). Project implementation is best-in-class. | chezmoi-plugin-design |
| [x] | chezmoi marketplace skills | docs/research/trail/findings/finding-marketplace-chezmoi-mise-search.yaml | ECOSYSTEM SURVEY — terrylica/cc-skills@chezmoi-workflows (85 installs) is highest-adoption external skill; samhvw8/dotfiles@mise-expert (98 installs) for mise; currently mde uses faintghost/skills@chezmoi-config (28 installs, low adoption). | chezmoi-plugin-design |
| [x] | Claude Code agent template | node_modules/claude-code-templates/.claude/agents/*.md | REFERENCE PATTERNS — Templates show <example> blocks, <commentary>, model selection, tools/skills declarations. Used to validate mise-specialist as pattern reference. | chezmoi-plugin-design |

---

## Audio/Video Processing Tools for YouTube Pipeline (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | yt-dlp GitHub | https://github.com/yt-dlp/yt-dlp | CORE TOOL — Feature-rich YouTube downloader; 200+ format support; audio extraction (MP3, M4A); subtitle fetching; quality control; mise installation status unclear | youtube-pipeline-tools |
| [x] | openai-whisper GitHub | https://github.com/openai/whisper | OFFICIAL TRANSCRIPTION — OpenAI's speech recognition; 99 languages; local inference (no API key required); model sizes: tiny to large; accuracy prioritized | youtube-pipeline-tools |
| [x] | faster-whisper GitHub | https://github.com/SYSTRAN/faster-whisper | OPTIMIZED TRANSCRIPTION — CTransformers-based Whisper; 10x faster than official; reduced memory; GPU support; best speed/accuracy balance | youtube-pipeline-tools |
| [x] | whisper.cpp GitHub | https://github.com/ggerganov/whisper.cpp | LIGHTWEIGHT TRANSCRIPTION — C++ implementation; no external dependencies; CPU-efficient; edge deployment capable; build complexity higher | youtube-pipeline-tools |
| [x] | claude-mem GitHub | https://github.com/thedotmack/claude-mem | SESSION MEMORY SYSTEM — Persistent memory for Claude Code (v10.6.2); automatic context capture; MCP-based search/retrieval; AGPL-3.0 | youtube-pipeline-tools |
| [x] | claude-mem installation | /plugin install command | PLUGIN MODE — `/plugin marketplace add thedotmack/claude-mem` + `/plugin install claude-mem` (NOT npm install); enables session-to-session context preservation | youtube-pipeline-tools |

---

## Multi-Model Orchestration Tools Survey (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | sub-agents-skills GitHub | https://github.com/shinpr/sub-agents-skills | Python skill (pyproject.toml); wraps CLI execution (Codex, Claude Code, Cursor, Gemini); zero dependencies; subprocess-based; SKILL format, NOT SDK; 14 stars, 4 forks, low activity | multi-model-orchestration |
| [x] | nyldn/claude-octopus GitHub | https://github.com/nyldn/claude-octopus | Shell-based plugin; 8 providers, 47 commands, 50 skills, 75% consensus gates; Claude Code plugin marketplace; 2044 stars, 168 forks, very active; NOT a Python SDK | multi-model-orchestration |
| [x] | dsifry/metaswarm GitHub | https://github.com/dsifry/metaswarm | Shell agent template; multi-agent orchestration via markdown + .claude config; TDD enforcement; 145 stars, 16 forks, moderate activity; NOT an SDK | multi-model-orchestration |
| [x] | catlog22/Claude-Code-Workflow GitHub | https://github.com/catlog22/Claude-Code-Workflow | TypeScript/JavaScript (Node ecosystem); JSON-driven workflow orchestration; 1575 stars, 130 forks, very active; NOT Python | multi-model-orchestration |
| [x] | BitDanceLabels/claude-octopus-skills GitHub | https://github.com/BitDanceLabels/claude-octopus-skills | Fork of nyldn/claude-octopus; 0 stars, abandoned; SEO farming pattern | multi-model-orchestration |
| [x] | multi-model-sdk-evaluation-2026-03-24 | docs/research/trail/findings/multi-model-sdk-evaluation-2026-03-24.yaml | CRITICAL FINDING — No Python SDK exists for multi-model CLI orchestration. All tools are skill/agent deployment frameworks (not code libraries). Consensus gates, Double Diamond workflows, and provider detection logic CAN be extracted as patterns, NOT as an importable SDK. | multi-model-orchestration |

---

## Adversarial Review & Multi-Model Evaluation Frameworks (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | DSPy GitHub | https://github.com/dspy-ai/dspy | **STRONGEST CANDIDATE** — 16K+ stars; Stanford NLP framework for composable LLM pipelines; features: MultiChainComparison (debate), BootstrapFewShot, Retrieve (RAG); extensible LM provider layer; MIT license; pip installable; recently updated 2026-03 | adversarial-review |
| [x] | DSPy Docs | https://dspy.ai | Declarative framework for building optimized AI systems; supports modular composition, RAG, agents, classifiers | adversarial-review |
| [x] | PydanticAI GitHub | https://github.com/pydantic/pydantic-ai | **SECOND CANDIDATE** — 1600+ stars; multi-model orchestration framework; pluggable ModelProvider; supports Anthropic, OpenAI, Groq, Gemini, Ollama, vLLM; MIT license; pip installable; can swap models per-call; tracks confidence; 2026-03 active | adversarial-review |
| [x] | PydanticAI Docs | https://docs.pydantic.dev/latest/concepts/agents/ | Agent class API, tool integration, structured outputs; multi-turn conversation support | adversarial-review |
| [x] | vLLM GitHub | https://github.com/vLLM-project/vllm | **INFRASTRUCTURE CANDIDATE** — 30K+ stars; fast LLM inference engine; OpenAI-compatible HTTP API; structured output support (Outlines); suitable for self-hosted inference; Apache 2.0; not CLI-native but provides HTTP endpoint | adversarial-review |
| [x] | alpaca_eval GitHub | https://github.com/tatsu-lab/alpaca_eval | **SPECIALIZED CANDIDATE** — 1100+ stars; LLM evaluation framework with judge models; pairwise comparison, head-to-head judgments; pip installable; Apache 2.0; but stale (last push 2025-10) and API-dependent (needs judge credentials) | adversarial-review |
| [x] | alpaca_eval Docs | https://github.com/tatsu-lab/alpaca_eval/blob/main/README.md | Judge patterns: ChatGPT, Claude; head-to-head comparison; batch processing; aggregation logic | adversarial-review |
| [x] | Outlines GitHub | https://github.com/dottxt-ai/outlines | **UTILITY FRAMEWORK** — 9000+ stars; token-constrained generation (force valid JSON/function responses); integrates with vLLM, HF; Apache 2.0; solves structured output parsing problem; orthogonal to orchestration | adversarial-review |
| [x] | Instructor GitHub | https://github.com/jxnl/instructor | **OUTPUT EXTRACTION** — 10K+ stars; structured output via Pydantic; not orchestration-focused; SDK-only (requires direct API access); MIT license | adversarial-review |
| [x] | Marvin GitHub | https://github.com/prefectio/marvin | **NOT RECOMMENDED** — 6400+ stars; decorator-based LLM interface; function calling, classification; single-model (hardcoded OpenAI); Apache 2.0; not suitable for multi-model adversarial review | adversarial-review |
| [x] | Guidance GitHub | https://github.com/guidance-ai/guidance | **PATTERN ONLY** — 18K+ stars; prompt programming DSL; control flow, structured generation; MIT license; not debate-specific; overcomplicated for this use case | adversarial-review |
| [x] | FastChat (LMSYS) GitHub | https://github.com/lmsys/FastChat | **BENCHMARK INFRASTRUCTURE** — 37K+ stars; LLM chat service + leaderboard infrastructure; includes pairwise judge implementation (used in LMSYS leaderboard); Apache 2.0; infrastructure-heavy; pip installable via `pip install fschat` | adversarial-review |
| [x] | ChatbotArena Judge Patterns | https://github.com/lmsys/FastChat/blob/main/fastchat/serve/gradio_web_server.py | LMSYS leaderboard judge logic; pairwise comparison; extensible to custom models; reference implementation for consensus gates | adversarial-review |
| [x] | Anthropic SDK (Python) GitHub | https://github.com/anthropics/anthropic-sdk-python | **BASELINE LLM** — Official Anthropic Python SDK; tool use, vision, batch API, extended thinking; 2026-03 active; use as baseline model provider, not orchestration | adversarial-review |
| [x] | adversarial-review-existing-tech-2026-03-24 | docs/research/trail/findings/adversarial-review-existing-tech-2026-03-24.yaml | **CRITICAL ANALYSIS** — Four candidates identified: DSPy (debate patterns), PydanticAI (orchestration), vLLM (infrastructure), alpaca_eval (judge patterns). None support CLI-backend mode natively; requires custom subprocess adapter (~150 lines). Recommendation: Use DSPy + custom SubprocessLMProvider (compose strategy, not build new SDK). | adversarial-review |
| [x] | sentinelone-adversarial-engine-search-2026-03-24 | docs/research/trail/findings/sentinelone-adversarial-engine-search-2026-03-24.yaml | **RESEARCH CORRECTION** — SentinelOne has NO public "adversarial consensus engine." SentinelOne is endpoint security (MDR/XDR), not LLM evaluation. GitHub search: 0 results for "adversarial," "consensus," "engine" in sentinelone org. Likely user misattribution; recommend checking LMSYS Arena, OpenAI Evals, Anthropic CAI instead. | sentinelone-search |
| [x] | skill-marketplace-adversarial-2026-03-24 | docs/research/trail/findings/skill-marketplace-adversarial-2026-03-24.yaml | **MARKETPLACE AUDIT** — No pre-built adversarial review skills exist (skills.sh, Awesome Claude Code, Factorial). Closest: claude-octopus (multi-agent orchestration with 75% consensus gates). Adversarial review skills must be created; recommend DSPy-based composition. Skills marketplace gap identified; custom skill structure documented. | skill-marketplace |
| [x] | adversarial-review-best-stack-synthesis-2026-03-24 | docs/research/trail/findings/adversarial-review-best-stack-synthesis-2026-03-24.yaml | **FINAL RECOMMENDATION** — Compose DSPy (debate patterns) + Outlines (structured output) + Custom SubprocessLMProvider (CLI adapter) + Consensus logic (~200-300 lines). 4-component stack, zero new libraries. 2-3 day implementation (600 lines total code). Detailed architecture, rationale, roadmap, and composition breakdown provided. Honors user mandate: assemble existing → build new (LAST RESORT). | adversarial-synthesis |

---

## Adversarial/Multi-LLM Skills & Consensus Engines (2026-03-24)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | SentinelOne Adversarial Consensus Engine | https://www.sentinelone.com/labs/building-an-adversarial-consensus-engine-multi-agent-llms-for-automated-malware-analysis/ | CONFIRMED — Serial consensus pipeline pattern for catching LLM hallucinations; malware analysis use case; multi-agent debate concept | PATTERN |
| [x] | skill.fish multi-LLM search | https://www.skill.fish/?q=multi+llm | BLOCKED — Vercel Security Checkpoint; geo/bot detection prevents automated fetch | GEO-RESTRICTED |
| [x] | skill.fish adversarial search | https://www.skill.fish/?q=adversarial | BLOCKED — Vercel Security Checkpoint | GEO-RESTRICTED |
| [x] | skill.fish red-team search | https://www.skill.fish/?q=red+team | BLOCKED — Vercel Security Checkpoint | GEO-RESTRICTED |
| [x] | skills.sh adversarial search | https://skills.sh/?q=adversarial | PARTIAL — Accessible but returns generic skills (UI/UX, React, Azure), no adversarial tools identified | SEARCH-INEFFECTIVE |
| [x] | skills.sh red-team search | https://skills.sh/?q=red+team | PARTIAL — Generic leaderboard, no red-team categorization | SEARCH-INEFFECTIVE |
| [x] | skills.sh multi-LLM search | https://skills.sh/?q=multi+llm | PARTIAL — No multi-LLM aggregation skills identified | SEARCH-INEFFECTIVE |
| [x] | mcpmarket.com adversarial skills | https://mcpmarket.com/search?q=adversarial&type=skills | BLOCKED — HTTP 403 Forbidden (geo-fenced or rate-limited) | GEO-RESTRICTED |
| [x] | mcpmarket.com multi-LLM skills | https://mcpmarket.com/search?q=multi+llm&type=skills | BLOCKED — HTTP 403 Forbidden | GEO-RESTRICTED |
| [x] | mcpmarket.com red-team skills | https://mcpmarket.com/search?q=red+team&type=skills | BLOCKED — HTTP 403 Forbidden | GEO-RESTRICTED |
| [x] | skillfish CLI tool | https://github.com/knoxgraeme/skillfish | PARTIAL — GitHub repo (Next.js SPA); purpose unclear, likely local skill discovery/management tool; requires browser/DOM rendering | LOCAL-TOOL |

---

## Chezmoi Plugin Hook Research (2026-03-25)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | chezmoi official command overview | https://www.chezmoi.io/user-guide/command-overview/ | REFERENCE — Daily commands (add, edit, apply, diff, status, cd), multi-machine workflows (init, update), template patterns (data, execute-template, chattr). Workflow entry points: chezmoi add (source capture), chezmoi edit --apply (edit+deploy), chezmoi update (pull+apply) | chezmoi-plugin |
| [x] | chezmoi hooks reference | https://www.chezmoi.io/reference/configuration-file/hooks/ | REFERENCE — Hook events: pre/post for any command (add, edit, apply, update, etc.) + special events (git-auto-commit, git-auto-push, read-source-state). Environment variables: CHEZMOI=1, CHEZMOI_COMMAND, CHEZMOI_COMMAND_DIR, CHEZMOI_ARGS. Hooks run even on --dry-run. Integration point: Claude Code hooks fire BEFORE chezmoi CLI; chezmoi hooks fire within CLI. | chezmoi-plugin |
| [x] | Claude Code hooks v2.1.81 reference | https://code.claude.com/docs/en/hooks | REFERENCE — 22 hook events: 5 lifecycle (SessionStart, InstructionsLoaded, SessionEnd, PreCompact, PostCompact), 5 interaction (UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, Stop), 4 agent (SubagentStart, SubagentStop, TeammateIdle, TaskCompleted), 2 security (PermissionRequest, ConfigChange), 2 filesystem (WorktreeCreate, WorktreeRemove), 2 notification (Notification, Elicitation), 1 special (StopFailure). Blocking behavior: PreToolUse, PostToolUseFailure, UserPromptSubmit, PermissionRequest, ConfigChange, Stop, TeammateIdle, TaskCompleted support exit code 1 blocking. | claude-code-hooks |
| [x] | mise-toolkit plugin hooks.json | rsm-subagents/plugins/mise-toolkit/hooks/hooks.json | PATTERN — Guard pattern: PreToolUse:Bash matcher intercepts direct install commands (brew install, npm -g, pipx install, etc.). Execution: bash script receives ${TOOL_INPUT}. Exit code 1 blocks tool execution. Can be reused for chezmoi dotfile protection (block vim ~/.bashrc, suggest chezmoi edit instead). | guard-pattern |
| [x] | mise-toolkit guard-install.sh | rsm-subagents/plugins/mise-toolkit/hooks/scripts/guard-install.sh | PATTERN — Implementation: BLOCKED_PATTERNS array with grep -qi matching. Exception handling (pip install -e allowed). Clear error message + suggestion to use mise. Exit code 1 blocks. Timeout 5000ms. Pattern directly applicable to prevent-direct-dotfile-edits hook for chezmoi plugin. | guard-pattern |
| [x] | awesome-claude-code (32.2K⭐) | https://github.com/hesreallyhim/awesome-claude-code | SURVEY — Curated list of 0 chezmoi-specific hooks; hooks section exists but no dotfiles/chezmoi integration documented. Community reference for hook patterns. | awesome-lists |
| [x] | awesome-claude-code-toolkit (899⭐) | https://github.com/rohitg00/awesome-claude-code-toolkit | SURVEY — 19 hooks documented; 0 chezmoi integration; hook categories: git-related, file-related, UI, validation, performance. No dotfiles or chezmoi-specific hooks found. | awesome-lists |
| [x] | awesome-claude-code-plugins (646⭐) | https://github.com/ccplugins/awesome-claude-code-plugins | SURVEY — Hooks and plugins curated; 0 chezmoi integration found. Confirms greenfield opportunity for chezmoi plugin hooks. | awesome-lists |
| [x] | buildwithclaude (2.6K⭐) | https://github.com/davepoon/buildwithclaude | SURVEY — Hub for Claude skills, agents, hooks, plugins; 0 chezmoi hooks documented. Validates that no existing community implementations exist. | awesome-lists |


---

## Chezmoi Plugin Skill Gap Analysis (2026-03-25)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | chezmoi setup documentation | https://www.chezmoi.io/user-guide/setup/ | REFERENCE — Init workflows, remote repo setup, one-shot mode for ephemeral environments. Multi-machine deployment patterns. Fresh install, clone existing, Docker/CI deployment. | chezmoi-plugin |
| [x] | chezmoi templating documentation | https://www.chezmoi.io/user-guide/templating/ | REFERENCE — Go template syntax, variables (.chezmoi.os, .chezmoi.arch, .chezmoi.hostname), conditionals, loops, template functions, password managers, external resources, .chezmoiexternal configuration | chezmoi-plugin |
| [x] | chezmoi reference/special-files | https://www.chezmoi.io/reference/special-files/ | REFERENCE — Processing order: .chezmoiroot (source path), .chezmoi.$FORMAT.tmpl (init), .chezmoidata/, .chezmoitemplates/, .chezmoiignore, .chezmoiremove, .chezmoiexternal, .chezmoiversion. All optional; evaluated in specific order. | chezmoi-plugin |
| [x] | chezmoi reference/special-directories | https://www.chezmoi.io/reference/special-directories/ | REFERENCE — .chezmoidata/ (config data), .chezmoitemplates/ (include templates), .chezmoiscripts/ (lifecycle scripts), .chezmoiexternals/ (external resources). All optional; read in lexical order. | chezmoi-plugin |
| [ ] | johnstegeman/dotfiles repository | https://github.com/johnstegeman/dotfiles | BLOCKED — Research queued to analyze chezmoi source structure, external resources, secrets/encryption, mise config, and script patterns for adoption. Tool access required (curl/agent-fetch/gh API). See finding-johnstegeman-dotfiles.yaml | dotfiles-patterns |
| [x] | chezmoi daily operations | https://www.chezmoi.io/user-guide/daily-operations/ | REFERENCE — Edit patterns (chezmoi edit, edit --apply, edit --watch), pull and diff, auto-commit/push, one-shot install, one-command deploy (sh -c "$(curl...)" -- init --apply) | chezmoi-plugin |
| [x] | chezmoi commands reference | https://www.chezmoi.io/reference/commands/ | INDEX — All commands documented separately; setup: add, edit, apply, diff, status, cd, source-path, managed, unmanaged, ignored, execute-template, state dump, verify, forget, doctor, init, merge | chezmoi-plugin |

---

## Mise Environment Variables & Settings (2026-03-25)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | mise-env-fnox integration | docs/mise-config.md (lines 44-47) | PATTERN — Use MISE_ENV_CACHE=1 to enable caching for fnox secret resolution; export before `mise activate zsh`. Secrets loaded from ~/.config/mise/secrets.sops.json; fnox is refresh/restore layer. | mise-environment |
| [x] | Official mise env variables | docs/plans/2026-02-28-research-r1-mise-core.md (lines 232-236) | DOCUMENTED — MISE_YES=1 (auto-answer yes), MISE_TRUSTED_CONFIG_PATHS (colon-sep paths), MISE_PIN=1 (exact versions not fuzzy). Equivalent config: yes=true, [settings] pin_versions=true | mise-environment |
| [x] | MISE_BACKENDS override | docs/mise-config.md (line 39) | PATTERN — MISE_BACKENDS_<TOOL> env var can override backend; example: MISE_BACKENDS_CLAUDE="npm:@anthropic-ai/claude-code" | mise-environment |
| [x] | status.missing_tools setting | rsm-subagents/plugins/mise-toolkit/skills/mise-config-settings/SKILL.md (line 41) | SETTING — Controls warning behavior for missing tools. Value "if_other_versions_installed" documented; other values not yet enumerated. Related to status warnings, not strict mode. | mise-settings |
| [x] | Project automation: MDE_AUTOFIX_STRICT | scripts/macos-dev-maintenance.sh (lines 8, 598-602) | PROJECT-SPECIFIC — Not official mise feature. Removes brew-managed runtimes (node, go, rust, python) when MDE_AUTOFIX=1 AND MDE_AUTOFIX_STRICT=1. Invokes remove_brew_runtimes() function. Destructive; for CI/CD or aggressive cleanup. | project-automation |
| [x] | GitHub jdx/mise (official) | https://github.com/jdx/mise | OFFICIAL — Version 2026.3.14+. No MISE_STRICT environment variable found in repository. No official "strict mode" concept documented. Potential future feature based on project patterns. | mise-core |
| [x] | Homebrew llvm formula | https://formulae.brew.sh/formula/llvm | TOOL — LLVM 22.1.1 (stable), keg-only. Includes clang, clang++, clang-format, clang-tidy, lldb, clang-tools-extra. LLD split to separate formula. 63K installs/month. | llvm-clang |
| [x] | Homebrew lld formula | https://formulae.brew.sh/formula/lld | TOOL — LLVM linker 22.1.1. Separate from llvm formula since Homebrew split. Requires llvm dep. | llvm-clang |
| [x] | LLVM official releases (GitHub) | https://github.com/llvm/llvm-project/releases | OFFICIAL — llvmorg-22.1.2 latest. macOS ARM64 prebuilt: 1.4GB. Full distribution. | llvm-clang |
| [x] | mise-plugins/mise-llvm (asdf backend) | https://github.com/mise-plugins/mise-llvm | PLUGIN — asdf-style LLVM plugin for mise. Alternative to conda backend. Untested. | llvm-clang |
| [x] | wshobson/agents marketplace | https://github.com/wshobson/agents | MARKETPLACE — 32K stars. 72 plugins, 112 agents, 146 skills. python-development plugin has 3 agents + 16 skills (all markdown). No hooks, no executable code. marketplace.json schema documented. | plugin-marketplace |
| [x] | anthropics/claude-plugins-official | https://github.com/anthropics/claude-plugins-official | MARKETPLACE — 14.6K stars. Official Anthropic-managed plugin directory. | plugin-marketplace |
| [x] | jeremylongshore/claude-code-plugins-plus-skills | https://github.com/jeremylongshore/claude-code-plugins-plus-skills | MARKETPLACE — 1.7K stars. 340 plugins, 1367 skills. CCPI package manager. | plugin-marketplace |
| [x] | obra/superpowers-marketplace | https://github.com/obra/superpowers-marketplace | MARKETPLACE — 731 stars. Curated Claude Code plugin marketplace. | plugin-marketplace |
| [x] | thedotmack/claude-mem | https://github.com/thedotmack/claude-mem | PLUGIN — 40.5K stars. Memory capture plugin (not a marketplace). | plugin-memory |
| [x] | jarrodwatts/claude-hud | https://github.com/jarrodwatts/claude-hud | PLUGIN — 13.2K stars. Context usage HUD plugin. | plugin-monitoring |
| [x] | Ruff configuration docs | https://docs.astral.sh/ruff/configuration/ | OFFICIAL — Ruff 0.15.7 config reference. pyproject.toml, select/ignore, per-file-ignores, preview mode. | python-quality |
| [x] | Ruff rules reference | https://docs.astral.sh/ruff/rules/ | OFFICIAL — 900+ lint rules. Preview rules marked. Fixable rules marked. | python-quality |
| [x] | Ruff preview mode docs | https://docs.astral.sh/ruff/preview/ | OFFICIAL — Preview expands defaults to B/UP/RUF. explicit-preview-rules for per-rule opt-in. | python-quality |
| [x] | Ruff integrations docs | https://docs.astral.sh/ruff/integrations/ | OFFICIAL — GitHub Actions, pre-commit, Docker, GitLab CI. ruff-action@v3. | python-quality |
| [x] | Ruff GitHub releases | https://github.com/astral-sh/ruff/releases | OFFICIAL — 0.15.7 latest (2026-03-19). Lazy import parsing, PEP 798 in preview. | python-quality |
| [x] | ty docs (Astral type checker) | https://docs.astral.sh/ty/ | OFFICIAL — Alpha 0.0.25. 10-100x faster than mypy/Pyright. LSP, intersection types. | python-quality |
| [x] | ty configuration reference | https://docs.astral.sh/ty/reference/configuration/ | OFFICIAL — rules, analysis, environment config. allowed-unresolved-imports, replace-imports-with-any. | python-quality |
| [x] | ty GitHub releases | https://github.com/astral-sh/ty/releases | OFFICIAL — 0.0.25 (2026-03-24). Weekly breaking changes. type:ignore[ty:code] suppression. | python-quality |
| [x] | uv docs (Astral package manager) | https://docs.astral.sh/uv/ | OFFICIAL — 0.11.1 stable. Replaces pip/poetry/pyenv/pipx. Universal lockfile, workspaces. | python-quality |
| [x] | uv workspaces docs | https://docs.astral.sh/uv/concepts/projects/workspaces/ | OFFICIAL — Monorepo support. Single lockfile, editable inter-deps. | python-quality |
| [x] | ty playground | https://play.ty.dev | OFFICIAL — Online playground for ty type checker. | python-quality |

---

## Multi-Model Orchestration & Consensus Systems (2026-03-25)

| Status | Source | URL | Finding | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | claude-octopus GitHub repo | https://github.com/nyldn/claude-octopus | PRODUCTION-READY — v9.13.0 MIT-licensed Claude Code plugin with 75% consensus gate, multi-model orchestration (8 providers), 32 personas, 47 commands. Zero external API key requirements (all auth via OAuth or subscription CLIs). Subprocess dispatch to Codex/Gemini CLIs. | multi-model-orchestration |
| [x] | claude-octopus README | https://raw.githubusercontent.com/nyldn/claude-octopus/main/README.md | CONFIRMED — Double Diamond workflow (Discover/Define/Develop/Deliver), 75% quality gate threshold, blinded/cross-critique debate modes, autonomy modes (supervised/semi-autonomous/autonomous) | consensus-gate |
| [x] | claude-octopus scripts/lib/debate.sh | https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/debate.sh | IMPLEMENTATION — grapple_debate() function with 3-7 round adversarial review, debate integrity rules (ANTI-CONTRARIAN, ANTI-RUBBER-STAMP, EVIDENCE-BASED), parallel proposal generation, sequential synthesis | debate-logic |
| [x] | claude-octopus scripts/lib/quality.sh | https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/quality.sh | IMPLEMENTATION — Quality gate branching (proceed/proceed_warn/retry/escalate/abort), threshold evaluation (>= 90% → proceed, >= 75% → proceed_warn), provider lockout mechanism, autonomy-aware retry logic | quality-scoring |
| [x] | claude-octopus preflight checks | https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/preflight.sh | CONFIRMED — Zero required external API keys. Codex/Gemini/Perplexity are optional. Claude is built-in. Detects auth via ~/.codex/auth.json OR OPENAI_API_KEY (same pattern for all providers). All features work on Claude alone. | provider-detection |
| [x] | claude-octopus package.json | https://raw.githubusercontent.com/nyldn/claude-octopus/main/package.json | METADATA — @anthropic-plugins/claude-octopus v9.13.0, MIT License, requires Bash 3.2+, zero npm dependencies (pure shell) | plugin-format |
| [x] | claude-octopus LICENSE | https://raw.githubusercontent.com/nyldn/claude-octopus/main/LICENSE | CONFIRMED — MIT License, permissive derivative/commercial use allowed | license-compat |


## Autonomous PR Review Tools — Multi-Model Consensus (2026-03-25)

| Status | Source | URL | Verdict | Classification |
|--------|--------|-----|---------|-----------------|
| [x] | reviewd GitHub | https://github.com/simion/reviewd | RECOMMENDED — Python package (MIT, v0.6.0) for local PR review via claude/gemini/codex CLIs. Subprocess invocation, no API keys. Structured JSON findings. See finding-reviewd-integration-eval.yaml for full eval. | TOOL — Production Ready |
| [x] | reviewd PyPI | https://pypi.org/project/reviewd/ | installable via `pip install reviewd` or `uv tool install reviewd`. Requires Python 3.12+. Dependencies: click, httpx, pyyaml, questionary. | TOOL — Packaging |
| [x] | reviewd Source (reviewer.py) | https://raw.githubusercontent.com/simion/reviewd/main/src/reviewd/reviewer.py | Core review orchestration: git worktree creation, test command execution, AI CLI invocation, JSON parsing. 600+ lines, importable modules. | TOOL — Architecture |
| [x] | reviewd Models | https://raw.githubusercontent.com/simion/reviewd/main/src/reviewd/models.py | Dataclasses: Finding (severity/category/title/file/line/issue/fix), ReviewResult, ProjectConfig. Matches mde findings format. | TOOL — Data Schema |
| [x] | reviewd Prompt | https://raw.githubusercontent.com/simion/reviewd/main/src/reviewd/prompt.py | Prompt generation with security scope, severity definitions, auto-approve rules. Produces JSON schema output. | TOOL — Prompt Engineering |
| [x] | public-apis GitHub (416k stars) | https://github.com/public-apis/public-apis | CATALOG EVALUATION — 1,436 free APIs indexed. Searched for code review, linting, static analysis, LLM orchestration APIs. VERDICT: SKIP — No relevant APIs for autonomous-fix-review skill. SonarQube (OAuth, paid), Deepcode (enterprise), GitHub (OAuth required). All violate zero-key constraint. See finding-public-apis-review-relevance.yaml for detailed evaluation. | free-api-catalog |
| [x] | claude-octopus scripts/lib/quality.sh (complete) | https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/quality.sh | FULL CONTENT EXTRACTED — Complete quality gate implementation (1,012 lines): evaluate_branch_condition(), get_branch_display(), evaluate_quality_branch(), execute_quality_branch(), lock_provider(), is_provider_locked(), get_alternate_provider(), reset_provider_lockouts(), append_provider_history(), read_provider_history(), build_provider_context(), write_structured_decision(), design_review_ceremony(), retrospective_ceremony(), detect_response_mode(), get_gate_threshold(), score_importance(), search_observations(), search_similar_errors(), flag_repeat_error(), score_cross_model_review(), format_review_scorecard(), get_cross_model_reviewer(), run_project_quality_checks(), detect_project_quality_commands(). Saved to docs/research/trail/deep-reviews/claude-octopus-quality.sh.md | quality-gate-complete |
| [x] | claude-octopus scripts/lib/debate.sh (complete) | https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/debate.sh | FULL CONTENT EXTRACTED — Complete debate orchestration (717 lines): grapple_debate() function with round 1 (parallel proposals from 3 providers), round 2 (mode-aware: blinded independent evals vs cross-critique ACH falsification), rounds 3-N (rebuttals with integrity rules), quorum consensus mode (v8.20.0), final synthesis. Debate integrity constraints (ANTI-CONTRARIAN, ANTI-RUBBER-STAMP, EVIDENCE-BASED, PROPORTIONAL). Saved to docs/research/trail/deep-reviews/claude-octopus-debate.sh.md | debate-implementation |

## Devcontainer Spec Deep Dive (2026-03-25)

### Official Specification
- https://github.com/devcontainers/spec/blob/main/docs/specs/devcontainerjson-reference.md - Complete devcontainer.json reference
- https://github.com/devcontainers/spec/blob/main/docs/specs/features-contribute-lifecycle-scripts.md - Feature lifecycle integration
- https://github.com/devcontainers/spec/blob/main/docs/specs/image-metadata.md - Image metadata structure
- https://context7.com/devcontainers/spec/llms.txt - Context7 aggregated spec documentation

### CLI Reference
- https://context7.com/devcontainers/cli/llms.txt - Complete CLI command reference
- https://github.com/devcontainers/cli/blob/main/README.md - CLI overview
- https://github.com/devcontainers/cli/blob/main/docs/features/test.md - CLI testing patterns
- devcontainer 0.84.1 local --help output (2026-03-26) - All 11 subcommands with complete flag reference. See docs/research/trail/findings/devcontainer-cli-capabilities.yaml

### Skill Marketplace Discovery (2026-03-26)
- https://skills.sh - Skills CLI and marketplace search
- https://skillsmp.com - Skillsmp marketplace
- sickn33/antigravity-awesome-skills@devcontainer-setup (1306 skills library) - Safe risk assessment, comprehensive devcontainer template system
- trailofbits/skills@devcontainer-setup (775 installs) - High risk assessment, production-grade devcontainer generator
- manutej/luxor-claude-marketplace@docker-compose-orchestration (641 installs) - Comprehensive compose patterns, health checks, networking
- microsoft/vscode-remote-try-node - Official VS Code Node.js sample devcontainer
- verlab/ros1_devcontainer_docker_compose - ROS1 Noetic real-world pattern: privileged mode, initializeCommand, sidecar services
- reinoxl/unique-devcontainer-name-with-docker-compose - Path-specific naming pattern for multi-workspace isolation
- containers.dev/implementors/json_reference/ - Lifecycle command properties (postCreateCommand, postStartCommand, postAttachCommand, waitFor)
- containers.dev/implementors/features/ - Feature dependencies, installation order, lifecycle hooks


## 2026-03-26: Community Plugins Research Round

- https://github.com/anthropics/claude-plugins-community | CONFIRMED | 500 community plugins, marketplace sync
- https://raw.githubusercontent.com/anthropics/claude-plugins-community/main/README.md | CONFIRMED | Integration guide
- https://raw.githubusercontent.com/anthropics/claude-plugins-community/main/.claude-plugin/marketplace.json | CONFIRMED | Community plugins registry

### High-relevance community plugins evaluated (2026-03-26):
| Status | Plugin | URL | Verdict |
|--------|--------|-----|---------|
| [x] | test-generator | https://github.com/a-abdellatif98/test-generator | INSTALL — Python PostToolUse hook, pytest scaffolding, test-writer agent |
| [x] | srclight | https://github.com/srclight/claude-code-plugin | REJECT — bash hooks, MCP server, conflicts with no-shell-scripts + MCP access policies |
| [x] | scenario-testing | https://github.com/2389-research/claude-plugins | REJECT — anti-mock philosophy conflicts with mde test patterns, thin value |
| [x] | mcp2cli | https://github.com/myeolinmalchi/mcp2cli | EXTRACT — overlaps existing mcp2cli CLI; reference docs useful for plugin dev |
| [x] | workflow-toolkit | https://github.com/dougwithseismic/workflow-toolkit | REJECT — all bash hooks, SQLite vs YAML, 21 skills context cost, massive overlap |
| [x] | superdevflow | https://github.com/ykdojo/superdevflow | EXTRACT — GHA debug skill valuable; "All Rights Reserved" license blocks extraction |


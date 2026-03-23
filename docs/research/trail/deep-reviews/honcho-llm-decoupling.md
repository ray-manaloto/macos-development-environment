# Honcho LLM Requirements & Architecture Review

**Date:** 2026-03-23
**Subject:** Investigating Honcho v3.0.3 self-hosting viability without paid LLM API keys
**Status:** Research Complete - Recommendation Below

## Executive Summary

Honcho v3.0.3 **requires paid LLM API keys** from Anthropic, OpenAI, Google, and Groq to operate in self-hosted mode. The reasoning backend (deriver) cannot function without these credentials. However, the API server can run in **degraded storage-only mode** without reasoning capabilities.

**Bottom line:** You cannot self-host Honcho with the reasoning capabilities you want without paying for API keys across multiple providers.

## Findings

### 1. LLM Provider Requirements (CONFIRMED)

Honcho v3.0.3 requires the following paid LLM API keys:

| Provider | Key | Purpose | Required? | Default Model |
|----------|-----|---------|-----------|---|
| Anthropic | `LLM_ANTHROPIC_API_KEY` | Dialectic reasoning | Yes | claude-haiku-4-5 |
| OpenAI | `LLM_OPENAI_API_KEY` | Embeddings | Yes | text-embedding-3-small |
| Google Gemini | `LLM_GEMINI_API_KEY` | Summarization | No (default disabled) | gemini-2.5-flash |
| Groq | `LLM_GROQ_API_KEY` | Query generation | No (default disabled) | Not specified |

**Critical:** The API server cannot start without at least the embedding provider (OpenAI) configured. The deriver (reasoning worker) requires Anthropic keys.

### 2. Local LLM Support (NOT IMPLEMENTED)

- **Ollama support:** Does not exist in v3.0.3
- **SQLite support:** Requested in GitHub Issue #405, not implemented (requires PostgreSQL + pgvector)
- **vLLM endpoints:** Configuration variables exist (`LLM_VLLM_BASE_URL`, `LLM_VLLM_API_KEY`) but integration status unclear
- **OpenAI-compatible endpoints:** Supported via `LLM_OPENAI_COMPATIBLE_BASE_URL` config

**Implication:** You cannot run Honcho with local models like Ollama without significant code changes.

### 3. Architectural Decoupling (IMPORTANT FINDING)

Honcho has **two decoupled processes:**

```
API Server (src/main.py)
├─ Handles HTTP requests
├─ Stores messages immediately
├─ Does NOT require reasoning
└─ Dependencies: PostgreSQL only

Deriver Worker (src.deriver module)
├─ Processes queued messages asynchronously
├─ Generates peer representations
├─ Requires all LLM API keys
└─ Completely optional (DERIVER_ENABLED=false)
```

**Key capability:** The API server can run without the deriver.

### 4. Deriver Functionality (OPTIONAL BUT CORE)

Without the deriver running, Honcho provides:

**What still works:**
- Message ingestion (immediate storage)
- Basic retrieval (raw message history)
- Database CRUD operations
- Session/peer/workspace management

**What is lost:**
- Peer representations (learned profiles about users)
- Summaries of conversations
- Peer cards (biographical data)
- Dreaming (background synthesis and pattern learning)
- Formal logical reasoning over stored data

This is the **death of core functionality.** Honcho's value proposition is "memory that reasons." Without reasoning, it's just a message store.

### 5. Honcho SaaS Offering (ALTERNATIVE)

Honcho offers a managed service at **app.honcho.dev** with:

**Pricing:**
- **Storage:** $2.00/million messages (includes reasoning)
- **Queries:** Unlimited at ~200ms latency
- **Reasoning levels:** $0.001-$0.50 per query (depending on depth)
- **Free tier:** $100 credits for new users
- **Startups:** $1,000 credits + 12 months subsidized pricing
- **Enterprise:** Custom pricing with dedicated support

**Why this matters:** The open-source project is open-core. The real product is the managed service.

## Analysis

### The Core Problem

Honcho's reasoning models (Neuromancer XR) are proprietary and optimized for formal logical reasoning. The architecture assumes you'll either:

1. **Option A:** Use the managed service (pay per message + queries)
2. **Option B:** Self-host with your own LLM API keys (pay OpenAI, Anthropic, Google, Groq)
3. **Option C:** Run API-only (lose all reasoning/memory benefits)

There is no Option D ("use free local models like Ollama").

### Why Not Local LLMs?

Honcho's design depends on:
- **Multiple specialized models** for different reasoning tasks (extraction, deduction, induction, abduction, summarization, dreaming)
- **Formal logical reasoning** which requires models trained specifically for consistency and logical rules
- **Cost optimization** through batching and specialized smaller models
- **Proven performance** on their evals benchmark

Off-the-shelf local models (Ollama, Llama 2, Mistral) are not trained for formal reasoning. Using them would:
- Destroy the reasoning quality Honcho is built on
- Increase token usage (broader context needed to get same quality)
- Require weeks of fine-tuning per model
- Defeat the "memory that reasons" value proposition

### Architectural Silver Lining

The deriver is decoupled, so you **could theoretically:**

1. Run API server locally (messages stored immediately)
2. Send deriver jobs to Honcho's managed service via API calls
3. Hybrid deployment where storage is local but reasoning is cloud

But Honcho doesn't expose this architecture. It's a design possibility, not a supported feature.

## Recommendation

Based on your stated constraints (avoiding paid API keys), Honcho is **not viable for your use case.**

### Viable Alternatives

1. **Use Honcho managed service ($100 free credits)**
   - No infrastructure cost
   - Let Plastic Labs handle scaling
   - Pay per-message for reasoning you use
   - **Pro:** Instant, proven, benchmarked
   - **Con:** Vendor lock-in, ongoing costs

2. **Use cheaper memory alternatives**
   - **LangChain + Chroma:** Local embeddings, semantic search (no reasoning)
   - **LangGraph:** Agent state management without learned memory
   - **RAG frameworks:** Basic retrieval-augmented generation
   - **Con:** Not "memory that reasons" — it's retrieval-based context

3. **Build custom solution**
   - Implement message storage (SQLite + embeddings)
   - Integrate local LLM for simple summarization
   - Skip formal reasoning layer
   - **Pro:** Full control, no vendor lock-in
   - **Con:** Years of work to approach Honcho quality

4. **Fork Honcho + patch**
   - Replace Neuromancer with Ollama
   - Replace PostgreSQL with SQLite
   - Rewrite reasoning to use local models
   - **Con:** 1000+ hours of engineering, maintenance burden

## Decision Matrix

| Approach | Cost | Setup Time | Reasoning Quality | Lock-In |
|----------|------|-----------|-------------------|---------|
| Honcho SaaS | $$ (pay-as-you-go) | 5 min | Excellent | High |
| Honcho Self-Hosted (API-only) | Free | 2 hours | None | Low |
| Custom RAG | Free | 40+ hours | Basic | Low |
| Build Memory System | Free | 500+ hours | Custom | Low |

## Conclusion

Honcho v3.0.3 **requires paid LLM APIs** to deliver its core value. The architecture supports self-hosting, but only with your own API credentials or as a degraded storage-only system.

**Your options:**
1. Accept the costs of multiple LLM APIs and self-host
2. Use Honcho's managed service (simplest path)
3. Choose a different memory architecture
4. Invest in building your own system

The research did uncover that the API and deriver are cleanly decoupled, which provides some architectural flexibility for future integration patterns. But as-is, self-hosting requires multi-provider LLM access.

---

## Sources Consulted

- GitHub: https://github.com/plastic-labs/honcho (v3.0.3 tag)
- Documentation: https://docs.honcho.dev/v3
- Pricing: https://honcho.dev
- Blog: https://blog.plasticlabs.ai
- Issues: #405 (SQLite), #407 (Local development), #420 (Custom endpoints)

## Confidence Assessment

- **LLM Requirements:** Confirmed (HIGH)
- **Local LLM Support:** Not implemented (HIGH)
- **API/Deriver Decoupling:** Confirmed (HIGH)
- **SaaS Pricing:** Current as of website (MEDIUM - may change)
- **API-only viability:** Probable (MEDIUM - untested in practice)

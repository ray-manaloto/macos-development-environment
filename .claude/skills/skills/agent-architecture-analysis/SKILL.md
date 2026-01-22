---
name: agent-architecture-analysis
description: Perform 12-Factor Agents compliance analysis on LLM/agent systems. Use when reviewing agent architectures, LangGraph/DeepAgents designs, or multi-agent deployments for reliability and scale.
---

# 12-Factor Agents (Concise Checklist)
Inspired by https://12factor.net, adapted for agentic systems.

## How to Use
1) Identify the agent system (graph/workflows, tools, memory, runtime). 2) For each factor, collect quick evidence. 3) Mark Strong/Partial/Weak and list remediations.

## Factors & Fast Checks

**I. Single Source of Truth (Graphs/Flows)**
- Check: graph/workflow defined as code; versioned; env parity maintained.
- Anti: ad-hoc prompts/flows per env, manual edits in prod.

**II. Dependencies & Models**
- Check: model/tool deps declared (lockfiles, manifest); model versions/policies explicit.
- Anti: implicit model selection, undeclared tool deps, drift between envs.

**III. Config (Prompts/Keys/Endpoints)**
- Check: prompts/templates versioned; keys/URIs in env/secret mgr; per-env overrides minimal.
- Anti: prompts hardcoded in prod, secrets in code, branching on env for prompts.

**IV. Backing Services (Vector DB, Cache, Observability)**
- Check: OTLP/logging configured; vector stores/DBs swappable via config; feature flags for new tools.
- Anti: hardcoded stores, no telemetry, tightly coupled to one vendor.

**V. Build/Release/Run (Artifacts)**
- Check: prompts/graphs packaged immutably; release metadata captured (model/tool versions, prompt hash).
- Anti: editing prompts in prod, mutable artifacts.

**VI. Stateless Execution / Checkpointing**
- Check: runs are idempotent or checkpointed; state externalized (DB/cache/object store).
- Anti: stateful in-memory chains, retries redo side effects, no idempotency keys.

**VII. Interfaces / Port Binding**
- Check: clear API/CLI/queue entrypoints; contracts documented.
- Anti: hidden entrypoints, tight coupling to orchestrator internals.

**VIII. Concurrency & Resource Control**
- Check: concurrency limits, rate limits per model/tool, queueing/backpressure.
- Anti: unbounded parallelism, model/tool rate-limit errors without handling.

**IX. Disposability & Timeouts**
- Check: timeouts per tool/model call; cancellation support; graceful shutdown of workers.
- Anti: no timeouts, orphaned subagents on cancel, long-lived processes without health checks.

**X. Env Parity (Eval/Prod)**
- Check: synthetic evals mirror prod traffic; can replay traces; fixtures for tools.
- Anti: manual prod-only tools, no replay/eval, divergent data sources.

**XI. Observability & Traces**
- Check: structured logging, OTLP traces, token/latency metrics, redaction in place.
- Anti: no traces, PII leakage in logs, missing cost accounting.

**XII. Admin / One-Offs**
- Check: migrations for prompt stores/vector schemas; one-off scripts use same runtime/creds.
- Anti: manual DB edits, different creds for ops scripts.

## Scoring Template
- Strong/Partial/Weak with evidence + 2–3 remediations; owners/dates.

## Report Skeleton
- Summary: top 3 risks, model/tool drift, observability posture, safety posture.
- Per factor: status, evidence (trace/log links), specific fixes.

## Quick Commands / Checks
- Find prompt files: `find . -name "*prompt*" -o -name "*.yaml" -o -name "*.json" | head`
- Check timeouts: search for `timeout`, `AbortController`, `context.with_timeout`, `httpx.Timeout`.
- Check telemetry: look for OTLP exporters, trace middleware, cost metrics.
- Check rate limits: search for `rate`, `limiter`, `backoff`, `retry` in tool/model wrappers.

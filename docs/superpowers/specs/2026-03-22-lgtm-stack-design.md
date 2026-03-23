# LGTM Docker Stack — Observability Storage & Visualization

**Date:** 2026-03-22
**PR:** A2 (follows PR A1 — loguru migration, merged as PR #38)
**Branch:** `feat/lgtm-stack`
**Status:** Design

## Problem

PR A1 set up the Python logging pipeline (loguru with OTEL sink), but the OTEL
Collector currently exports to `debug` (console only). Telemetry data is
collected but never stored or visualized. The standalone `codex-otel-collector`
container has no storage backends.

## Goal

Add a Docker Compose LGTM stack that receives OTEL data from Claude Code and
the mde Python library, stores traces in Tempo, stores logs in Loki, and
visualizes both in Grafana. Replace the standalone `codex-otel-collector` with a
managed compose stack.

## Success Criteria

1. `mise run mde:observability:up` starts the full stack (Collector, Tempo, Loki, Grafana)
2. Claude Code OTEL traces appear in Grafana via Tempo datasource
3. mde loguru logs (forwarded via OTEL sink) appear in Grafana via Loki datasource
4. `uv run mde-py telemetry verify` validates the stack is running and correctly configured
5. All images pinned by digest, no `:latest` tags
6. Quality gate passes 6/6

## Architecture

```
Claude Code (OTEL SDK)     mde Python (loguru → OTEL sink)
         │                              │
         └──────── OTLP/HTTP ───────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  OTEL Collector  │  :4317 (gRPC) / :4318 (HTTP) / :13133 (health)
            │  (transform +    │
            │   fan-out)       │
            └────┬────────┬───┘
                 │        │
          otlphttp     loki exporter
                 │        │
                 ▼        ▼
            ┌────────┐ ┌──────┐
            │ Tempo  │ │ Loki │
            │ :3200  │ │:3100 │
            └────┬───┘ └──┬───┘
                 │        │
                 ▼        ▼
            ┌─────────────────┐
            │    Grafana       │  :3000
            │  (datasources    │
            │   auto-provisioned)
            └─────────────────┘
```

## Design Decisions

### Why LGTM (not Jaeger, not SigNoz, not Aspire)

- **Grafana stack is the de-facto OSS observability standard** — widest community, most plugins
- **Tempo is trace-native** — no indexing overhead, object-storage compatible, TraceQL
- **Loki is log-native** — label-based indexing like Prometheus, efficient for structured JSON logs
- **Single-vendor stack** simplifies compose networking and datasource provisioning
- **All components are free/OSS** with no license restrictions

### Why Docker Compose (not Kubernetes, not Tilt)

- This is a local dev environment — single-machine, not production
- Compose profiles allow selective startup (observability vs. future memory stack)
- docker-bake.hcl as single build source of truth for reproducibility

### Why transform processor for secrets redaction

- OTEL spans may contain tool inputs, file paths, or environment variables
- Redacting at the Collector layer (before storage) is defense-in-depth
- Simpler than instrumenting every SDK call site

### Why no Prometheus/Mimir in default profile

- No metrics source exists yet — Claude Code exports traces and logs, not metrics
- Adding Prometheus without a scrape target wastes resources
- Can be added later via a `metrics` compose profile

## Components

### 1. Docker Infrastructure (`docker/observability/`)

| File | Purpose |
|------|---------|
| `docker-compose.yml` | LGTM stack with profiles |
| `docker-bake.hcl` | Single build/pull source of truth |
| `collector-config.yaml` | OTEL Collector: receive → transform → fan-out |
| `grafana/provisioning/datasources/datasources.yaml` | Auto-provision Tempo + Loki datasources |

**Collector pipeline:**
- Receivers: `otlp` (gRPC :4317, HTTP :4318)
- Processors: `transform` (redact sensitive attributes), `batch`
- Exporters: `otlphttp` → Tempo, `loki` → Loki, `debug` (for local troubleshooting)

**Image pinning:** All images use `@sha256:...` digests. No `:latest` tags.

**Secrets:** `GRAFANA_PASSWORD` sourced from fnox via environment variable, never hardcoded.

### 2. Mise Tasks + Stack Management (`src/mde/domain/observability_stack.py`)

| Task | Action |
|------|--------|
| `mde:observability:up` | Stop orphan collectors → `docker compose up -d` |
| `mde:observability:down` | `docker compose down` |
| `mde:observability:status` | Show container names, health, ports |

**Pre-start check:** Detect and stop the legacy `codex-otel-collector` container
before starting the compose stack to avoid port conflicts on 4317/4318/13133.

### 3. Telemetry Verify Updates (`src/mde/telemetry_verify.py`)

New pure-function checks added to the existing verify command:

| Check | What it validates |
|-------|-------------------|
| `_check_collector_pipelines(config_path)` | Collector config has non-debug exporters |
| Duplicate collector check | No duplicate OTEL collectors on ports 4317/4318 |
| Compose stack identity | Our compose stack is the running instance (container name/image match) |

### 4. orjson Serialization (`src/mde/observability.py`)

Wire `orjson.dumps()` into the loguru file sink as a custom format function.
orjson is already declared as a dependency but not yet used.

- Custom format function: `orjson.dumps(record)` for the JSON file sink
- Fallback: `serialize=True` (stdlib json) if orjson import fails
- Benchmark: verify orjson is faster than json.dumps for log records

### 5. Integration Tests (`tests/mde/test_lgtm_integration.py`)

```python
@pytest.mark.integration
class TestLGTMIntegration:
    """Integration tests — only run when Docker stack is up."""

    def test_trace_appears_in_tempo(self): ...
    def test_log_appears_in_loki(self): ...
```

- Send test span via OTEL SDK → query Tempo HTTP API → verify span appears
- Send test log via loguru → query Loki HTTP API → verify log appears
- Skip with `pytest.mark.skipif` when Docker stack is not running

### 6. Documentation

- Update CLAUDE.md if workflow changes discovered
- Write findings to `docs/research/trail/findings/` (YAML provenance)
- Update memory files with learnings
- Update next-PR prompt for PR B (Honcho)

## Security Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| CRIT-S1 | Redact secrets before storage | OTEL Collector transform processor strips sensitive attributes |
| CRIT-S2 | Image pinning + credential management | All images pinned by digest; GRAFANA_PASSWORD from fnox |
| HIGH-S2 | No `:latest` tags | Enforced in docker-bake.hcl |

## File Ownership (for parallel subagent execution)

| Agent | Files Owned |
|-------|-------------|
| infra-agent | `docker/observability/**` |
| mise-agent | `.mise.toml` (new tasks only), `src/mde/domain/observability_stack.py` |
| python-agent | `src/mde/telemetry_verify.py`, `src/mde/observability.py` (serialization) |
| test-agent | `tests/mde/test_lgtm_integration.py` |
| docs-agent | CLAUDE.md, `docs/research/trail/`, memory files |

## Verification Gates

```bash
uv run mde-py quality                    # 6/6
uv run mde-py telemetry verify           # all green
docker compose -f docker/observability/docker-compose.yml ps  # all healthy
uv run pytest tests/mde/ -v              # all pass including new tests
```

## Out of Scope

- Prometheus/Mimir (no metrics source yet)
- Grafana dashboards beyond datasource provisioning (follow-up PR)
- Production deployment or remote access
- Alerting rules

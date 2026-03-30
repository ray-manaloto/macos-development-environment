# Observability Stack Policy

## Architecture

The `mde-observability` Docker Compose stack provides telemetry collection for all AI CLI tools:

```
Codex CLI  ─→ HTTP :4318 ─→ OTEL Collector ─→ Tempo (traces) + Loki (logs)
Gemini CLI ─→ HTTP :4318 ─→ OTEL Collector ─→ Tempo (traces) + Loki (logs)
Claude Code ─→ gRPC :4317 ─→ OTEL Collector ─→ Tempo (traces) + Loki (logs)
                                                 └→ Grafana :3000 (visualization)
```

Compose file: `docker/observability/compose.yaml`

## Starting the stack

```bash
GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) docker compose -f docker/observability/compose.yaml up -d
```

`GRAFANA_PASSWORD` is sourced from fnox/Keychain — never hardcoded.

## Verifying health

```bash
curl -sf http://localhost:4318/v1/traces -X POST -d '{}' -H "Content-Type: application/json"  # OTLP HTTP endpoint
curl -sf http://localhost:3100/ready  # Loki
curl -sf http://localhost:3200/ready  # Tempo
curl -sf http://localhost:3000/api/health  # Grafana
```

Note: Port 13133 (OTEL Collector health check) is NOT exposed by the grafana/otel-lgtm
all-in-one image. Use the OTLP HTTP endpoint (4318) with an empty POST to verify the
collector is running.

## CLI telemetry configuration

All three CLIs are configured to send OTEL data to the collector:

- **Codex** (`.codex/config.toml`): `otlp-http` exporter → `http://127.0.0.1:4318`
- **Gemini** (`.gemini/settings.json`): No user-configurable OTLP setting; telemetry arrives via internal CLI mechanisms
- **Claude Code** (`.claude/settings.json`): `OTEL_EXPORTER_OTLP_ENDPOINT` → `http://localhost:4317`

## Enforcement

- The `check-observability` SessionStart hook verifies the OTEL collector is reachable
- If the collector is down, the hook emits a warning with startup instructions
- The `guard-debate` PreToolUse hook should also verify before debate invocations
- When debugging CLI failures, ALWAYS check telemetry first: `docker compose -f docker/observability/compose.yaml ps`

## What went wrong (2026-03-30)

The stack was never started after Docker/machine restart. No autostart mechanism existed.
All three CLIs silently dropped telemetry with no user-visible error. The Codex timeout
during adversarial review (300s) could not be diagnosed because traces were lost.
Fix: added SessionStart hook to detect and warn.

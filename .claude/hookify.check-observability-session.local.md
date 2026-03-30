---
name: check-observability-session
enabled: true
event: bash
pattern: uv\s+run\s+mde-py\s+hooks\s+session-start
action: warn
---

Before this session continues, verify the mde-observability stack is running.
Telemetry from Claude Code, Codex, and Gemini is silently lost when the OTEL collector is down.

**Quick check:**
```bash
curl -sf http://localhost:13133 || echo "OTEL collector is DOWN"
```

**If down, start it:**
```bash
GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) docker compose -f docker/observability/compose.yaml up -d
```

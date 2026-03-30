---
name: check-observability-debate
enabled: true
event: bash
pattern: uv\s+run\s+mde-py\s+debate
action: warn
---

**Debate telemetry check:** The mde debate system sends traces to the OTEL collector.
Without the collector running, you cannot debug Codex/Gemini CLI failures after the fact.

**Verify before proceeding:**
```bash
curl -sf http://localhost:13133 && echo "Collector UP" || echo "Collector DOWN — start with: GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) docker compose -f docker/observability/compose.yaml up -d"
```

If the collector is down, start the stack before running the debate.

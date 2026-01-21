# OpenLIT Telemetry (SkyPilot + AWS + Kubernetes)

This setup deploys OpenLIT on AWS via SkyPilot and configures macOS tools to
send OpenTelemetry (OTLP) telemetry to it. Kubernetes deployment is supported
via a user-supplied manifest.

## Summary (from SkyPilot AWS OpenLIT Deployment Guide.docx)
- Architecture: SkyPilot provisions an EC2 instance, OpenLIT runs via Docker
  Compose, and MacBook tools send OTLP telemetry to the public endpoint.
- Required ports: UI (3000), OTLP gRPC (4317), OTLP HTTP (4318).
- Typical flow: `sky launch` -> `sky status --ip` -> set `OPENLIT_ENDPOINT` and
  `OTEL_EXPORTER_OTLP_ENDPOINT` to `http://<IP>:4318`.

## Quickstart (SkyPilot on AWS)
1) Deploy OpenLIT:

```bash
scripts/openlit-control.sh deploy
```

2) Check status/endpoints:

```bash
scripts/openlit-control.sh status
scripts/openlit-control.sh endpoints
```

3) Write telemetry env to your secrets file (sets OTEL_* and Gemini CLI GEMINI_TELEMETRY_* for OpenLIT):

```bash
scripts/openlit-control.sh env --write-env
```

4) Reload your shell:

```bash
source ~/.zshrc
```

## Integrated Tooling
- macOS global OTLP env: `OPENLIT_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`.
- Gemini CLI: `GEMINI_TELEMETRY_ENABLED=1`, `GEMINI_TELEMETRY_TARGET=local`, `GEMINI_TELEMETRY_OTLP_ENDPOINT`/`_PROTOCOL`, `GEMINI_TELEMETRY_LOG_PROMPTS=1`.
- LangChain/LangSmith + other OTEL-aware CLIs/SDKs: inherit OTEL_* env for traces/metrics to OpenLIT.
- Status dashboard: `scripts/status-dashboard.sh --json` includes `openlit` and `gemini_telemetry` entries.

## UI Access
- URL: http://<OPENLIT_IP>:3000 (OpenLIT UI served directly; no Caddy layer).
- Preseeded user: `admin@example.com`
- Preseeded password: `OpenlitTemp!123`
- You can change the password after login from the OpenLIT UI. Keep the value in `~/.config/macos-development-environment/secrets.env` if you want it documented locally (not required for runtime).


## Local Telemetry Environment
Use OTLP HTTP for widest compatibility:

```
OPENLIT_ENDPOINT=http://<OPENLIT_IP>:4318
OTEL_EXPORTER_OTLP_ENDPOINT=http://<OPENLIT_IP>:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

Optional best-practice defaults:

```
OTEL_SERVICE_NAME=macbook-dev
OTEL_RESOURCE_ATTRIBUTES=env=local
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.2
```

## Update / Maintenance
- Update OpenLIT server (pull + restart):

```bash
scripts/openlit-control.sh update
```

- Stop/start/down:

```bash
scripts/openlit-control.sh stop
scripts/openlit-control.sh start
scripts/openlit-control.sh down
```

## Kubernetes Deployment (optional)
This repo does not ship a Kubernetes manifest for OpenLIT. Provide your own
manifest or Helm output and pass it to the control script.

```bash
scripts/openlit-control.sh k8s-deploy --k8s-manifest /path/to/openlit.yaml --namespace openlit
scripts/openlit-control.sh k8s-status --k8s-manifest /path/to/openlit.yaml --namespace openlit
```

If you want to write env vars for a Kubernetes endpoint, supply it explicitly:

```bash
scripts/openlit-control.sh k8s-env --endpoint http://<LOAD_BALANCER_IP>:4318 --write-env
```

## Status / Verification
- Full status + AWS details:

```bash
scripts/sky-status.sh
```

- OpenLIT env validation:

```bash
scripts/verify-openlit.sh
```

Set `MDE_OPENLIT_REQUIRED=1` to fail when the endpoint is missing, and
`MDE_OPENLIT_CHECK=1` to attempt a network check.

## Notes / Best Practices
- OTLP HTTP (4318) is easiest to use from CLIs and SDKs.
- Keep the endpoint in `secrets.env` so shells + launchd jobs share it.
- Use stable `OTEL_SERVICE_NAME` values so telemetry groups consistently.
- Avoid exporting secrets in shell files; keep them in `secrets.env` or
  1Password when service accounts are available.


## Security Considerations
- Restrict inbound ports (3000/4317/4318) to trusted IPs via AWS security groups.
- Prefer HTTPS/TLS for OTLP and UI endpoints when exposing them publicly.
- Avoid exporting API keys or secrets via shell files; keep them in `secrets.env`.
- Be mindful of PII in telemetry (filter or scrub before export).

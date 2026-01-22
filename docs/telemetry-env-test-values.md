# Telemetry Test Values (placeholder)

Use these temporary values for dry runs only; replace with real endpoints/creds before production.

## OTLP Gateway / Collector
- OPENLIT_ENDPOINT: https://test-openlit.local:4318
- OPENLIT_TOKEN: test-openlit-token-123
- TEMPO_ENDPOINT: https://test-tempo.local:4318
- LOKI_ENDPOINT: https://test-loki.local/loki/api/v1/push
- MIMIR_ENDPOINT: https://test-mimir.local/api/v1/push
- TLS/auth: plan to use basic auth or bearer tokens; currently placeholder.

## Grafana Stack
- GRAFANA_PASSWORD: TestGrafana!123
- S3 buckets (create or replace):
  - TEMPO_S3_BUCKET: mde-tempo-test-bucket
  - LOKI_S3_BUCKET: mde-loki-test-bucket
  - MIMIR_S3_BUCKET: mde-mimir-test-bucket
- S3 creds: TEMPO_S3_ACCESS_KEY/SECRET_KEY, LOKI_S3_ACCESS_KEY/SECRET_KEY, MIMIR_S3_ACCESS_KEY/SECRET_KEY (placeholders).

## RDS Postgres
- DB_INSTANCE_ID: mde-openlit-pg
- DB_USERNAME: mdeadmin
- DB_PASSWORD: TestDbPass!123
- DB_INSTANCE_CLASS: db.t4g.medium (sample)
- DB_STORAGE_GB: 50 (sample)

## OAuth (if enabling Grafana OAuth)
- Google:
  - GOOGLE_CLIENT_ID: test-google-client-id.apps.googleusercontent.com
  - GOOGLE_CLIENT_SECRET: test-google-client-secret
  - Redirect URI: https://<grafana-host>/login/google
- GitHub:
  - GITHUB_CLIENT_ID: test-github-client-id
  - GITHUB_CLIENT_SECRET: test-github-client-secret
  - Redirect URI: https://<grafana-host>/login/github

Notes:
- Replace all test values before real deployment.
- Restrict SGs/ports to trusted CIDRs; prefer TLS on OTLP/Grafana.
- Store real secrets in `~/.config/macos-development-environment/secrets.env` (not committed).

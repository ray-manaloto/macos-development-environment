# Claude Code Monitoring Reference

**Source:** https://code.claude.com/docs/en/monitoring-usage
**Fetched:** 2026-03-22
**Format:** OpenTelemetry (OTel) configuration and metrics/events schema

## Overview

Claude Code exports telemetry data through OpenTelemetry (OTel) for monitoring usage, costs, and tool activity across organizations. Both metrics (time series) and events (logs) are supported via configurable exporters.

---

## Environment Variables

### Core Telemetry Configuration

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | Enable telemetry collection (required to use any telemetry) | disabled | `1` (enabled) | Must be set to `1` to enable any telemetry export |
| `OTEL_METRICS_EXPORTER` | Metrics exporter backends (comma-separated, optional) | unset | `console`, `otlp`, `prometheus` | Configure only if metrics are needed |
| `OTEL_LOGS_EXPORTER` | Logs/events exporter backends (comma-separated, optional) | unset | `console`, `otlp` | Configure only if events/logs are needed |

### OTLP (OpenTelemetry Protocol) Configuration

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Protocol for OTLP exporter (applies to all signals unless overridden) | unset | `grpc`, `http/json`, `http/protobuf` | Overridable per signal type |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint for all signals | `http://localhost:4317` | HTTP/HTTPS URL | e.g., `http://localhost:4317` or `http://collector.example.com:4317` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Authentication headers for OTLP (all signals) | unset | HTTP headers format | e.g., `Authorization=Bearer token` |
| `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL` | Protocol override for metrics only | unset | `grpc`, `http/json`, `http/protobuf` | Overrides `OTEL_EXPORTER_OTLP_PROTOCOL` for metrics |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Metrics endpoint override | unset | HTTP/HTTPS URL | e.g., `http://localhost:4318/v1/metrics` |
| `OTEL_EXPORTER_OTLP_LOGS_PROTOCOL` | Protocol override for logs only | unset | `grpc`, `http/json`, `http/protobuf` | Overrides `OTEL_EXPORTER_OTLP_PROTOCOL` for logs |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | Logs endpoint override | unset | HTTP/HTTPS URL | e.g., `http://localhost:4318/v1/logs` |

### mTLS Authentication (for OTLP)

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY` | Client private key for mTLS (metrics) | unset | File path | Path to client key file in PEM format |
| `OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE` | Client certificate for mTLS (metrics) | unset | File path | Path to client certificate file in PEM format |

### Export Intervals & Behavior

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `OTEL_METRIC_EXPORT_INTERVAL` | Metrics export interval in milliseconds | `60000` (60 sec) | Integer >= 1000 | Use shorter intervals (e.g., 10000) for debugging; reset for production |
| `OTEL_LOGS_EXPORT_INTERVAL` | Logs/events export interval in milliseconds | `5000` (5 sec) | Integer >= 1000 | Logs export more frequently by default |
| `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` | Metrics temporality preference | `delta` | `delta`, `cumulative` | Set to `cumulative` if backend expects cumulative temporality |

### Content Logging Control

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `OTEL_LOG_USER_PROMPTS` | Include user prompt content in events | disabled | `1` (enabled) | Disabled by default for privacy; enables `prompt` field in events |
| `OTEL_LOG_TOOL_DETAILS` | Include MCP server/tool names and skill names in tool events | disabled | `1` (enabled) | Disabled by default; reveals user-specific configurations when enabled |

### Metrics Cardinality Control

| Variable | Description | Default Value | Example to Disable | Notes |
|----------|-------------|----------------|-------------------|-------|
| `OTEL_METRICS_INCLUDE_SESSION_ID` | Include `session.id` attribute in metrics | `true` | `false` | Impacts cardinality and storage requirements |
| `OTEL_METRICS_INCLUDE_VERSION` | Include `app.version` attribute in metrics | `false` | `true` | Generally disabled to reduce cardinality |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | Include `user.account_uuid` and `user.account_id` attributes in metrics | `true` | `false` | Controls per-user granularity in cost/usage tracking |

### Dynamic Headers (Enterprise)

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` | Interval for refreshing dynamic headers script | `1740000` (29 min) | Integer in milliseconds | Set in `.claude/settings.json` via `otelHeadersHelper` |

### Resource Attributes & Team Segmentation

| Variable | Description | Default | Valid Values | Notes |
|----------|-------------|---------|--------------|-------|
| `OTEL_RESOURCE_ATTRIBUTES` | Custom attributes for team/dept/org segmentation | unset | Comma-separated `key=value` pairs | Format: `department=eng,team.id=platform,cost_center=123` |

#### OTEL_RESOURCE_ATTRIBUTES Formatting Requirements

- **No spaces allowed** in values: `org.name=My Company` ❌ → `org.name=My_Company` ✅
- **Format:** Comma-separated key=value pairs: `key1=value1,key2=value2`
- **Allowed characters:** US-ASCII excluding control chars, whitespace, quotes, commas, semicolons, backslashes
- **Special characters:** Percent-encode if needed (e.g., `org.name=John%27s%20Organization`)
- **Note:** Quote wrapping does NOT escape spaces; `org.name="My Company"` includes literal quotes

---

## Metrics

### Metric Catalog

| Metric Name | Description | Unit | Exported By | Notes |
|-------------|-------------|------|------------|-------|
| `claude_code.session.count` | Count of CLI sessions started | `count` | Metrics exporter | Incremented at session start |
| `claude_code.lines_of_code.count` | Lines of code modified (added/removed) | `count` | Metrics exporter | Includes `type` attribute (added/removed) |
| `claude_code.pull_request.count` | Pull requests created via Claude Code | `count` | Metrics exporter | Incremented on PR creation |
| `claude_code.commit.count` | Git commits created via Claude Code | `count` | Metrics exporter | Incremented on commit creation |
| `claude_code.cost.usage` | Cost of Claude Code session | `USD` | Metrics exporter | Incremented after each API request; includes `model` attribute |
| `claude_code.token.usage` | Tokens used | `tokens` | Metrics exporter | Includes `type` (input/output/cacheRead/cacheCreation) and `model` |
| `claude_code.code_edit_tool.decision` | Code editing tool permission decisions | `count` | Metrics exporter | Tracks Edit/Write/NotebookEdit accept/reject; includes decision source |
| `claude_code.active_time.total` | Total active time (excluding idle) | `s` (seconds) | Metrics exporter | Includes `type` attribute (user/cli) |

### Metric Attributes

**Standard attributes** (included in all metrics):
- `session.id` (if `OTEL_METRICS_INCLUDE_SESSION_ID=true`, default: true)
- `app.version` (if `OTEL_METRICS_INCLUDE_VERSION=true`, default: false)
- `organization.id` (when authenticated)
- `user.account_uuid` (if `OTEL_METRICS_INCLUDE_ACCOUNT_UUID=true`, default: true)
- `user.account_id` (if `OTEL_METRICS_INCLUDE_ACCOUNT_UUID=true`, default: true)
- `user.id` (anonymous device identifier, always included)
- `user.email` (when authenticated via OAuth)
- `terminal.type` (when detected, e.g., iTerm.app, vscode, cursor, tmux)

**Context-specific attributes** (per metric):

| Metric | Additional Attributes | Values |
|--------|----------------------|--------|
| `claude_code.lines_of_code.count` | `type` | "added", "removed" |
| `claude_code.cost.usage` | `model` | e.g., "claude-sonnet-4-6" |
| `claude_code.token.usage` | `type`, `model` | type: "input", "output", "cacheRead", "cacheCreation"; model: "claude-sonnet-4-6" |
| `claude_code.code_edit_tool.decision` | `tool_name`, `decision`, `source`, `language` | tool_name: "Edit", "Write", "NotebookEdit"; decision: "accept", "reject"; source: "config", "hook", "user_permanent", "user_temporary", "user_abort", "user_reject"; language: e.g., "Python", "TypeScript", "JavaScript", "Markdown", "unknown" |
| `claude_code.active_time.total` | `type` | "user" (keyboard interactions), "cli" (tool execution/AI responses) |

---

## Events / Traces

Claude Code exports events via OpenTelemetry logs/events protocol when `OTEL_LOGS_EXPORTER` is configured.

### Event Correlation

| Attribute | Description | Usage |
|-----------|-------------|-------|
| `prompt.id` | UUID v4 correlating all events from a single user prompt | Filter events by `prompt.id` to trace all activity (user_prompt, api_request, tool_result events) triggered by one prompt |

### Event Types

#### 1. User Prompt Event

**Event Name:** `claude_code.user_prompt`

| Attribute | Type | Description | Conditional |
|-----------|------|-------------|-------------|
| `event.name` | string | "user_prompt" | Always |
| `event.timestamp` | ISO 8601 | Timestamp of prompt submission | Always |
| `event.sequence` | integer | Monotonically increasing counter within session | Always |
| `prompt.id` | UUID | Correlates with all subsequent events | Always |
| `prompt_length` | integer | Length of the prompt | Always |
| `prompt` | string | Prompt content (redacted by default) | Only if `OTEL_LOG_USER_PROMPTS=1` |
| Standard attributes | — | (session.id, user.id, etc.) | Always |

#### 2. Tool Result Event

**Event Name:** `claude_code.tool_result`

| Attribute | Type | Description | Notes |
|-----------|------|-------------|-------|
| `event.name` | string | "tool_result" | Always |
| `event.timestamp` | ISO 8601 | Timestamp of tool completion | Always |
| `event.sequence` | integer | Monotonically increasing counter | Always |
| `prompt.id` | UUID | Links to triggering prompt | Always |
| `tool_name` | string | Name of the tool executed | Always |
| `success` | string | "true" or "false" | Always |
| `duration_ms` | integer | Execution time in milliseconds | Always |
| `error` | string | Error message (if failed) | Only if tool failed |
| `decision_type` | string | "accept" or "reject" | Always |
| `decision_source` | string | Decision source | Always: "config", "hook", "user_permanent", "user_temporary", "user_abort", "user_reject" |
| `tool_result_size_bytes` | integer | Size of tool result | Always |
| `mcp_server_scope` | string | MCP server scope identifier | Only for MCP tools |
| `tool_parameters` | JSON string | Tool-specific parameters | When available; may contain sensitive values (bash commands, file paths) |
| Standard attributes | — | (session.id, user.id, etc.) | Always |

**Tool-specific tool_parameters fields:**
- **Bash tool:** `bash_command`, `full_command`, `timeout`, `description`, `dangerouslyDisableSandbox`, `git_commit_id` (commit SHA on success)
- **MCP tools** (if `OTEL_LOG_TOOL_DETAILS=1`): `mcp_server_name`, `mcp_tool_name`
- **Skill tool** (if `OTEL_LOG_TOOL_DETAILS=1`): `skill_name`

#### 3. API Request Event

**Event Name:** `claude_code.api_request`

| Attribute | Type | Description | Notes |
|-----------|------|-------------|-------|
| `event.name` | string | "api_request" | Always |
| `event.timestamp` | ISO 8601 | Timestamp of request | Always |
| `event.sequence` | integer | Monotonically increasing counter | Always |
| `prompt.id` | UUID | Links to triggering prompt | Always |
| `model` | string | Model used (e.g., "claude-sonnet-4-6") | Always |
| `cost_usd` | float | Estimated cost in USD | Always |
| `duration_ms` | integer | Request duration in milliseconds | Always |
| `input_tokens` | integer | Input token count | Always |
| `output_tokens` | integer | Output token count | Always |
| `cache_read_tokens` | integer | Tokens read from cache | Always |
| `cache_creation_tokens` | integer | Tokens used for cache creation | Always |
| `speed` | string | "fast" or "normal" | Indicates fast mode status |
| Standard attributes | — | (session.id, user.id, etc.) | Always |

#### 4. API Error Event

**Event Name:** `claude_code.api_error`

| Attribute | Type | Description | Notes |
|-----------|------|-------------|-------|
| `event.name` | string | "api_error" | Always |
| `event.timestamp` | ISO 8601 | Timestamp of error | Always |
| `event.sequence` | integer | Monotonically increasing counter | Always |
| `prompt.id` | UUID | Links to triggering prompt | Always |
| `model` | string | Model used (e.g., "claude-sonnet-4-6") | Always |
| `error` | string | Error message | Always |
| `status_code` | string | HTTP status code or "undefined" | Always |
| `duration_ms` | integer | Request duration in milliseconds | Always |
| `attempt` | integer | Attempt number (for retried requests) | Always |
| `speed` | string | "fast" or "normal" | Indicates fast mode status |
| Standard attributes | — | (session.id, user.id, etc.) | Always |

#### 5. Tool Decision Event

**Event Name:** `claude_code.tool_decision`

| Attribute | Type | Description | Notes |
|-----------|------|-------------|-------|
| `event.name` | string | "tool_decision" | Always |
| `event.timestamp` | ISO 8601 | Timestamp of decision | Always |
| `event.sequence` | integer | Monotonically increasing counter | Always |
| `prompt.id` | UUID | Links to triggering prompt | Always |
| `tool_name` | string | Tool name (e.g., "Read", "Edit", "Write", "NotebookEdit") | Always |
| `decision` | string | "accept" or "reject" | Always |
| `source` | string | Decision source | Always: "config", "hook", "user_permanent", "user_temporary", "user_abort", "user_reject" |
| Standard attributes | — | (session.id, user.id, etc.) | Always |

---

## Settings.json Configuration

### OTel Headers Helper (Dynamic Headers)

**Location:** `.claude/settings.json`

```json
{
  "otelHeadersHelper": "/bin/generate_opentelemetry_headers.sh"
}
```

**Requirements:**
- Script must output valid JSON with string key-value pairs representing HTTP headers
- Script runs at startup and periodically (default: every 29 minutes)
- Customizable interval via `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS`
- Supports token refresh for dynamic authentication

**Example script:**
```bash
#!/bin/bash
echo "{\"Authorization\": \"Bearer $(get-token.sh)\", \"X-API-Key\": \"$(get-api-key.sh)\"}"
```

---

## Resource Attributes

All metrics and events include these resource attributes:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `service.name` | Service identifier | "claude-code" |
| `service.version` | Current Claude Code version | "1.0.0" |
| `os.type` | Operating system | "darwin", "linux", "windows" |
| `os.version` | OS version string | "14.3" |
| `host.arch` | Host architecture | "amd64", "arm64" |
| `wsl.version` | WSL version (Windows only) | Only present when running on WSL |

**Meter Name:** `com.anthropic.claude_code`

---

## Administrator Configuration

Administrators can configure OpenTelemetry settings for all users via a managed settings file distributed through MDM or device management solutions.

**Example managed settings configuration:**
```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector.example.com:4317",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer example-token"
  }
}
```

**Note:** Environment variables in managed settings have high precedence and cannot be overridden by users.

---

## Example Configurations

### Console Debugging (1-second intervals)
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=console
export OTEL_METRIC_EXPORT_INTERVAL=1000
```

### OTLP/gRPC (Standard)
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Prometheus
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=prometheus
```

### Multiple Exporters
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=console,otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/json
```

### Different Endpoints for Metrics and Logs
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_METRICS_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://metrics.example.com:4318
export OTEL_EXPORTER_OTLP_LOGS_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://logs.example.com:4317
```

### Metrics Only (No Events/Logs)
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Events/Logs Only (No Metrics)
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---

## Deprecated Settings

None explicitly listed in official documentation. However, the following features are noted as optional/beta:
- **Server-managed settings (beta):** Subject to change in future releases

---

## Security Considerations

### Privacy & Data Handling

1. **Telemetry is opt-in**: Requires explicit `CLAUDE_CODE_ENABLE_TELEMETRY=1` to enable

2. **Code content exclusion**: Raw file contents and code snippets are NOT included in metrics or events
   - However: Tool execution events include bash commands and file paths in `tool_parameters` field, which may contain sensitive values
   - **Mitigation:** Configure telemetry backend to filter/redact `tool_parameters`

3. **User email handling**: When authenticated via OAuth, `user.email` is included in telemetry attributes
   - **Mitigation:** Configure backend to filter/redact this field if privacy is a concern

4. **Prompt content handling**: User prompt content is NOT collected by default
   - **Default:** Only `prompt_length` is recorded
   - **Opt-in:** Set `OTEL_LOG_USER_PROMPTS=1` to include full `prompt` field

5. **MCP/Skill name logging**: MCP server/tool names and skill names are NOT logged by default (reveals user-specific configurations)
   - **Opt-in:** Set `OTEL_LOG_TOOL_DETAILS=1` to include `mcp_server_name`, `mcp_tool_name`, and `skill_name`

6. **prompt.id intentionally excluded from metrics**: Each prompt generates a unique ID, which would create unbounded cardinality in time series
   - Used only for event-level analysis and audit trails

### Backend Security

- Support for mTLS authentication via `OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY` and `OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE`
- Support for custom authorization headers via `OTEL_EXPORTER_OTLP_HEADERS`
- Support for dynamic header refresh via `otelHeadersHelper` script in `.claude/settings.json`

---

## Data Analysis Use Cases

### Usage Monitoring
- **Token usage breakdown** by type (input/output), user, team, or model
- **Session adoption** and engagement trends over time
- **Code productivity** measured by lines added/removed
- **Development workflow impact** via commit and PR metrics

### Cost Monitoring
- **Cost trends** across teams or individuals
- **High-usage session identification** for optimization
- **Note:** Metrics are approximations; refer to API provider (Claude Console, AWS Bedrock, Google Cloud Vertex) for official billing

### Alerting & Segmentation
Common alerts:
- Cost spikes
- Unusual token consumption
- High session volume from specific users

Segmentation dimensions:
- `user.account_uuid` / `user.account_id`
- `organization.id`
- `session.id`
- `model`
- `app.version`
- Custom attributes via `OTEL_RESOURCE_ATTRIBUTES`

### Event Analysis
- **Tool usage patterns:** Most frequently used tools, success rates, average execution times
- **Error patterns:** By tool type, model, or user
- **Performance monitoring:** API request durations, tool execution times

---

## Backend Recommendations

### For Metrics
- **Time series databases** (e.g., Prometheus): Rate calculations, aggregated metrics
- **Columnar stores** (e.g., ClickHouse): Complex queries, unique user analysis
- **Full-featured platforms** (e.g., Honeycomb, Datadog): Advanced querying, visualization, alerting

### For Events/Logs
- **Log aggregation** (e.g., Elasticsearch, Loki): Full-text search, log analysis
- **Columnar stores** (e.g., ClickHouse): Structured event analysis
- **Full-featured platforms** (e.g., Honeycomb, Datadog): Correlation between metrics and events

### For DAU/WAU/MAU Metrics
- Requires backends with efficient unique value queries (e.g., Honeycomb, Datadog)

---

## Additional Resources

- **Claude Code ROI Measurement Guide:** Comprehensive guide on measuring ROI, including telemetry setup, cost analysis, productivity metrics, and automated reporting with ready-to-use Docker Compose configurations, Prometheus/OTel setups, and templates for productivity reports
- **Claude Code Monitoring (Bedrock):** For Amazon Bedrock-specific monitoring guidance
- **OpenTelemetry Specification:** Official OTel spec for advanced configuration options

---

## Implementation Checklist

- [ ] Set `CLAUDE_CODE_ENABLE_TELEMETRY=1`
- [ ] Choose metrics exporter: `console` (debug), `otlp` (production), or `prometheus`
- [ ] Choose logs exporter: `otlp` (production) or `console` (debug)
- [ ] Configure OTLP endpoint if using OTLP: `OTEL_EXPORTER_OTLP_ENDPOINT`
- [ ] Set authentication headers if required: `OTEL_EXPORTER_OTLP_HEADERS`
- [ ] Configure export intervals: `OTEL_METRIC_EXPORT_INTERVAL`, `OTEL_LOGS_EXPORT_INTERVAL`
- [ ] Control cardinality: Review `OTEL_METRICS_INCLUDE_*` settings
- [ ] Configure team segmentation: `OTEL_RESOURCE_ATTRIBUTES`
- [ ] Add dynamic headers helper if needed: `otelHeadersHelper` in `.claude/settings.json`
- [ ] Test with short export intervals (debug), reset for production
- [ ] Configure backend filtering/redaction for sensitive fields (`tool_parameters`, `user.email`, `prompt` content)
- [ ] Set up dashboards and alerts in backend

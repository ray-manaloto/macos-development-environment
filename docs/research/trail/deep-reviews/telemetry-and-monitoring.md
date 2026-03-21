# Claude Code Telemetry, Monitoring, and Observability

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://code.claude.com/docs/en/monitoring-usage (official monitoring/OTel docs)
- https://code.claude.com/docs/en/hooks (complete hooks reference)
- https://code.claude.com/docs/en/settings (settings reference)
- https://code.claude.com/docs/en/cli-reference (CLI flags reference)
- https://github.com/anthropics/claude-code-monitoring-guide (official ROI measurement guide)
- https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock (AWS Bedrock monitoring)
- Local filesystem: `~/.claude/transcripts/` (verified transcript format, 510 JSONL files)
- `claude --help` output (verified all CLI flags)

---

## 1. Native OpenTelemetry Integration (First-Party)

Claude Code has **full native OpenTelemetry support** as of current version. This is the primary and recommended monitoring path.

### 1.1 Enabling Telemetry

Set `CLAUDE_CODE_ENABLE_TELEMETRY=1` to activate. Without this, no telemetry is collected.

### 1.2 Exporter Configuration

| Variable | Options | Default |
|----------|---------|---------|
| `OTEL_METRICS_EXPORTER` | `otlp`, `prometheus`, `console` (comma-separated) | none |
| `OTEL_LOGS_EXPORTER` | `otlp`, `console` (comma-separated) | none |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc`, `http/json`, `http/protobuf` | -- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | URL | -- |
| `OTEL_METRIC_EXPORT_INTERVAL` | ms | 60000 |
| `OTEL_LOGS_EXPORT_INTERVAL` | ms | 5000 |

Metrics and logs can target **separate endpoints** using signal-specific overrides:
- `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL` / `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`
- `OTEL_EXPORTER_OTLP_LOGS_PROTOCOL` / `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`

Authentication: `OTEL_EXPORTER_OTLP_HEADERS` or mTLS via `OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY` / `OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE`.

### 1.3 Available Metrics (8 counters)

| Metric | Unit | Extra Attributes |
|--------|------|------------------|
| `claude_code.session.count` | count | -- |
| `claude_code.lines_of_code.count` | count | `type` (added/removed) |
| `claude_code.pull_request.count` | count | -- |
| `claude_code.commit.count` | count | -- |
| `claude_code.cost.usage` | USD | `model` |
| `claude_code.token.usage` | tokens | `type` (input/output/cacheRead/cacheCreation), `model` |
| `claude_code.code_edit_tool.decision` | count | `tool_name`, `decision`, `source`, `language` |
| `claude_code.active_time.total` | seconds | `type` (user/cli) |

### 1.4 Available Events (5 event types, via OTEL_LOGS_EXPORTER)

All events share a `prompt.id` (UUID v4) for correlation within a single user prompt.

**`claude_code.user_prompt`** -- logged when user submits prompt
- `prompt_length`, `prompt` (redacted unless `OTEL_LOG_USER_PROMPTS=1`)

**`claude_code.tool_result`** -- logged when tool completes
- `tool_name`, `success`, `duration_ms`, `error`, `decision_type`, `decision_source`
- `tool_result_size_bytes`, `mcp_server_scope`, `tool_parameters` (JSON string)
- Bash tool parameters include `bash_command`, `full_command`, `timeout`, `git_commit_id`
- MCP tools include `mcp_server_name`, `mcp_tool_name` (when `OTEL_LOG_TOOL_DETAILS=1`)

**`claude_code.api_request`** -- logged per API call
- `model`, `cost_usd`, `duration_ms`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`, `speed`

**`claude_code.api_error`** -- logged on API failure
- `model`, `error`, `status_code`, `duration_ms`, `attempt`, `speed`

**`claude_code.tool_decision`** -- logged on accept/reject
- `tool_name`, `decision`, `source`

### 1.5 Standard Attributes on All Metrics/Events

| Attribute | Notes |
|-----------|-------|
| `session.id` | Controllable via `OTEL_METRICS_INCLUDE_SESSION_ID` (default: true) |
| `app.version` | Off by default, enable via `OTEL_METRICS_INCLUDE_VERSION` |
| `organization.id` | When authenticated |
| `user.account_uuid` | Controllable via `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` (default: true) |
| `user.id` | Anonymous device/installation ID, always included |
| `user.email` | When OAuth authenticated |
| `terminal.type` | iTerm.app, vscode, cursor, tmux |

### 1.6 Resource Attributes (Service Info)

- `service.name`: `claude-code`
- `service.version`: current version
- `os.type`, `os.version`, `host.arch`
- `wsl.version` (when on WSL)
- Meter name: `com.anthropic.claude_code`

Custom resource attributes for multi-team: `OTEL_RESOURCE_ATTRIBUTES="department=engineering,team.id=platform,cost_center=eng-123"`

### 1.7 Cardinality Control

| Variable | Default | Purpose |
|----------|---------|---------|
| `OTEL_METRICS_INCLUDE_SESSION_ID` | true | Session-level granularity |
| `OTEL_METRICS_INCLUDE_VERSION` | false | Version tracking |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | true | User-level granularity |

### 1.8 Privacy Controls

| Variable | Default | What it controls |
|----------|---------|-----------------|
| `OTEL_LOG_USER_PROMPTS` | disabled | Include prompt text content |
| `OTEL_LOG_TOOL_DETAILS` | disabled | MCP server/tool names, skill names |

### 1.9 Dynamic Headers for Enterprise Auth

Setting: `otelHeadersHelper` in `settings.json` -- points to a script that outputs JSON headers.
Refresh interval: `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` (default: 1740000ms / 29 min).

### 1.10 Administrator Managed Configuration

Admins can push OTel settings via managed settings (MDM, plist, registry, `managed-settings.json`) using the `env` key. These cannot be overridden by users.

---

## 2. CLI Debug and Verbose Modes

### 2.1 `--debug [filter]`

Enables debug logging with optional category filtering.

**Syntax:** `claude --debug "api,hooks"` or `claude --debug "!statsig,!file"` (exclusion)

Known debug categories (from docs and help output):
- `api` -- API request/response details
- `hooks` -- Hook execution lifecycle
- `mcp` -- MCP server communication
- `file` -- File operations
- `statsig` -- Feature flag evaluation
- `1p` -- First-party internals

**`--debug-file <path>`** -- Write debug logs to a specific file (implicitly enables debug mode).

### 2.2 `--verbose`

Shows full turn-by-turn output. When hooks fail with non-zero exit (other than 2), stderr is shown in verbose mode.

### 2.3 `--max-budget-usd <amount>`

Budget cap for print mode. Stops API calls when limit reached.

### 2.4 `--max-turns <count>`

Limits agentic turns in print mode. Exits with error when reached.

### 2.5 Console Exporter for Quick Debugging

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=console
export OTEL_METRIC_EXPORT_INTERVAL=1000  # 1 second
```

---

## 3. Session Transcripts

### 3.1 Location and Format

- Path: `~/.claude/transcripts/ses_<session_id>.jsonl`
- Format: JSONL (one JSON object per line)
- Currently 510 transcript files on this machine

### 3.2 Transcript Record Types

Each line is a JSON object with a `type` field:

| Type | Fields | Description |
|------|--------|-------------|
| `user` | `timestamp`, `content` | User message |
| `tool_use` | `timestamp`, `tool_name`, `tool_input` | Tool invocation |
| `tool_result` | `timestamp`, `tool_name`, `tool_input`, `tool_output` | Tool result |

### 3.3 Hooks Receive Transcript Path

Every hook invocation receives `transcript_path` in its JSON input, allowing hooks to read the transcript for analysis.

### 3.4 Session Persistence Control

- `--no-session-persistence` -- disables saving (print mode only)
- `cleanupPeriodDays` setting -- auto-delete old sessions (default: 30 days)
- Setting `cleanupPeriodDays: 0` deletes all transcripts and disables persistence

### 3.5 Session History

`~/.claude/history.jsonl` -- separate history file tracking session metadata.

---

## 4. Hook-Based Telemetry (Custom Observability Layer)

### 4.1 Hook Events for Monitoring

There are **22 hook events**. The most useful for telemetry:

| Event | Telemetry Use | Blocking? |
|-------|---------------|-----------|
| `SessionStart` | Log session begin, set up env vars | No |
| `SessionEnd` | Log session end, archive data | No |
| `UserPromptSubmit` | Log user prompts, rate limiting | Yes |
| `PreToolUse` | Audit tool usage before execution | Yes |
| `PostToolUse` | Track tool success, duration | No |
| `PostToolUseFailure` | Track tool errors | No |
| `Stop` | Log agent completion | Yes |
| `StopFailure` | Log API errors | No |
| `SubagentStart` / `SubagentStop` | Track subagent lifecycle | No/Yes |
| `TaskCompleted` | Track task completion | Yes |
| `Notification` | Track notification events | No |

### 4.2 Hook Handler Types

1. **command** -- Shell script receives JSON on stdin; best for local file logging
2. **http** -- POST to endpoint; best for remote telemetry collectors
3. **prompt** -- LLM evaluation; for policy/safety checks
4. **agent** -- Subagent with tool access; for complex analysis

### 4.3 Common Input Fields (Available to ALL hooks)

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions",
  "hook_event_name": "EventName"
}
```

### 4.4 Event-Specific Input Schemas

**PreToolUse / PostToolUse:**
```json
{
  "tool_name": "Bash|Edit|Write|Read|...|mcp__*",
  "tool_input": {},
  "tool_use_id": "toolu_01ABC123...",
  "tool_response": {}
}
```

**SessionStart:**
```json
{
  "source": "startup|resume|clear|compact",
  "model": "claude-sonnet-4-6"
}
```

**SubagentStart / SubagentStop:**
```json
{
  "agent_id": "agent-abc123",
  "agent_type": "Explore",
  "agent_transcript_path": "path/to/transcript"
}
```

### 4.5 Environment Variables for Hooks

- `CLAUDE_ENV_FILE` -- SessionStart only; write exports here to persist env vars
- `CLAUDE_CODE_REMOTE` -- "true" in web, unset in CLI
- `CLAUDE_PROJECT_DIR` -- project root directory

### 4.6 Async Hooks

Command hooks support `"async": true` to run in background without blocking. Ideal for non-critical telemetry that should not slow down the user.

### 4.7 Telemetry Hook Configuration Example

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/telemetry-session-start.sh",
        "async": true
      }]
    }],
    "PostToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "http",
        "url": "https://otel-collector.local:4318/v1/logs",
        "timeout": 5,
        "headers": { "Authorization": "Bearer $OTEL_TOKEN" },
        "allowedEnvVars": ["OTEL_TOKEN"]
      }]
    }],
    "PostToolUseFailure": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/log-tool-error.sh",
        "async": true
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/telemetry-session-end.sh"
      }]
    }]
  }
}
```

---

## 5. Third-Party Monitoring Tools and Resources

### 5.1 Official: claude-code-monitoring-guide

**Repository:** https://github.com/anthropics/claude-code-monitoring-guide

Provides a production-ready monitoring stack:
- `docker-compose.yml` -- one-command deployment of Prometheus + OTel Collector + Grafana
- `prometheus.yml` -- pre-configured scrape jobs
- `otel-collector-config.yaml` -- collector pipeline config
- `grafana/` -- pre-built dashboards for cost, tokens, productivity, team adoption
- `report-generation-prompt.md` -- LLM prompt for automated ROI reports
- Linear integration for productivity correlation
- 220 stars, 27 forks as of research date

### 5.2 AWS Bedrock Monitoring Guide

**URL:** https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/MONITORING.md

Bedrock-specific monitoring for Claude Code usage.

### 5.3 Backend Recommendations (from official docs)

**For metrics:**
- Time series: Prometheus (rate calculations, aggregated metrics)
- Columnar: ClickHouse (complex queries, unique user analysis)
- Full observability: Honeycomb, Datadog (advanced querying, visualization, alerting)

**For events/logs:**
- Log aggregation: Elasticsearch, Loki
- Columnar: ClickHouse
- Full observability: Honeycomb, Datadog

For DAU/WAU/MAU analysis, prefer backends with efficient unique value queries.

---

## 6. Metrics Temporality

`OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` -- default `delta`. Set to `cumulative` if your backend expects it (e.g., some Prometheus setups).

---

## 7. Implementation Plan for Our Setup

### 7.1 Phase 1: Local Console Observability (Immediate)

Add to `.claude/settings.local.json`:
```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "console",
    "OTEL_LOGS_EXPORTER": "console",
    "OTEL_METRIC_EXPORT_INTERVAL": "10000",
    "OTEL_LOG_TOOL_DETAILS": "1"
  }
}
```

### 7.2 Phase 2: Hook-Based JSONL Logging

Create Python hooks (per no-shell-scripts policy) in `src/mde/hooks/telemetry/`:
- `session_start.py` -- log session begin with model, source
- `post_tool_use.py` -- log tool name, duration, success/failure
- `session_end.py` -- log session end, compute session summary
- Output to `~/.claude/telemetry/` as structured JSONL

Register via `mde-py hooks telemetry <subcommand>` entry points.

### 7.3 Phase 3: OTel Collector Stack

Deploy using the official `claude-code-monitoring-guide` Docker Compose:
```bash
git clone https://github.com/anthropics/claude-code-monitoring-guide
cd claude-code-monitoring-guide
docker-compose up -d
```

Then configure endpoints:
```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1"
  }
}
```

### 7.4 Phase 4: Transcript Analysis

Build a transcript analyzer (Python in `src/mde/`) that:
- Reads `~/.claude/transcripts/*.jsonl`
- Computes per-session statistics (tool counts, durations, error rates)
- Generates summary reports
- CLI: `uv run mde-py telemetry analyze [--session-id ID | --all | --last N]`

### 7.5 Phase 5: Grafana Dashboards

Import pre-built dashboards from the monitoring guide repo, then customize:
- Cost per session / per day / per project
- Token usage breakdown (input/output/cache)
- Tool usage frequency and error rates
- Active time tracking (user vs CLI)
- Lines of code modified over time

---

## 8. Key Files and Paths

| Path | Purpose |
|------|---------|
| `~/.claude/settings.json` | User-level settings (OTel env vars go here) |
| `.claude/settings.json` | Project-level settings (shared with team) |
| `.claude/settings.local.json` | Local project settings (not shared) |
| `~/.claude/transcripts/ses_*.jsonl` | Session transcripts |
| `~/.claude/history.jsonl` | Session history metadata |
| Managed: `/Library/Application Support/ClaudeCode/managed-settings.json` | macOS admin settings |
| Schema: `https://json.schemastore.org/claude-code-settings.json` | Settings JSON schema |

---

## 9. Quick Reference: All Telemetry Environment Variables

```bash
# Core
CLAUDE_CODE_ENABLE_TELEMETRY=1

# Exporters
OTEL_METRICS_EXPORTER=otlp,console,prometheus
OTEL_LOGS_EXPORTER=otlp,console

# OTLP config (general)
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer token"

# OTLP config (per-signal overrides)
OTEL_EXPORTER_OTLP_METRICS_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://metrics:4318
OTEL_EXPORTER_OTLP_LOGS_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://logs:4317

# mTLS
OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY=/path/to/key
OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE=/path/to/cert

# Intervals
OTEL_METRIC_EXPORT_INTERVAL=60000
OTEL_LOGS_EXPORT_INTERVAL=5000

# Privacy
OTEL_LOG_USER_PROMPTS=1
OTEL_LOG_TOOL_DETAILS=1

# Cardinality
OTEL_METRICS_INCLUDE_SESSION_ID=true
OTEL_METRICS_INCLUDE_VERSION=false
OTEL_METRICS_INCLUDE_ACCOUNT_UUID=true

# Temporality
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta

# Resource attributes
OTEL_RESOURCE_ATTRIBUTES="department=engineering,team.id=platform"

# Dynamic headers refresh
CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS=1740000
```

---

## 10. Sources Consulted

| Source | URL | Content Retrieved |
|--------|-----|-------------------|
| Official monitoring docs | https://code.claude.com/docs/en/monitoring-usage | Full page |
| Official hooks reference | https://code.claude.com/docs/en/hooks | Full page |
| Official settings reference | https://code.claude.com/docs/en/settings | Full page |
| Official CLI reference | https://code.claude.com/docs/en/cli-reference | Full page |
| Official monitoring guide repo | https://github.com/anthropics/claude-code-monitoring-guide | README + structure |
| AWS Bedrock monitoring | https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock | MONITORING.md |
| Local transcripts | `~/.claude/transcripts/` | 510 JSONL files verified |
| CLI help output | `claude --help` | All flags verified |

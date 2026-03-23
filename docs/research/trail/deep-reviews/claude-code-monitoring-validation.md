# Claude Code Monitoring Settings Validation

Source: https://code.claude.com/docs/en/monitoring-usage
Reviewed: 2026-03-22
Reviewer: deep-review-agent (researcher)

---

## Complete Environment Variable Inventory

All variables extracted directly from the official docs page (JSX-rendered content, confirmed).

### Table: All Vars from Official Docs vs Our settings.json

| Environment Variable | Description | Default | Example Values | We Set It? | Our Value | Status |
|---|---|---|---|---|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | Enable telemetry collection (required) | disabled | `1` | YES | `"1"` | CORRECT |
| `OTEL_METRICS_EXPORTER` | Metrics exporter types, comma-separated | unset | `console`, `otlp`, `prometheus` | YES | `"otlp"` | CORRECT |
| `OTEL_LOGS_EXPORTER` | Logs/events exporter types, comma-separated | unset | `console`, `otlp` | YES | `"otlp"` | CORRECT |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Protocol for OTLP exporter, applies to all signals | unset | `grpc`, `http/json`, `http/protobuf` | YES | `"grpc"` | CORRECT |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint for all signals | unset | `http://localhost:4317` | YES | `"http://localhost:4317"` | CORRECT |
| `OTEL_EXPORTER_OTLP_HEADERS` | Authentication headers for OTLP | unset | `Authorization=Bearer token` | NO | — | NOT SET (OK for local) |
| `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL` | Protocol for metrics, overrides general setting | unset | `grpc`, `http/json`, `http/protobuf` | NO | — | NOT SET (OK) |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | OTLP metrics endpoint, overrides general setting | unset | `http://localhost:4318/v1/metrics` | NO | — | NOT SET (OK) |
| `OTEL_EXPORTER_OTLP_LOGS_PROTOCOL` | Protocol for logs, overrides general setting | unset | `grpc`, `http/json`, `http/protobuf` | NO | — | NOT SET (OK) |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | OTLP logs endpoint, overrides general setting | unset | `http://localhost:4318/v1/logs` | NO | — | NOT SET (OK) |
| `OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY` | Client key for mTLS authentication | unset | Path to client key file | NO | — | NOT SET (OK) |
| `OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE` | Client certificate for mTLS authentication | unset | Path to client cert file | NO | — | NOT SET (OK) |
| `OTEL_METRIC_EXPORT_INTERVAL` | Export interval in ms (default: 60000) | `60000` | `5000`, `60000` | YES | `"10000"` | REVIEW (see below) |
| `OTEL_LOGS_EXPORT_INTERVAL` | Logs export interval in ms (default: 5000) | `5000` | `1000`, `10000` | YES | `"5000"` | CORRECT (matches default) |
| `OTEL_LOG_USER_PROMPTS` | Enable logging of user prompt content (default: disabled) | disabled | `1` | YES | `"1"` | INTENTIONAL (review privacy) |
| `OTEL_LOG_TOOL_DETAILS` | Enable logging of MCP server/tool names and skill names (default: disabled) | disabled | `1` | NO | — | PLANNED addition |
| `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` | Temporality preference | `delta` | `delta`, `cumulative` | NO | — | NOT SET (defaults to `delta`, OK) |
| `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` | Interval for refreshing dynamic headers (default: 1740000ms / 29 min) | `1740000` | `900000` | NO | — | NOT SET (OK) |
| `OTEL_METRICS_INCLUDE_SESSION_ID` | Include session.id in metrics | `true` | `false` | YES | `"true"` | CORRECT (matches default explicitly) |
| `OTEL_METRICS_INCLUDE_VERSION` | Include app.version in metrics | `false` | `true` | YES | `"true"` | SET TO non-default — intentional to track version |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | Include user.account_uuid and user.account_id in metrics | `true` | `false` | NO | — | NOT SET (defaults to `true`, OK) |
| `OTEL_RESOURCE_ATTRIBUTES` | Custom attributes for team/dept identification | unset | `department=engineering,team.id=platform` | NO | — | PLANNED (via service.name) |

### Vars in Our settings.json That Are NOT in the Official Docs

| Variable | Our Value | Finding |
|---|---|---|
| `OTEL_SERVICE_NAME` | `"mde-claude-code"` | NOT listed in official docs. Claude Code hardcodes `service.name=claude-code` as a resource attribute. Setting `OTEL_SERVICE_NAME` may override this in the OTEL SDK layer, but it is not a documented Claude Code config variable. **This is the planned removal, and it is the correct call.** The documented way is via `OTEL_RESOURCE_ATTRIBUTES=service.name=mde-claude-code`. |
| `ENABLE_LSP_TOOL` | `"1"` | This is a Claude Code plugin/feature flag, not a monitoring variable. Not in scope for this review, and correctly set. |

---

## Metrics Schema Verification

### Complete Metric Catalog (from official docs)

| Metric Name | Description | Unit | Additional Attributes |
|---|---|---|---|
| `claude_code.session.count` | Count of CLI sessions started | `count` | (standard only) |
| `claude_code.lines_of_code.count` | Count of lines of code modified | `count` | `type`: "added", "removed" |
| `claude_code.pull_request.count` | Number of pull requests created | `count` | (standard only) |
| `claude_code.commit.count` | Number of git commits created | `count` | (standard only) |
| `claude_code.cost.usage` | Cost of the Claude Code session | `USD` | `model` |
| `claude_code.token.usage` | Number of tokens used | `tokens` | `type` ("input","output","cacheRead","cacheCreation"), `model` |
| `claude_code.code_edit_tool.decision` | Count of code editing tool permission decisions | `count` | `tool_name` ("Edit","Write","NotebookEdit"), `decision` ("accept","reject"), `source` ("config","hook","user_permanent","user_temporary","user_abort","user_reject"), `language` ("TypeScript","Python","JavaScript","Markdown","unknown") |
| `claude_code.active_time.total` | Total active time in seconds | `s` (seconds) | `type` ("user", "cli") |

**Count: 8 metrics total.** Our reference doc correctly listed all 8.

### Standard Attributes (All Metrics)

| Attribute | Control | Default Inclusion |
|---|---|---|
| `session.id` | `OTEL_METRICS_INCLUDE_SESSION_ID` | true |
| `app.version` | `OTEL_METRICS_INCLUDE_VERSION` | false |
| `organization.id` | Always when authenticated | when available |
| `user.account_uuid` | `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | true |
| `user.account_id` | `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | true |
| `user.id` | Always | always |
| `user.email` | Always when OAuth | when available |
| `terminal.type` | Always when detected | when detected |

### Event-Only Attributes (Never on Metrics — Unbounded Cardinality)

- `prompt.id` — UUID v4 correlating all events for a single prompt
- `workspace.host_paths` — workspace path info

**Our reference doc was accurate on this distinction.**

---

## Events Schema Verification

### Complete Event Catalog

#### 1. `claude_code.user_prompt`
Logged when a user submits a prompt.

| Attribute | Conditional? |
|---|---|
| `event.name` = "user_prompt" | Always |
| `event.timestamp` | Always |
| `event.sequence` | Always |
| `prompt.id` | Always |
| `prompt_length` | Always |
| `prompt` | Only if `OTEL_LOG_USER_PROMPTS=1` |
| standard attributes | Always |

#### 2. `claude_code.tool_result`
Logged when a tool completes execution.

| Attribute | Conditional? |
|---|---|
| `event.name` = "tool_result" | Always |
| `event.timestamp` | Always |
| `event.sequence` | Always |
| `tool_name` | Always |
| `success` ("true"/"false") | Always |
| `duration_ms` | Always |
| `error` | Only if tool failed |
| `decision_type` ("accept"/"reject") | Always |
| `decision_source` ("config","hook","user_permanent","user_temporary","user_abort","user_reject") | Always |
| `tool_result_size_bytes` | Always |
| `mcp_server_scope` | Only for MCP tools |
| `tool_parameters` (JSON) | When available — may contain sensitive values |
| `bash_command`, `full_command`, `timeout`, `description`, `dangerouslyDisableSandbox`, `git_commit_id` | Bash tool specific, within tool_parameters |
| `mcp_server_name`, `mcp_tool_name` | Only if `OTEL_LOG_TOOL_DETAILS=1` |
| `skill_name` | Only if `OTEL_LOG_TOOL_DETAILS=1` |
| standard attributes | Always |

#### 3. `claude_code.api_request`
Logged for each API request to Claude.

| Attribute | Conditional? |
|---|---|
| `event.name` = "api_request" | Always |
| `event.timestamp` | Always |
| `event.sequence` | Always |
| `model` | Always |
| `cost_usd` | Always |
| `duration_ms` | Always |
| `input_tokens` | Always |
| `output_tokens` | Always |
| `cache_read_tokens` | Always |
| `cache_creation_tokens` | Always |
| `speed` ("fast"/"normal") | Always |
| standard attributes | Always |

#### 4. `claude_code.api_error`
Logged when an API request to Claude fails.

| Attribute | Conditional? |
|---|---|
| `event.name` = "api_error" | Always |
| `event.timestamp` | Always |
| `event.sequence` | Always |
| `model` | Always |
| `error` | Always |
| `status_code` (HTTP code or "undefined") | Always |
| `duration_ms` | Always |
| `attempt` | Always |
| `speed` ("fast"/"normal") | Always |
| standard attributes | Always |

#### 5. `claude_code.tool_decision`
Logged when a tool permission decision is made.

| Attribute | Conditional? |
|---|---|
| `event.name` = "tool_decision" | Always |
| `event.timestamp` | Always |
| `event.sequence` | Always |
| `tool_name` | Always |
| `decision` ("accept"/"reject") | Always |
| `source` ("config","hook","user_permanent","user_temporary","user_abort","user_reject") | Always |
| standard attributes | Always |

**Count: 5 event types.** Our reference doc listed all 5 correctly.

### Critical Finding: No Traces — Only Metrics + Logs

The official docs make NO mention of `OTEL_TRACES_EXPORTER`. Claude Code does NOT export OpenTelemetry traces. It exports only:
- **Metrics** via `OTEL_METRICS_EXPORTER`
- **Logs/Events** via `OTEL_LOGS_EXPORTER`

Our reference doc's section heading "Events / Traces" is technically misleading. The official documentation consistently uses "events" language. These are exported via the OTel Logs API (structured log records), NOT via the Traces/Spans API. There is no distributed tracing.

---

## Security & Privacy Analysis

### Default Behavior (What Is Logged by Default)

When `CLAUDE_CODE_ENABLE_TELEMETRY=1` and exporters are configured:

| Data Element | Logged by Default? | Notes |
|---|---|---|
| Session start/count | YES | Via `claude_code.session.count` |
| Token usage | YES | Counts only, not content |
| API costs (approximate) | YES | In USD |
| Model name | YES | e.g., "claude-sonnet-4-6" |
| Lines of code modified | YES | Count only (added/removed), not content |
| PR/commit counts | YES | Count only |
| Tool decisions (accept/reject) | YES | Via `claude_code.tool_decision` event |
| Tool execution results | YES | Via `claude_code.tool_result` event |
| `tool_parameters` (bash commands, file paths) | YES | **HIGH SENSITIVITY** — includes actual bash commands |
| `git_commit_id` | YES (on success) | Commit SHA in tool_result |
| `user.id` (anonymous device ID) | YES | Always |
| `user.email` | YES (when OAuth auth) | Personal data |
| `session.id` | YES (default: true) | Unique per session |
| `organization.id` | YES (when authenticated) | |
| `user.account_uuid` / `user.account_id` | YES (default: true) | Personal data |
| Prompt content | NO | Only `prompt_length` unless `OTEL_LOG_USER_PROMPTS=1` |
| MCP server names / tool names | NO | Unless `OTEL_LOG_TOOL_DETAILS=1` |
| Skill names | NO | Unless `OTEL_LOG_TOOL_DETAILS=1` |
| File content / code content | NO | Never |

### Privacy Implications of `OTEL_LOG_USER_PROMPTS=1` (We Have This Set)

Setting this variable adds the full `prompt` field to `claude_code.user_prompt` events. This means:
- Every user message/prompt is stored verbatim in your telemetry backend
- Prompts may contain: credentials, API keys, proprietary code, PII, confidential business information
- The telemetry backend becomes a secondary store of potentially sensitive user interactions
- **Risk:** If the OTEL collector or backend is compromised, all prompts are exposed
- **Mitigation options:**
  1. Ensure OTEL endpoint is localhost-only (as we currently have)
  2. Apply redaction rules at the collector level before forwarding
  3. Restrict backend access with strict RBAC
  4. Only set this in development/personal environments

**Assessment for our setup:** We have `OTEL_LOG_USER_PROMPTS=1` with `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` (local-only collector). This is acceptable for personal development use where you're both the user and the collector admin. **Do not set this in shared or team environments.**

### Privacy Implications of `OTEL_LOG_TOOL_DETAILS=1` (Planned Addition)

Setting this adds to `claude_code.tool_result` events:
- `mcp_server_name`: Names of connected MCP servers (reveals infrastructure/integrations)
- `mcp_tool_name`: Names of MCP tools used (reveals workflow and tooling)
- `skill_name`: Names of skills invoked (reveals automation setup)

**Risk:** Exposes configuration topology. For personal/local setup, this is acceptable. For team deployments, evaluate whether MCP server names contain sensitive organizational information.

**Assessment for our setup:** Adding `OTEL_LOG_TOOL_DETAILS=1` with localhost-only collector is acceptable. Useful for debugging which skills and MCP tools are being used and how often.

### `tool_parameters` Field — Default Sensitivity

This field is logged **by default** (not opt-in) and may contain:
- Bash commands (full command text including arguments)
- File paths
- Git commit IDs
- Timeout values
- `dangerouslyDisableSandbox` flag status

**Recommendation:** If using a remote/shared telemetry backend, configure redaction at the collector for `tool_parameters.bash_command` and `tool_parameters.full_command`.

---

## Gaps Found

### Variables in Official Docs Missing from Our Reference Doc

The reference doc (`claude-code-monitoring-reference.md`) is **comprehensive and accurate**. After careful comparison, all 22 variables from the official docs are present in the reference. No gaps found.

### Variables in Our settings.json Not in Official Docs

| Variable | Assessment |
|---|---|
| `OTEL_SERVICE_NAME` | **NOT a documented Claude Code config variable.** The official docs state that `service.name=claude-code` is a hardcoded resource attribute. `OTEL_SERVICE_NAME` is an OTEL SDK standard env var that Claude Code may or may not respect. The correct way to customize service name attribution is via `OTEL_RESOURCE_ATTRIBUTES=service.name=mde-claude-code`. **The planned removal is correct.** |

### Reference Doc Inaccuracies

1. **Section heading "Events / Traces"** (line 126): The section header says "Events / Traces" but Claude Code does NOT export traces. It uses the OTel Logs API for events. Should be "Events (via OTel Logs API)".

2. **`claude_code.active_time.total` unit**: Reference doc says `s` (seconds). Official docs confirm the unit field is just listed as "seconds" in the description. This is consistent.

3. **`OTEL_METRICS_INCLUDE_VERSION` default**: Reference doc says default is `false`. Official docs confirm default is `false`. **CORRECT.** However, our settings.json sets it to `"true"` — this is intentional (we want to track which Claude Code version is running).

4. **`OTEL_LOGS_EXPORT_INTERVAL` note**: The official docs say the default is `5000ms`. We have `OTEL_LOGS_EXPORT_INTERVAL=5000` set explicitly — this matches the default exactly. It can be removed from settings.json without effect if desired.

5. **No mention of traces exporter**: Reference doc's framing is correct, but the heading "Events / Traces" could mislead readers into thinking OTEL_TRACES_EXPORTER is relevant. It is not documented and should not be set.

### Additional Finding: `OTEL_HEADERS_HELPER_DEBOUNCE_MS` Alias

The official docs mention both `OTEL_HEADERS_HELPER_DEBOUNCE_MS` (short form, appears in env var table) and `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` (full canonical name in the refresh behavior section). The canonical name per the docs is `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS`. Our reference doc has the correct canonical name.

---

## Planned Changes Validation

### Change 1: Remove `OTEL_SERVICE_NAME`, Use `OTEL_RESOURCE_ATTRIBUTES=service.name=mde-claude-code`

**VALIDATED: CORRECT.**

Rationale from official docs:
- The official docs show `service.name=claude-code` as a **hardcoded resource attribute** (listed under "Service information" section).
- `OTEL_SERVICE_NAME` is not mentioned anywhere in the Claude Code monitoring docs.
- `OTEL_RESOURCE_ATTRIBUTES` IS documented (under "Multi-team organization support") and is the correct mechanism for adding or overriding resource attributes including `service.name`.
- The standard OTEL SDK behavior is that `OTEL_RESOURCE_ATTRIBUTES` values merge with/override code-specified resource attributes, making this the correct approach.

**Implementation:** In settings.json, replace:
```json
"OTEL_SERVICE_NAME": "mde-claude-code"
```
With:
```json
"OTEL_RESOURCE_ATTRIBUTES": "service.name=mde-claude-code"
```

**Warning on formatting:** The docs explicitly state no spaces are allowed in `OTEL_RESOURCE_ATTRIBUTES` values. `service.name=mde-claude-code` has no spaces — this is valid.

### Change 2: Add `OTEL_LOG_TOOL_DETAILS=1`

**VALIDATED: CORRECT AND SAFE for local setup.**

This is an official documented variable (table row [120-121] in extracted content):
- Description: "Enable logging of MCP server/tool names and skill names in tool events (default: disabled)"
- Effect: Adds `mcp_server_name`, `mcp_tool_name`, and `skill_name` to `claude_code.tool_result` events

For our local development setup with localhost-only collector, adding this provides valuable visibility into MCP and skill usage patterns. No privacy concern for personal setup.

### Change 3: Remove `OTEL_METRIC_EXPORT_INTERVAL` (Use Default 60000)

**VALIDATED: CORRECT for production use.**

From the official docs (text node [39]):
> "The default export intervals are 60 seconds for metrics and 5 seconds for logs. During setup, you may want to use shorter intervals for debugging purposes. Remember to reset these for production use."

We currently have `OTEL_METRIC_EXPORT_INTERVAL=10000` (10 seconds). The docs explicitly recommend reverting to the 60-second default for production. Removing this variable restores the documented production default.

**However, consider:** If this is an active development environment where you're frequently checking metrics, keeping a shorter interval (e.g., 30000) could be reasonable. The official guidance is to use 60000 for production.

---

## Additional Recommendations

### Recommendation 1: Explicitly Set `OTEL_METRICS_INCLUDE_ACCOUNT_UUID`

Default is `true`, which includes `user.account_uuid` and `user.account_id` in metrics. For personal local use this is fine. If metrics are ever forwarded to a shared backend, consider setting to `false`.

**Current status:** Not set (inherits `true` default). No action required for current setup.

### Recommendation 2: Keep `OTEL_LOGS_EXPORT_INTERVAL=5000` or Remove It

Currently set to `"5000"` which exactly matches the default. The setting is redundant but harmless. Can be removed for cleanliness.

### Recommendation 3: Consider `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE`

Not currently set (defaults to `delta`). If your Prometheus/Grafana setup expects cumulative counters, add:
```json
"OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE": "delta"
```
Since default is `delta` and we're using OTLP to a local collector, current behavior is correct.

### Recommendation 4: Document `OTEL_LOG_USER_PROMPTS=1` Policy

Since we have prompt content logging enabled, this should be documented as a known intentional policy choice (personal development only), with a note that this variable MUST NOT be deployed to shared/team settings without privacy review.

### Recommendation 5: No Prometheus Scrape Endpoint Configuration Needed

The docs show `prometheus` as a valid `OTEL_METRICS_EXPORTER` value. When set, Claude Code will expose a Prometheus scrape endpoint (standard OTEL Prometheus exporter behavior — typically on port 9464). We are using `otlp` with gRPC push, so this is not relevant. Our current approach (push via OTLP to collector) is the documented production pattern.

### Final Recommended settings.json env Block

After applying all three planned changes and cleaning up redundancies:

```json
"env": {
  "ENABLE_LSP_TOOL": "1",
  "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
  "OTEL_METRICS_EXPORTER": "otlp",
  "OTEL_LOGS_EXPORTER": "otlp",
  "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
  "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
  "OTEL_LOG_USER_PROMPTS": "1",
  "OTEL_LOG_TOOL_DETAILS": "1",
  "OTEL_METRICS_INCLUDE_SESSION_ID": "true",
  "OTEL_METRICS_INCLUDE_VERSION": "true",
  "OTEL_RESOURCE_ATTRIBUTES": "service.name=mde-claude-code"
}
```

Changes from current:
- REMOVED: `OTEL_SERVICE_NAME` (not a documented Claude Code var)
- REMOVED: `OTEL_METRIC_EXPORT_INTERVAL` (restore 60s production default)
- REMOVED: `OTEL_LOGS_EXPORT_INTERVAL` (redundant — matches 5000ms default)
- ADDED: `OTEL_LOG_TOOL_DETAILS=1` (planned addition)
- ADDED: `OTEL_RESOURCE_ATTRIBUTES=service.name=mde-claude-code` (replaces OTEL_SERVICE_NAME)

---

## Summary Table: Issue Classification

| Issue | Severity | Action |
|---|---|---|
| `OTEL_SERVICE_NAME` not documented | MEDIUM | Remove, replace with `OTEL_RESOURCE_ATTRIBUTES` (planned) |
| `OTEL_METRIC_EXPORT_INTERVAL=10000` for production | LOW | Remove to use 60s default (planned) |
| `OTEL_LOGS_EXPORT_INTERVAL=5000` is redundant | LOW | Remove (optional cleanup) |
| Reference doc heading "Events / Traces" misleading | LOW | Update heading to "Events (via OTel Logs API)" |
| `OTEL_LOG_USER_PROMPTS=1` privacy policy undocumented | MEDIUM | Add comment/note in settings or CLAUDE.md |
| `OTEL_LOG_TOOL_DETAILS` not yet added | LOW | Add (planned) |
| No traces exporter — reference doc should clarify | LOW | Update reference doc heading |

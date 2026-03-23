# Claude Code OTEL Resource Attributes Deep Review

**Date:** 2026-03-22
**Analyst:** coder-agent (source code analysis)
**Sources:**
- Claude Code v2.1.81 bundled source (`cli.js`, decompiled)
- OpenTelemetry JS SDK source (github.com/open-telemetry/opentelemetry-js)
- Official docs: https://code.claude.com/docs/en/monitoring-usage
- Prior deep review: `claude-code-monitoring-reference.md` (2026-03-22)
- Prior deep review: `claude-code-monitoring-validation.md` (2026-03-22)

---

## 1. Core Question: Can OTEL_SERVICE_NAME or OTEL_RESOURCE_ATTRIBUTES Override service.name?

**Answer: YES. Both env vars will override the hardcoded `service.name=claude-code`.**

### Evidence: Claude Code Source (v2.1.81 cli.js)

The resource creation chain in Claude Code's OTEL setup (decompiled from minified bundle):

```javascript
// Step 1: Hardcoded attributes
_ = {
  [ATTR_SERVICE_NAME]: "claude-code",
  [ATTR_SERVICE_VERSION]: "2.1.81"
};
if (platform === "wsl") _["wsl.version"] = getWslVersion();

// Step 2: Create individual resource objects
Y = resourceFromAttributes(_);                    // hardcoded service info
z = resourceFromAttributes(osDetector.detect());   // os.type, os.version
$ = resourceFromAttributes({host.arch: ...});      // host.arch
H = resourceFromAttributes(envDetector.detect());  // OTEL_RESOURCE_ATTRIBUTES + OTEL_SERVICE_NAME

// Step 3: Merge chain (LAST merge wins)
j = Y.merge(z).merge($).merge(H);
```

### Evidence: OTEL JS SDK Resource.merge() Behavior

From `opentelemetry-js/packages/opentelemetry-resources/src/ResourceImpl.ts`:

```typescript
public merge(resource: Resource | null): Resource {
  // Order is important
  // Spec states incoming attributes override existing attributes
  return ResourceImpl.FromAttributeList(
    [...resource.getRawAttributes(), ...this.getRawAttributes()],
    mergedOptions
  );
}
```

The `attributes` getter resolves duplicates with first-write-wins:

```typescript
public get attributes(): Attributes {
  const attrs: Attributes = {};
  for (const [k, v] of this._rawAttributes) {
    if (v != null) {
      attrs[k] ??= v;  // FIRST occurrence wins
    }
  }
}
```

Since `merge()` puts the OTHER resource's attributes FIRST in the array, the OTHER resource wins conflicts. In the chain `Y.merge(z).merge($).merge(H)`, `H` (env vars) is merged LAST, so its attributes are placed first in the final array and WIN over all previous values.

### Evidence: envDetector Implementation

From Claude Code's bundled OTEL SDK (class `gSA`):

```javascript
detect() {
  let attrs = {};
  let resourceAttrs = getStringFromEnv("OTEL_RESOURCE_ATTRIBUTES");
  let serviceName = getStringFromEnv("OTEL_SERVICE_NAME");

  if (resourceAttrs) {
    Object.assign(attrs, this._parseResourceAttributes(resourceAttrs));
  }
  if (serviceName) {
    attrs[ATTR_SERVICE_NAME] = serviceName;  // Overwrites OTEL_RESOURCE_ATTRIBUTES
  }
  return { attributes: attrs };
}
```

**Priority within envDetector:** `OTEL_SERVICE_NAME` > `OTEL_RESOURCE_ATTRIBUTES` (for service.name key).

**Priority in merge chain:** env vars > host detection > OS detection > hardcoded values.

---

## 2. Official Documentation on Resource Attributes

From `claude-code-monitoring-reference.md` (extracted from official docs page):

### Resource Attributes (Service Information)

> All metrics and events include these resource attributes:
>
> | Attribute | Description | Example |
> |-----------|-------------|---------|
> | `service.name` | Service identifier | "claude-code" |
> | `service.version` | Current Claude Code version | "1.0.0" |
> | `os.type` | Operating system | "darwin", "linux", "windows" |
> | `os.version` | OS version string | "14.3" |
> | `host.arch` | Host architecture | "amd64", "arm64" |
> | `wsl.version` | WSL version (Windows only) | Only present when running on WSL |
>
> **Meter Name:** `com.anthropic.claude_code`

### OTEL_RESOURCE_ATTRIBUTES (Official Docs)

> | Variable | Description | Default | Valid Values | Notes |
> |----------|-------------|---------|--------------|-------|
> | `OTEL_RESOURCE_ATTRIBUTES` | Custom attributes for team/dept/org segmentation | unset | Comma-separated `key=value` pairs | Format: `department=eng,team.id=platform,cost_center=123` |
>
> #### Formatting Requirements
> - **No spaces allowed** in values
> - **Format:** Comma-separated key=value pairs: `key1=value1,key2=value2`
> - **Allowed characters:** US-ASCII excluding control chars, whitespace, quotes, commas, semicolons, backslashes
> - **Special characters:** Percent-encode if needed

**CRITICAL NOTE:** The official docs list `OTEL_RESOURCE_ATTRIBUTES` but do NOT list `OTEL_SERVICE_NAME`. The docs describe `OTEL_RESOURCE_ATTRIBUTES` for "team/dept/org segmentation", suggesting custom attributes alongside (not replacing) the built-in ones.

---

## 3. Answers to the Specific Questions

### Q1: Should we set `OTEL_RESOURCE_ATTRIBUTES=service.name=mde-claude-code`?

**No.** While it would technically work (env wins over hardcoded), overriding `service.name` is not the documented use case. The docs describe this variable for team/department segmentation. Overriding `service.name` could:
- Confuse Grafana dashboards built for `service.name=claude-code`
- Break any upstream filtering that expects the standard service name
- Create confusion if Anthropic changes the merge behavior in a future version

### Q2: Should we keep `OTEL_SERVICE_NAME=mde-claude-code`?

**No.** `OTEL_SERVICE_NAME` is not documented by Claude Code at all. It works only because the OTEL JS SDK's envDetector reads it. This is an implementation detail, not a supported feature. Remove it.

### Q3: Should we just use Claude Code's default `service.name=claude-code`?

**Yes.** Use the hardcoded default. If you need to distinguish this project's telemetry, use custom resource attributes instead:
```
OTEL_RESOURCE_ATTRIBUTES=project=mde,environment=dev
```

### Q4: Can we add CUSTOM resource attributes without conflicting?

**Yes, absolutely.** This is the documented and intended use case. The envDetector merges custom attributes alongside the built-in ones. Only overlapping keys would conflict. Safe custom attributes:
- `project=mde`
- `environment=dev`
- `team.name=personal`
- `deployment.id=local`

These will NOT conflict with any built-in attribute (`service.name`, `service.version`, `os.type`, `os.version`, `host.arch`).

---

## 4. Complete Settings Validation

### Current settings.json env block:

| Variable | Current Value | Status | Action |
|----------|---------------|--------|--------|
| `ENABLE_LSP_TOOL` | `"1"` | OK | Not telemetry-related; keep |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `"1"` | CORRECT | Required to enable any telemetry |
| `OTEL_METRICS_EXPORTER` | `"otlp"` | CORRECT | Documented, valid value |
| `OTEL_LOGS_EXPORTER` | `"otlp"` | CORRECT | Documented, valid value |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `"grpc"` | CORRECT | Documented, valid value |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `"http://localhost:4317"` | CORRECT | Documented default for gRPC |
| `OTEL_METRIC_EXPORT_INTERVAL` | `"10000"` | REMOVE | 10s is debug-only; use default 60000ms for production |
| `OTEL_LOGS_EXPORT_INTERVAL` | `"5000"` | REDUNDANT | Matches default; can keep for explicitness or remove |
| `OTEL_LOG_USER_PROMPTS` | `"1"` | INTENTIONAL | Privacy decision - enables prompt content in events |
| `OTEL_METRICS_INCLUDE_SESSION_ID` | `"true"` | REDUNDANT | Matches default; can keep for explicitness or remove |
| `OTEL_METRICS_INCLUDE_VERSION` | `"true"` | INTENTIONAL | Non-default; enables version tracking in metrics |
| `OTEL_SERVICE_NAME` | `"mde-claude-code"` | REMOVE | Undocumented; overrides hardcoded value |

### Recommended Final settings.json env block:

```json
{
  "env": {
    "ENABLE_LSP_TOOL": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_LOGS_EXPORT_INTERVAL": "5000",
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1",
    "OTEL_METRICS_INCLUDE_SESSION_ID": "true",
    "OTEL_METRICS_INCLUDE_VERSION": "true",
    "OTEL_RESOURCE_ATTRIBUTES": "project=mde,environment=dev"
  }
}
```

### Changes from current:

| Change | Reason |
|--------|--------|
| REMOVE `OTEL_SERVICE_NAME` | Undocumented; overrides hardcoded `service.name=claude-code` |
| REMOVE `OTEL_METRIC_EXPORT_INTERVAL` | Was 10000ms (debug interval); use default 60000ms |
| ADD `OTEL_LOG_TOOL_DETAILS=1` | Documented; enables MCP server/tool names and skill names in events |
| ADD `OTEL_RESOURCE_ATTRIBUTES=project=mde,environment=dev` | Documented; adds custom attributes without overriding built-in ones |

---

## 5. OTEL JS SDK Merge Priority Reference

For future reference, the complete priority chain (highest to lowest):

1. `OTEL_SERVICE_NAME` env var (within envDetector, overwrites any `service.name` from `OTEL_RESOURCE_ATTRIBUTES`)
2. `OTEL_RESOURCE_ATTRIBUTES` env var (parsed key=value pairs)
3. `host.arch` from hostDetector
4. `os.type`, `os.version` from osDetector
5. Hardcoded: `service.name=claude-code`, `service.version=X.Y.Z`

This is because of the `Y.merge(z).merge($).merge(H)` chain where `merge()` gives priority to the "other" resource (the argument), and `H` (env) is merged last.

---

## 6. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Custom `service.name` breaks dashboards | LOW | Removed; using default |
| `OTEL_RESOURCE_ATTRIBUTES` format error | LOW | Use only ASCII, no spaces, comma-separated |
| Future Claude Code version changes merge order | LOW | We only add safe custom attributes, not override built-ins |
| `OTEL_LOG_USER_PROMPTS=1` privacy exposure | MEDIUM | Intentional for local dev; disable in shared/production environments |
| `OTEL_LOG_TOOL_DETAILS=1` reveals config | LOW | Intentional for local dev observability |

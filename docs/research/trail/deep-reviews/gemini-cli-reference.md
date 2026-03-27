# Gemini CLI Reference: Configuration, Commands, and Settings

**Status**: Complete research from official documentation
**Fetched**: 2026-03-27
**Source**: https://geminicli.com (6 documentation pages)

## Quick Summary

Gemini CLI is Google's official interactive REPL for the Gemini API, supporting:
- Interactive and non-interactive modes
- Rich configuration system (7-layer precedence: defaults → system → user → project → env → CLI flags)
- 40+ settings covering UI, approval modes, telemetry, and tool behavior
- 25+ slash commands for session control and customization
- OpenTelemetry integration for observability
- Custom project-level and global commands

## Configuration Layer Precedence

Configuration is applied in this order (highest priority last):

1. **Default values** — Hardcoded application defaults
2. **System defaults file** — `/etc/gemini-cli/system-defaults.json` (Linux/macOS) or `C:\ProgramData\gemini-cli\system-defaults.json` (Windows)
   - Override via env var: `GEMINI_CLI_SYSTEM_DEFAULTS_PATH`
3. **User settings file** — `~/.gemini/settings.json`
4. **Project settings file** — `.gemini/settings.json` (in project root)
5. **System settings file** — `/etc/gemini-cli/settings.json` (Linux/macOS) or `C:\ProgramData\gemini-cli\settings.json` (Windows)
   - Override via env var: `GEMINI_CLI_SYSTEM_SETTINGS_PATH`
6. **Environment variables** — System or session-specific (loaded from `.env` files)
7. **Command-line arguments** — Values passed at launch (highest priority)

### Environment Variable Syntax in Settings

String values in `settings.json` and `gemini-extension.json` can reference environment variables:
- `$VAR_NAME` or `${VAR_NAME}` syntax
- Automatically resolved when settings are loaded
- Example: `"apiKey": "$MY_API_TOKEN"`

Each extension can have its own `.env` file that loads automatically.

## Settings Schema Reference

### General Settings (`general.*`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `general.preferredEditor` | string | undefined | Preferred editor to open files in |
| `general.vimMode` | boolean | false | Enable Vim keybindings |
| `general.defaultApprovalMode` | enum | "default" | Tool execution approval mode; values: `"default"` (prompt), `"auto_edit"` (auto-approve edits), `"plan"` (read-only). **NOTE**: YOLO mode (auto-approve all) is CLI-only (`--yolo` or `--approval-mode=yolo`), never in settings.json |
| `general.devtools` | boolean | false | Enable DevTools inspector on launch |
| `general.enableAutoUpdate` | boolean | true | Enable automatic updates |
| `general.enableAutoUpdateNotification` | boolean | true | Enable update notification prompts |
| `general.enableNotifications` | boolean | false | Enable run-event notifications for action-required and completion |
| `general.checkpointing.enabled` | boolean | false | Enable session checkpointing for recovery (requires restart) |
| `general.plan.directory` | string | undefined | Directory for planning artifacts (defaults to system temp). Custom dir requires policy for write access in Plan Mode (requires restart) |
| `general.plan.modelRouting` | boolean | true | Auto-switch between Pro (planning) and Flash (implementation) models |
| `general.retryFetchErrors` | boolean | true | Retry on "exception TypeError: fetch failed" errors |
| `general.maxAttempts` | number | 10 | Max attempts for chat model requests (cannot exceed 10) |
| `general.debugKeystrokeLogging` | boolean | false | Enable keystroke debug logging to console |
| `general.sessionRetention.enabled` | boolean | true | Enable automatic session cleanup |
| `general.sessionRetention.maxAge` | string | "30d" | Auto-delete chats older than period (e.g., "30d", "7d", "24h", "1w") |
| `general.sessionRetention.maxCount` | number | undefined | Alternative: max sessions to keep (most recent) |
| `general.sessionRetention.minRetention` | string | "1d" | Minimum retention period (safety limit) |

### Output Settings (`output.*`)

| Setting | Type | Default | Values | Description |
|---------|------|---------|--------|-------------|
| `output.format` | enum | "text" | "text", "json" | CLI output format |

### UI Settings (`ui.*`)

**Theme & Display:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.theme` | string | undefined | Color theme (see themes guide for options) |
| `ui.autoThemeSwitching` | boolean | true | Auto-switch light/dark based on terminal background |
| `ui.terminalBackgroundPollingInterval` | number | 60 | Polling interval (seconds) for terminal background color |
| `ui.customThemes` | object | {} | Custom theme definitions |

**Window & Title:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.hideWindowTitle` | boolean | false | Hide window title bar (requires restart) |
| `ui.dynamicWindowTitle` | boolean | true | Update terminal title with status icons (Ready: ◇, Action Required: ✋, Working: ✦) |
| `ui.showStatusInTitle` | boolean | false | Show model thinking in terminal window title during work phase |

**Output Rendering:**

| Setting | Type | Default | Values | Description |
|---------|------|---------|--------|-------------|
| `ui.inlineThinkingMode` | enum | "off" | "off", "full" | Display model thinking inline |
| `ui.showLineNumbers` | boolean | true | Show line numbers in chat |
| `ui.showCitations` | boolean | false | Show citations for generated text |
| `ui.showModelInfoInChat` | boolean | false | Show model name in chat for each turn |
| `ui.incrementalRendering` | boolean | true | Enable incremental rendering (reduces flicker, may cause artifacts). Only when `useAlternateBuffer: true` |
| `ui.showSpinner` | boolean | true | Show spinner during operations |
| `ui.loadingPhrases` | enum | "tips" | "tips", "witty", "both", "nothing" | What to show while model works |
| `ui.useAlternateBuffer` | boolean | false | Use alternate screen buffer, preserving shell history |
| `ui.useBackgroundColor` | boolean | true | Use background colors in UI |

**Content & Warnings:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.showHomeDirectoryWarning` | boolean | true | Warn when running from home directory (requires restart) |
| `ui.showCompatibilityWarnings` | boolean | true | Show terminal/OS compatibility warnings (requires restart) |
| `ui.hideTips` | boolean | false | Hide helpful tips in UI |
| `ui.escapePastedAtSymbols` | boolean | false | Escape @ symbols in pasted text to prevent unintended @path expansion |
| `ui.showShortcutsHint` | boolean | true | Show "? for shortcuts" hint above input |
| `ui.hideBanner` | boolean | false | Hide application banner |
| `ui.hideContextSummary` | boolean | false | Hide context summary (GEMINI.md, MCP servers) above input |
| `ui.hideFooter` | boolean | false | Hide footer from UI |
| `ui.collapseDrawerDuringApproval` | boolean | true | Collapse drawer when tool awaits confirmation |

**Footer:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.footer.items` | array | undefined | List of item IDs to display in footer (rendered in order) |
| `ui.footer.showLabels` | boolean | true | Display second line with descriptive headers (e.g., `/model`) |
| `ui.footer.hideCWD` | boolean | false | Hide current working directory |
| `ui.footer.hideSandboxStatus` | boolean | false | Hide sandbox status indicator |
| `ui.footer.hideModelInfo` | boolean | false | Hide model name and context usage |
| `ui.footer.hideContextPercentage` | boolean | true | Hide context window usage percentage |

**Diagnostics:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.showMemoryUsage` | boolean | false | Display memory usage in UI |
| `ui.showUserIdentity` | boolean | true | Show signed-in user's identity (email) in UI |
| `ui.errorVerbosity` | enum | "low" | "low", "full" | "low" hides recoverable errors, "full" shows all |
| `ui.accessibility.screenReader` | boolean | false | Render output in plain-text for screen reader accessibility |

### IDE Settings (`ide.*`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ide.enabled` | boolean | false | Enable IDE integration mode |

### Billing Settings (`billing.*`)

| Setting | Type | Default | Values | Description |
|---------|------|---------|--------|-------------|
| `billing.overageStrategy` | enum | "ask" | "ask", "always", "never" | Handle quota exhaustion when AI credits available: "ask" = prompt, "always" = auto-use credits, "never" = disable |

### Model Settings (`model.*`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `model.name` | string | undefined | Gemini model to use for conversations |
| `model.maxSessionTurns` | number | -1 | Max user/model/tool turns to keep (-1 = unlimited) |
| `model.compressionThreshold` | number | 0.5 | Fraction of context to trigger compression (e.g., 0.2, 0.3, 0.5) |
| `model.disableLoopDetection` | boolean | false | Disable automatic infinite loop detection |
| `model.skipNextSpeakerCheck` | boolean | true | Skip next speaker check |

### Agents Settings (`agents.*`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `agents.browser.confirmSensitiveActions` | boolean | false | Require manual confirmation for sensitive browser actions (fill_form, evaluate_script) |
| `agents.browser.blockFileUploads` | boolean | false | Hard-block file upload requests from browser agent |

### Context Settings (`context.*`)

**Discovery & File Filtering:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `context.discoveryMaxDirs` | number | 200 | Maximum directories to search for memory |
| `context.loadMemoryFromIncludeDirectories` | boolean | false | When true, scan include dirs for GEMINI.md; when false, use only current dir |
| `context.fileFiltering.respectGitIgnore` | boolean | true | Respect .gitignore files when searching |
| `context.fileFiltering.respectGeminiIgnore` | boolean | true | Respect .geminiignore files when searching |
| `context.fileFiltering.enableRecursiveFileSearch` | boolean | true | Enable recursive file search for @ references |
| `context.fileFiltering.enableFuzzySearch` | boolean | true | Enable fuzzy search for files |
| `context.fileFiltering.customIgnoreFilePaths` | array | [] | Additional ignore file paths to respect (files earlier take precedence) |

### Tools Settings (`tools.*`)

**Sandbox:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tools.sandboxAllowedPaths` | array | [] | Additional paths sandbox can access |
| `tools.sandboxNetworkAccess` | boolean | false | Allow sandbox to access network |

**Shell:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tools.shell.enableInteractiveShell` | boolean | true | Use node-pty for interactive shell. Falls back to child_process if unavailable |
| `tools.shell.showColor` | boolean | false | Show color in shell output |

**Search & Output:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tools.useRipgrep` | boolean | true | Use ripgrep for file content search (faster than fallback) |
| `tools.truncateToolOutputThreshold` | number | 40000 | Max characters for large tool output truncation (0 or negative = disabled) |
| `tools.disableLLMCorrection` | boolean | true | Disable LLM-based error correction for edit tools. When enabled, fail immediately if exact string match not found |

### Top-Level Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `policyPaths` | array | [] | Additional policy files/directories to load (requires restart) |
| `adminPolicyPaths` | array | [] | Additional admin policy files/directories to load (requires restart) |

## Approval Modes

Gemini CLI has three approval modes for tool execution:

1. **`default`** (settings only)
   - Prompts user for approval before executing each tool
   - Safe for interactive use
   - Prevents accidental changes

2. **`auto_edit`** (settings only)
   - Auto-approves edit tools (file creation, modification, deletion)
   - Still prompts for other tool actions
   - Speeds up coding tasks

3. **`plan`** (settings only)
   - Read-only mode
   - No tool execution
   - Displays what would happen without doing it

4. **`yolo`** (CLI-only, never in settings.json)
   - Auto-approves ALL actions
   - Enable with `--yolo` or `--approval-mode=yolo` flag only
   - Cannot be set in settings file for security reasons

### Valid settings.json Approval Values

Only these 3 values are valid in `settings.json`:
```json
{
  "general": {
    "defaultApprovalMode": "default"     // or "auto_edit" or "plan"
  }
}
```

**YOLO mode cannot be set in settings.json** — enforce via CLI flag only.

## Headless/Non-Interactive Mode Configuration

Gemini CLI supports non-interactive usage through several mechanisms:

### Command-Line Flags

```bash
# Non-interactive single query
gemini -p "your query"

# Query with continuation to interactive mode
gemini "your query"

# Interactive with initial query
gemini -i "your query"

# Pipe input
cat file | gemini
```

### Output Format Configuration

For scripting and automation:
```json
{
  "output": {
    "format": "json"    // or "text" (default)
  }
}
```

When `output.format` is `"json"`, Gemini CLI returns structured JSON output suitable for parsing.

### Key Settings for Headless Mode

- `output.format: "json"` — Machine-readable output
- `general.enableNotifications: false` — Suppress user notifications
- `ui.hideBanner: true` — No ASCII art headers
- `ui.hideContextSummary: true` — No context display
- `ui.hideFooter: true` — No footer
- `general.defaultApprovalMode: "auto_edit"` — Pre-approve non-destructive actions
- `model.maxAttempts: 3` — Cap retries in automated contexts

### No Interactive REPL in Non-Interactive Mode

When running with `-p` flag or piped input, Gemini CLI exits after processing the query. To capture output for scripts:

```bash
# Capture to variable (requires JSON format)
response=$(gemini -p "query" 2>/dev/null)
result=$(echo "$response" | jq '.response')

# Or with output files (using telemetry or custom export)
gemini -p "query" > output.json
```

## Telemetry Configuration

Gemini CLI uses OpenTelemetry for observability, supporting:

### Settings Location

Configure in `.gemini/settings.json` under `telemetry.*` object:

```json
{
  "telemetry": {
    "enabled": false,
    "target": "local",
    "otlpEndpoint": "http://localhost:4317",
    "otlpProtocol": "grpc",
    "logPrompts": true,
    "useCollector": false,
    "useCliAuth": false
  }
}
```

### Telemetry Settings Schema

| Setting | Env Var | Type | Default | Values | Description |
|---------|---------|------|---------|--------|-------------|
| `telemetry.enabled` | `GEMINI_TELEMETRY_ENABLED` | boolean | false | true/false | Enable/disable telemetry |
| `telemetry.target` | `GEMINI_TELEMETRY_TARGET` | enum | "local" | "gcp", "local" | Where to send telemetry data |
| `telemetry.otlpEndpoint` | `GEMINI_TELEMETRY_OTLP_ENDPOINT` | string | http://localhost:4317 | URL | OTLP collector endpoint |
| `telemetry.otlpProtocol` | `GEMINI_TELEMETRY_OTLP_PROTOCOL` | enum | "grpc" | "grpc", "http" | OTLP transport protocol |
| `telemetry.outfile` | `GEMINI_TELEMETRY_OUTFILE` | string | - | file path | Save telemetry to file (overrides otlpEndpoint) |
| `telemetry.logPrompts` | `GEMINI_TELEMETRY_LOG_PROMPTS` | boolean | true | true/false | Include prompts in telemetry logs |
| `telemetry.useCollector` | `GEMINI_TELEMETRY_USE_COLLECTOR` | boolean | false | true/false | Use external OTLP collector (advanced) |
| `telemetry.useCliAuth` | `GEMINI_TELEMETRY_USE_CLI_AUTH` | boolean | false | true/false | Use CLI credentials for GCP telemetry (GCP target only) |
| (env only) | `GEMINI_CLI_SURFACE` | string | - | string | Custom label for traffic reporting |

### Boolean Environment Variables

For boolean settings like `enabled`, set env var to `true` or `1` to enable.

### Google Cloud Telemetry

Prerequisites:
1. Set Google Cloud project: `OTLP_GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_PROJECT`
2. Authenticate: ADC (Application Default Credentials) or service account key
3. Required IAM roles: Cloud Trace Agent, Monitoring Metric Writer, Logs Writer
4. Enable APIs: `cloudtrace.googleapis.com`, `monitoring.googleapis.com`, `logging.googleapis.com`

Two export methods:
- **Direct export** (recommended): In-process exporters, supports `useCliAuth`
- **Collector-based**: External OTLP collector, requires `useCollector: true`

### Local Telemetry

For development, save to file:
```json
{
  "telemetry": {
    "enabled": true,
    "target": "local",
    "outfile": "/tmp/gemini-telemetry.json"
  }
}
```

## Slash Commands Reference

Gemini CLI supports 25+ slash commands prefixed with `/`, `@`, or `!`:

### Session & UI Control

| Command | Description |
|---------|-------------|
| `/about` | Show version info (share when filing issues) |
| `/clear` | Clear chat history |
| `/help` | Show help message |
| `/settings` | Open settings dialog |
| `/exit` | Exit Gemini CLI |

### Context Management

| Command | Description |
|---------|-------------|
| `/context` | View current context |
| `/context-size` | Show context window usage |
| `/memory` | Manage memory/context |
| `/memory reload` | Reload GEMINI.md from disk |

### Tool & Model Configuration

| Command | Description |
|---------|-------------|
| `/model` | View/set current model |
| `/tools` | List available tools |
| `/agents` | View/manage agents |

### Approval & Safety

| Command | Description |
|---------|-------------|
| `/approve` | Approve pending tool execution |
| `/deny` | Reject pending tool execution |

### Advanced Features

| Command | Description |
|---------|-------------|
| `/custom` | Show custom commands (project and user) |
| `/plugins` | List loaded plugins/extensions |
| `/telemetry` | View telemetry status |

Full command documentation available at https://geminicli.com/docs/reference/commands/

## Custom Commands

Custom commands let you save frequently used prompts as shortcuts.

### File Locations & Precedence

1. **User commands (global)**: `~/.gemini/commands/`
   - Available in all projects
2. **Project commands (local)**: `.gemini/commands/`
   - Specific to current project
   - Can be checked into version control

**Project commands override user commands** with the same name.

### Creating Custom Commands

Create `.gemini/commands/mycmd.md`:
```markdown
---
name: mycmd
description: My custom command description
---

Your prompt or template here.
```

Access with:
```
/mycmd
```

## Known Issues & Gotchas

### 1. YOLO Mode Cannot Be Persisted

**Issue**: Attempting to set `"yolo"` in `settings.json` has no effect.

**Why**: YOLO mode (auto-approve all actions) is intentionally CLI-only for security.

**Solution**: Use `--yolo` or `--approval-mode=yolo` flag at launch instead.

### 2. Environment Variables in Settings

**Behavior**: Variables like `$API_KEY` in settings are automatically resolved.

**Gotcha**: If you need a literal `$` in a setting value, use double-dollar: `$$LITERAL_DOLLAR`

### 3. Plan Mode Directory Requires Policy

**Issue**: Custom `general.plan.directory` with no write policy causes failures.

**Solution**: When setting a custom plan directory, ensure your security policy allows write access in Plan Mode.

### 4. Model Routing Not Applicable to Subscription Plans

**Issue**: `general.plan.modelRouting` auto-switches Pro/Flash models.

**Note**: Subscription-only feature; doesn't apply if using quota/pay-per-use billing.

### 5. Sandbox Network Access is Global

**Issue**: `tools.sandboxNetworkAccess: true` enables network for all tool commands.

**Gotcha**: No per-command granularity; either all tools have network or none do.

### 6. Context Compression is Lossy

**Issue**: Setting `model.compressionThreshold` low triggers compression frequently.

**Impact**: Model has less context; may miss earlier conversation details.

**Recommendation**: Keep at default 0.5 unless memory is critical.

### 7. LLM Correction Disabled by Default

**Issue**: `tools.disableLLMCorrection: true` (default) means edits must match exactly.

**Gotcha**: Whitespace differences, formatting, or minor line changes cause edit failures.

**Workaround**: Increase `tools.truncateToolOutputThreshold` to see more context.

### 8. useCollector and useCliAuth are Mutually Exclusive

**Issue**: Setting both `useCollector: true` and `useCliAuth: true` disables telemetry.

**Why**: Direct export (useCliAuth) and collector-based export are incompatible.

**Solution**: Choose one: direct export for simplicity, collector for advanced setups.

## Validation & Best Practices

### Settings File Validation

After editing `.gemini/settings.json`, validate by:
1. Running `/settings` command in Gemini CLI
2. Checking for error messages in `gemini.log` (if available)
3. Testing a simple command to confirm settings apply

### Approval Mode Recommendations

- **Interactive development**: `"default"` — safe, prompts for each action
- **Trusted automation**: `"auto_edit"` — speeds up coding
- **Read-only exploration**: `"plan"` — plan mode for safe browsing
- **Full automation** (if needed): Use `--yolo` flag, not settings

### Telemetry Best Practices

- **Local development**: Use `target: "local"` with `outfile` for debugging
- **Production**: Use `target: "gcp"` with proper authentication
- **Privacy**: Set `logPrompts: false` if handling sensitive data
- **Performance**: Disable telemetry (`enabled: false`) if not needed — adds overhead

### Context Management

- Keep `context.discoveryMaxDirs: 200` unless you have extreme file counts
- Enable `context.fileFiltering.respectGitIgnore: true` to exclude build artifacts
- Use `context.loadMemoryFromIncludeDirectories: false` for isolated project context

### Tool Behavior

- Keep `tools.disableLLMCorrection: true` for deterministic edit behavior
- Increase `tools.truncateToolOutputThreshold` if debugging edit failures
- Monitor `tools.sandboxNetworkAccess` — enable only if tools need it

## Summary Table: All Top-Level Categories

| Category | Purpose | Key Settings |
|----------|---------|--------------|
| `general.*` | Session behavior, updates, limits | vimMode, defaultApprovalMode, maxAttempts, sessionRetention |
| `output.*` | Output formatting | format (text/json) |
| `ui.*` | User interface (theme, display, footer, accessibility) | theme, inlineThinkingMode, hideFooter, colorMode |
| `ide.*` | IDE integration | enabled |
| `billing.*` | Credit & quota handling | overageStrategy |
| `model.*` | Model selection & behavior | name, maxSessionTurns, compressionThreshold |
| `agents.*` | Agent-specific rules | browser (confirmSensitiveActions, blockFileUploads) |
| `context.*` | Memory & file discovery | discoveryMaxDirs, respectGitIgnore, enableFuzzySearch |
| `tools.*` | Tool execution (sandbox, shell, search) | sandboxNetworkAccess, useRipgrep, disableLLMCorrection |
| `telemetry.*` | OpenTelemetry observability | enabled, target, otlpEndpoint, logPrompts |
| Top-level | Policy & extensions | policyPaths, adminPolicyPaths |

## URLs & Source Catalog

- [CLI commands reference](https://geminicli.com/docs/reference/commands/) — Slash commands, built-in commands
- [Configuration reference](https://geminicli.com/docs/reference/configuration/) — Full settings schema with 40+ keys
- [CLI cheatsheet](https://geminicli.com/docs/cli/cli-reference/) — Quick command reference
- [Telemetry (OpenTelemetry)](https://geminicli.com/docs/cli/telemetry/) — Observability configuration
- [Custom commands](https://geminicli.com/docs/cli/custom-commands/) — User & project command definition
- [Settings command](https://geminicli.com/docs/cli/settings/) — Interactive settings UI and schema


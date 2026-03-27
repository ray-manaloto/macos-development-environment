# Gemini CLI Community Findings: Settings, Approval Modes, and Headless Integration

**Last Updated:** 2026-03-27
**Status:** Research Complete
**Confidence:** Confirmed (evidence from official docs, GitHub issues, and community discussions)

---

## Executive Summary

Community research on Gemini CLI reveals critical insights for autonomous review pipelines using gemini-cli as a non-interactive subprocess. The key finding is a **fundamental conflict in the approval system**: hardcoded tool exclusions in headless mode cannot be overridden by the Policy Engine, even with high-priority allow rules. This affects agent framework integration at the infrastructure level.

---

## 1. Configuration Architecture

### 1.1 Settings Precedence (Highest → Lowest)
Gemini CLI applies configuration in this strict order:

1. **Command-line Arguments** (e.g., `--yolo`, `--policy`, `-p`)
2. **Environment Variables** (e.g., `GEMINI_API_KEY`, `GEMINI_MODEL`)
3. **System Settings File** `/etc/gemini-cli/settings.json` (org-wide override)
4. **Project Settings** `.gemini/settings.json` (directory-specific)
5. **User Settings** `~/.gemini/settings.json` (personal defaults)
6. **Hardcoded Defaults**

**Implication for autonomous pipelines:** Command-line flags like `--yolo` override all settings.json configuration. This is both a feature (scripting flexibility) and a liability (inconsistent behavior if scripts don't use flags).

### 1.2 Environment Variable Locations (.env Files)

The CLI searches for `.env` files in this order:
1. `.env` in current working directory
2. Parent directories upward until `.git` found or home reached
3. `~/.env` (home directory)

**Key variables for automation:**
- `GEMINI_API_KEY` — LLM API authentication
- `GEMINI_MODEL` — Default model selection
- `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` — Vertex AI backends
- `GOOGLE_APPLICATION_CREDENTIALS` — GCP service account authentication

**Community practice:** Storing sensitive keys in `.env` files, but note that project `.gemini/settings.json` is often checked into version control and can reference environment variables via `${VAR_NAME}` syntax.

---

## 2. Approval Modes and Tool Access Control

### 2.1 Yolo Mode (`--yolo` flag)

**What it does:** Auto-approves all tool calls without interactive prompts.

**Activation methods:**
- Command-line: `gemini --yolo -p "prompt"`
- Settings: `"yolo": true` in `settings.json`
- Keyboard: `Ctrl+Y` toggle in interactive mode

**Community findings:**
- **Most commonly used for automation**, but Reddit discussions reveal confusion about why it still requests permissions in some scenarios (e.g., folder trust, MCP server confirmations)
- One Reddit user reported trying to set `yolo: true` in `~/.gemini/settings.json` but CLI still paused for approval — likely due to initialization-order issues or missing folder trust configuration
- Maestro (multi-agent orchestration framework) deliberately runs subagents in `--yolo` mode since agents cannot provide interactive approval

**Limitation:** `--yolo` does NOT bypass **folder trust dialogs** or **project-level security policies**. Users must explicitly trust the folder via:
```bash
gemini --trust-folder .  # Mark current directory as trusted
```

### 2.2 Auto-Edit Approval Mode (`--approval-mode auto_edit`)

**What it does:** Automatically approves tool calls that modify files without showing diffs.

**Configuration in settings.json:**
```json
{
  "approval": {
    "mode": "auto_edit"
  }
}
```

**Community issue #20469 (2026-02-26):** Users report that `auto_edit` mode in non-interactive context (`-p` flag) **ignores Policy Engine allow rules**. The CLI has a hardcoded "extra exclude" list for `run_shell_command` that is applied BEFORE the Policy Engine is consulted. Even if a policy rule explicitly allows a tool with high priority, the tool never makes it into the ToolRegistry, resulting in "Tool not found" errors.

**Root cause analysis (confirmed in GitHub issue):**
```typescript
// Simplified flow showing the bug
getExcludeTools(): Set<string> {
  const excludeToolsSet = new Set([...this.excludeTools]); // Hardcoded excludes

  // Policy Engine can only ADD to this set, never remove
  const policyExclusions = this.policyEngine.getExcludedTools(...);
  for (const tool of policyExclusions) {
    excludeToolsSet.add(tool);
  }

  return excludeToolsSet; // run_shell_command stays excluded even if policy allows it
}
```

### 2.3 Safe Mode and Implicit Approval Settings

**Settings.json options affecting approval:**
```json
{
  "safeMode": false,              // Disable safety checks (not recommended)
  "toolsEnabled": true,            // Enable/disable all tools
  "autoAccept": false,             // Auto-approve safe, read-only operations
  "allowImplicitApproval": false,  // Allow tools to execute without prompts (deprecated)
  "toolPermissions": {
    "alwaysAllow": [
      "run_shell_command",
      "write_file",
      "read_file",
      "shell"
    ]
  },
  "autoApprovedTools": [           // Older format, may be deprecated
    "run_shell_command",
    "write_file"
  ]
}
```

**Community confusion:** Users report trying various combinations of these settings without success. Reddit user (Dec 2025) documented attempting:
- `yolo: true` in settings.json
- `toolPermissions.alwaysAllow` array
- `autoApprovedTools` array
- `autoAccept: true`

...and still experiencing approval prompts for basic shell commands. **The issue was likely folder trust, not the approval mode itself.**

---

## 3. Non-Interactive / Headless Mode

### 3.1 Invocation Methods

**Non-interactive modes supported:**
- `gemini -p "prompt"` — Single prompt, no REPL
- `echo "prompt" | gemini` — Piped stdin
- `gemini -m gemini-2.0-flash -p "code review task"` — Model selection

**What happens in non-interactive mode:**
1. CLI parses prompt and context files (`@file.md` syntax)
2. Sends to LLM
3. Executes tool calls without waiting for user
4. Streams response to stdout
5. Exits with status code (0 = success, non-zero = error)

### 3.2 Known Headless Mode Issues

#### Issue #18776: Folder Trust in Headless Mode
**Context:** User runs `gemini -y -p "Write a file"` but folder is not trusted. Tool calls are rejected even though `--yolo` is set.

**Root cause:** Tool calls (especially `write_file`, `read_file`) fail because the **folder trust check happens independently** of the approval mode. The trust system exists at a different layer than the approval system.

**Workaround:** Pre-trust folders before headless execution:
```bash
gemini --trust-folder .
gemini --yolo -p "your task"
```

#### Issue #20438: Policy Engine Ignores `ask_user` in Headless
**Status:** FIXED (PR merged 2026-02-26)

The Policy Engine had a bug where `ask_user` decisions were not being converted to `DENY` in headless mode. This meant:
- Policy rule with `decision = "ask_user"` should block tools in headless contexts
- But they remained available, creating inconsistent behavior
- Fixed by ensuring `applyNonInteractiveMode()` is called when computing excluded tools

**Implication:** Policies can now reliably block dangerous tools in headless mode using `ask_user` as the decision.

#### Issue #20469: Approval Mode and Policy Engine Conflict (ONGOING)
**Status:** Reported as a critical design flaw

When using `--approval-mode auto_edit` in non-interactive mode with a policy that explicitly allows `run_shell_command`:
- The CLI hardcodes `run_shell_command` as excluded in auto_edit + headless context
- The Policy Engine has no mechanism to re-allow it
- Tools never register in the ToolRegistry
- Execution fails with "Tool not found"

**Current behavior matrix (non-interactive, with allow policy for run_shell_command):**

| Approval Mode | Result | Notes |
| --- | --- | --- |
| `--yolo` | Success | Explicitly bypasses hardcoded excludes |
| `auto_edit` | **Failure** | Hardcoded exclude, policy can't override |
| `default` | **Failure** | Part of defaultExcludes for headless |
| `plan` | **Failure** | Part of defaultExcludes for headless |

**Workaround:** Use `--yolo` for headless automation. Policy Engine is designed for interactive use and admin enforcement, not scripting.

---

## 4. Agent Framework Integration Patterns

### 4.1 Maestro: Multi-Agent Orchestration (Community Framework)

**Repository:** [josstei/maestro-gemini](https://github.com/josstei/maestro-gemini)
**Status:** Active (v1.1.0 as of 2026-02-16)
**Stars:** 116+ GitHub, Medium coverage

**Architecture:** Maestro turns a single Gemini CLI session into a 12-agent team with a TechLead orchestrator:

```
TechLead (Orchestrator)
  ├── architect      (system design)
  ├── coder          (implementation)
  ├── tester         (unit/integration tests)
  ├── debugger       (root cause analysis)
  ├── security-engineer (threat modeling, OWASP)
  ├── performance-engineer (profiling)
  ├── code-reviewer  (quality gates)
  ├── devops-engineer (CI/CD, infrastructure)
  ├── api-designer   (REST/GraphQL contracts)
  ├── data-engineer  (schema, query optimization)
  ├── refactor       (modernization)
  └── technical-writer (documentation)
```

**Workflow phases:**
1. **Design** — Structured requirements with trade-off analysis
2. **Plan** — Phase decomposition, agent assignment, dependency mapping
3. **Execute** — Parallel agent execution (where dependencies allow)
4. **Complete** — Final review and deliverable summary

**Key design decision:** Subagents run in `--yolo` mode, delegated by TechLead via separate `gemini` CLI processes. This means:
- Each agent has auto-approval enabled
- **The orchestrator, not the approval system, enforces boundaries**
- Agent capabilities are restricted per agent via tool whitelisting in delegation prompts
- Filesystem safety protocols are injected into every delegation

**Example delegation (from Maestro docs):**
```bash
gemini --yolo \
  --mcp github,firebase \
  -p "You are a code reviewer. Review this PR: [prompt + context]"
```

**Configuration via environment:**
```bash
MAESTRO_DEFAULT_MODEL=gemini-2.0-flash
MAESTRO_AGENT_TIMEOUT=300s
MAESTRO_MAX_CONCURRENT_AGENTS=4
MAESTRO_ENABLE_AGENTS=true  # Requires experimental.enableAgents in settings.json
```

**Lessons for autonomous review pipelines:**
- **Yolo mode is the standard** for subprocess-based agent orchestration
- **Tool restriction happens at prompt-level**, not via CLI approval modes (since approval modes don't work reliably in headless)
- **Each agent is a separate process**, not a conversation with subagents
- **Structured handoffs** between agents reduce hallucination (Downstream Context reports)

### 4.2 Other Community Patterns

**Pattern 1: Subprocess Integration (Generic)**
```bash
# Run gemini as a subprocess in a larger pipeline
gemini --yolo -p "Complete this task: $(cat task.txt)" > result.json
```

User issues reported:
- Stdout interleaving with debug logs (use `--quiet` or `--no-debug`)
- Approval dialogs blocking (solved by `--yolo`)
- Model timeouts in long-running tasks (need `--model gemini-2.0-flash` with explicit timeout)

**Pattern 2: CI/CD Integration (GitHub Actions, etc.)**
Standard approach:
1. Set `GEMINI_API_KEY` as GitHub Secret
2. Use `--yolo` flag
3. Redirect output to files
4. Parse JSON/YAML results for next step

Reddit user (Jan 2026) reported success using Gemini CLI in GitHub Actions with:
```bash
gemini --yolo -m gemini-2.0-flash --quiet -p "$(cat .github/prompts/review.md)"
```

**Pattern 3: Multi-Model Debate (Claude Code + Gemini CLI + Codex)**
Some users pipe output between multiple CLI tools:
```bash
# Use Gemini for initial analysis
gemini -p "Analyze this code" > analysis.md

# Use Codex for follow-up
codex -p "Based on this analysis: $(cat analysis.md), what are the top 3 issues?"
```

---

## 5. Configuration Best Practices (from Community)

### 5.1 User-Level Settings (`~/.gemini/settings.json`)

Recommended minimum for daily use:
```json
{
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    }
  },
  "ui": {
    "theme": "GitHub"
  },
  "general": {
    "previewFeatures": true
  }
}
```

For development (interactive):
```json
{
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    }
  },
  "general": {
    "checkpointing": {
      "enabled": true
    },
    "previewFeatures": true
  },
  "ui": {
    "theme": "GitHub"
  }
}
```

### 5.2 Project-Level Settings (`.gemini/settings.json`)

Checked into git for team consistency:
```json
{
  "sandbox": "docker",
  "fileFiltering": {
    "respectGitIgnore": true
  },
  "mcpServers": {
    "github": {
      "command": "npm",
      "args": ["start", "path/to/github-mcp"]
    }
  },
  "general": {
    "previewFeatures": true
  }
}
```

### 5.3 Automation-Specific (.env or environment)

For subprocess-based agents:
```bash
#!/bin/bash
export GEMINI_API_KEY=$(cat ~/.secrets/gemini-api-key)
export GEMINI_MODEL=gemini-2.0-flash
export GOOGLE_CLOUD_PROJECT=my-project

gemini --yolo \
  --sandbox \
  -p "Code review task..."
```

**Never in settings.json for CI/CD:** API keys, OAuth tokens, or project IDs. Use environment variables or secret managers.

### 5.4 Folder Trust Management

Critical for any headless automation:
```bash
# Mark all project directories as trusted (idempotent)
for dir in /workspace /home/user/projects/*/; do
  gemini --trust-folder "$dir"
done

# Verify trust
gemini --list-trusted-folders
```

Trusted folders are stored in:
- `~/.gemini/trusted_folders.json` (default)
- Or configurable via `trustedFoldersPath` in settings.json

---

## 6. Critical Gotchas and Workarounds

### Gotcha #1: Yolo Mode Doesn't Bypass Folder Trust
**Symptom:** `gemini --yolo -p "..."` still asks for permission or fails silently
**Root cause:** Folder trust and approval mode are orthogonal systems
**Fix:** Pre-trust folders with `gemini --trust-folder .` before headless execution

### Gotcha #2: Settings.json Approval Options Don't Work in Headless
**Symptom:** Setting `autoApprovedTools` or `allowImplicitApproval` in settings.json has no effect when running `gemini -p "..."`
**Root cause:** Settings.json approval options are designed for interactive REPL; headless mode uses hardcoded defaults
**Fix:** Use `--yolo` command-line flag instead (it works reliably in headless)

### Gotcha #3: Policy Engine Can't Override Hardcoded Headless Excludes
**Symptom:** Policy file allows `run_shell_command` with high priority, but CLI reports "Tool not found" in headless `auto_edit` mode
**Root cause:** Policy Engine only adds exclusions, never removes them. Hardcoded excludes are applied first
**Status:** Reported in issue #20469, no ETA for fix
**Workaround:** Use `--yolo` instead of `--approval-mode auto_edit`

### Gotcha #4: Non-Interactive Mode Produces Multiple Trace IDs
**Issue #23054:** When running in non-interactive mode, each tool invocation generates a separate trace ID. This breaks APM correlation across a single logical request.
**Impact:** Hard to debug distributed traces
**Workaround:** Log the parent trace ID in initial prompt and reference in post-processing

### Gotcha #5: Folder Trust Dialog on First Run
**Symptom:** First time running `gemini` in a new directory, it prompts "Trust this folder?"
**Context:** Security feature to prevent accidental file modification in untrusted contexts
**For automation:** Pre-run `gemini --trust-folder .` or set `"folderTrust": { "autoTrust": true }` in `.gemini/settings.json`

---

## 7. Comparison: Gemini CLI vs Claude Code vs Codex

| Feature | Gemini CLI | Claude Code | Codex |
| --- | --- | --- | --- |
| **Subprocess invocation** | Native (CLI) | Via skills/agents | Via CLI |
| **Approval mode in headless** | --yolo works, but issues with policies | Superpowers skills handle approval | Custom approval logic |
| **Folder trust** | Separate security layer | Per-workspace | Project-level |
| **Multi-agent orchestration** | Community frameworks (Maestro) | Native team support | Custom scripting |
| **Settings.json approval** | Limited effectiveness in headless | More reliable | N/A |
| **Policy engine** | Exists but conflicts with headless | Per-project settings | Configuration-based |
| **Community maturity** | ~2 years, growing adoption | 3+ years, production heavy | Emerging |

---

## 8. Recommendations for Autonomous Review Pipelines

### 8.1 Tool Selection

For a review pipeline using gemini-cli as a subprocess:

**✅ DO:**
- Use `--yolo` flag in all non-interactive invocations
- Pre-trust project directories with `gemini --trust-folder`
- Inject tool restrictions at the prompt level, not via approval modes
- Use environment variables for sensitive configuration
- Run each agent phase as a separate `gemini` process (Maestro pattern)

**❌ DON'T:**
- Rely on settings.json approval options in headless mode
- Use `--approval-mode auto_edit` for automation
- Expect Policy Engine to override hardcoded headless excludes
- Mix approval modes across a pipeline (inconsistent behavior)

### 8.2 Configuration Checklist

For autonomous review pipeline setup:
- [ ] User (`~/.gemini/settings.json`): minimal, theme only
- [ ] Project (`.gemini/settings.json`): MCP servers, sandbox, gitignore respect
- [ ] Environment: API key, model, cloud project (env vars or secrets manager)
- [ ] Pre-execution: `gemini --trust-folder . && gemini --list-trusted-folders`
- [ ] CLI invocation: `gemini --yolo --quiet -m gemini-2.0-flash -p "..."`
- [ ] Output handling: pipe to files, parse YAML/JSON results
- [ ] Error handling: log stderr separately, check exit codes

### 8.3 Safety for Headless Execution

Since approval modes don't work reliably in headless context, safety must be enforced elsewhere:

1. **Prompt-level tool scoping:**
   ```markdown
   You are a code reviewer. You have access to: read_file, grep_search, web_fetch.
   You DO NOT have access to: write_file, run_shell_command, delete_file.

   Never attempt these tools. If the user asks you to modify files, respond
   with specific instructions instead of executing write_file.
   ```

2. **Sandbox execution:**
   ```bash
   gemini --yolo --sandbox -p "..."  # Docker or Podman isolation
   ```

3. **Output filtering:**
   ```bash
   gemini --yolo -p "..." | jq '.toolCalls[] | select(.name != "dangerous_tool")'
   ```

4. **Explicit approval records:**
   ```bash
   gemini --yolo -p "..." | tee >(grep "write_file" >> /tmp/approvals.log)
   ```

---

## 9. Emerging Issues and Future Considerations

### 9.1 Planned Improvements (from Recent PRs)

- **PR #22670:** Support for `plan` mode in non-interactive context (in progress)
- **PR #23414:** Allow `-i/--prompt-interactive` with piped stdin (merging interactive + non-interactive)
- **Issue #23374:** Request for "ask only" feature in yolo mode (only ask for certain tools)

### 9.2 Infrastructure Trends

**Maestro popularity:** Growing adoption in agent orchestration, multi-agent orchestration is moving from prompt-hack to structured framework approach.

**Policy Engine investment:** Google is investing in better policy enforcement (PR #20438 fix), but the design flaw in #20469 suggests a fundamental mismatch between policy intent (interactive) and subprocess reality (headless).

**MCP server expansion:** More organizations building custom MCP servers to extend Gemini CLI with domain-specific tools, reducing reliance on shell commands.

---

## 10. Source References

### Official Documentation
- [Gemini CLI Configuration Guide](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md)
- [Gemini CLI Authentication](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/authentication.md)
- [Gemini CLI Hands-On Codelab](https://codelabs.developers.google.com/gemini-cli-hands-on)

### Community Guides
- [Gemini CLI Tutorial Series Part 3](https://medium.com/google-cloud/gemini-cli-tutorial-series-part-3-configuration-settings-via-settings-json-and-env-files-669c6ab6fd44) — Romin Irani, Google Cloud Community (2025-07-03)
- [Google Gemini CLI Cheatsheet](https://www.philschmid.de/gemini-cli-cheatsheet) — Philipp Schmid (2025-07-24)
- [Gemini CLI Settings with MCP](https://audrey.feldroy.com/articles/2025-07-27-Gemini-CLI-Settings-With-MCP) — Audrey Roy Greenfeld (2025-07-27)

### GitHub Issues (Critical)
- [#18776](https://github.com/google-gemini/gemini-cli/issues/18776) — Trusting folders in headless mode (OPEN)
- [#20438](https://github.com/google-gemini/gemini-cli/pull/20438) — Policy Engine ask_user in headless (MERGED 2026-02-26)
- [#20469](https://github.com/google-gemini/gemini-cli/issues/20469) — Approval mode conflict with headless (OPEN, critical design flaw)
- [#2748](https://github.com/google-gemini/gemini-cli/issues/2748) — Non-interactive mode in scripting (CLOSED)

### Community Projects
- [Maestro: Multi-Agent Orchestration](https://github.com/josstei/maestro-gemini) — 12-agent framework for Gemini CLI (116 stars, active maintenance)

### Reddit Discussions
- [How to stop gemini cli from asking permissions?](https://www.reddit.com/r/GeminiAI/comments/1poqd9g/) — Dec 2025, user documentation of approval mode confusion
- [Maestro v1.1.0 Update](https://www.reddit.com/r/GeminiCLI/comments/1r5wo95/) — Feb 2026, community framework for agent orchestration

---

## 11. Conclusion

Gemini CLI is viable for autonomous review pipelines, but requires careful configuration awareness:

1. **Use `--yolo` flag exclusively** for headless automation — settings.json approval options are unreliable
2. **Pre-trust folders** before headless execution — folder trust is orthogonal to approval modes
3. **Avoid Policy Engine in headless contexts** — it's designed for interactive use; design flaw (#20469) prevents tool re-allowance
4. **Enforce safety at the prompt level**, not via CLI approval modes — scope tools in delegation prompts
5. **Follow Maestro pattern** for multi-phase orchestration — separate processes per agent, structured handoffs

The framework is maturing (2+ years old, community adoption), but the approval system shows growing pains in headless contexts. As more teams adopt agent orchestration, expect these issues to be prioritized.

---
name: chezmoi-agent-config
description: Manage AI agent configurations (CLAUDE.md, AGENTS.md, permissions, MCP settings, skills) across multiple tools and machines using chezmoi templates. Use when syncing .claude/ settings across machines, templating CLAUDE.md for different environments, distributing agent instructions to Claude Code/Codex/Copilot from one source, managing AI agent permissions via chezmoi data, backing up Claude Code config with chezmoi, or setting up a shared skills directory.
---

# Chezmoi Agent Config Management

Use chezmoi templates to manage and distribute AI agent configurations across tools (Claude Code, Codex, Copilot) and machines.

## Why Chezmoi for Agent Config?

- **One source of truth** — Write agent instructions once, render for each tool
- **Cross-machine sync** — Same agent behavior on personal Mac, work laptop, CI
- **Templated secrets** — Inject API keys via 1Password/age, never plaintext
- **Version controlled** — Track changes, rollback, review diffs

## 1. Track Claude Code Config

Add Claude Code configuration to chezmoi:

```bash
chezmoi add ~/.claude/CLAUDE.md
chezmoi add ~/.claude/settings.json
chezmoi add --template ~/.claude/settings.local.json   # Template for secrets
chezmoi add ~/.claude/rules/                           # All rules
chezmoi add ~/.claude/agents/                          # All agent definitions
```

**Verify managed files:**
```bash
chezmoi managed | grep claude
```

## 2. Template CLAUDE.md for Environments

Convert to template for machine-specific behavior:

```bash
chezmoi add --template ~/.claude/CLAUDE.md
```

**dot_claude/CLAUDE.md.tmpl:**
```go
# Project Instructions

## Environment: {{ .chezmoi.hostname }}

{{ if eq .env "work" -}}
## Work Policies
- Use company proxy for all network requests
- Follow SOC2 compliance guidelines
{{ else -}}
## Personal Setup
- Use personal GitHub account
- Experimental features enabled
{{ end -}}

## Common Instructions
- Use mise for tool management
- Follow declarative config policy
```

**Data in .chezmoidata/env.yaml:**
```yaml
env: personal    # Override per machine in chezmoi.toml
```

## 3. Distribute to Multiple AI Tools

Render one canonical source to tool-specific formats:

**dot_claude/CLAUDE.md.tmpl** and **dot_codex/AGENTS.md.tmpl** share content:

```go
{{- /* shared agent instructions */ -}}
{{ $instructions := include ".chezmoitemplates/agent-instructions.md.tmpl" . -}}
{{ $instructions }}
```

**.chezmoitemplates/agent-instructions.md.tmpl:**
```go
# Agent Instructions

## Identity
You are assisting {{ .name }} ({{ .role }}).

## Tools
{{ if eq .chezmoi.os "darwin" -}}
- Package manager: brew + mise
{{ else -}}
- Package manager: apt + mise
{{ end -}}

## Rules
- Always check existing tools before writing code
- Use declarative configuration
```

This renders to both `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.

## 4. Manage Permissions via Data

**dot_chezmoidata/permissions.yaml:**
```yaml
claude:
  allowed_tools:
    - Read
    - Write
    - Edit
    - Bash
    - Glob
    - Grep
  denied_patterns:
    - "rm -rf /"
    - "sudo"

codex:
  sandbox: true
  network: false
```

**dot_claude/settings.json.tmpl:**
```go
{
  "permissions": {
    "allow": [
      {{ range $i, $tool := .claude.allowed_tools -}}
      {{ if $i }}, {{ end }}"{{ $tool }}"
      {{ end -}}
    ]
  }
}
```

## 5. Auto-Backup with Hooks

**PostToolUse hook** — auto-add Claude config changes:
```bash
# After editing .claude/ files, add to chezmoi
chezmoi add ~/.claude/CLAUDE.md
chezmoi add ~/.claude/settings.json
```

**Stop hook** — re-add all Claude config on session end:
```bash
chezmoi re-add
```

These can be configured in Claude Code's settings.json hooks or in the chezmoi-toolkit hooks.

## 6. Shared Skills Directory

**Pattern:** One canonical skills directory, chezmoi distributes to each tool.

```
.chezmoisource/
├── dot_agents/skills/          # Canonical skills (source of truth)
│   ├── my-skill/SKILL.md
│   └── another-skill/SKILL.md
├── dot_claude/skills -> ../dot_agents/skills  # Symlink or copy
└── dot_codex/skills -> ../dot_agents/skills   # Symlink or copy
```

**Or use chezmoi externals to pull skills from a shared repo:**
```toml
# .chezmoiexternal.toml
[".agents/skills/shared-skills"]
    type = "git-repo"
    url = "https://github.com/org/shared-agent-skills.git"
    refreshPeriod = "168h"
```

## 7. MCP Server Config

Template MCP configs for environment-specific servers:

**dot_claude/dot_mcp.json.tmpl:**
```go
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "{{ onepasswordRead "op://Dev/GitHub-PAT/token" }}"
      }
    }
    {{ if eq .env "work" -}}
    ,"jira": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/jira"],
      "env": {
        "JIRA_URL": "{{ .work.jira_url }}"
      }
    }
    {{ end -}}
  }
}
```

## Workflow Summary

1. **Add** agent configs to chezmoi: `chezmoi add ~/.claude/`
2. **Template** machine-specific parts: `chezmoi add --template`
3. **Store** secrets via 1Password/age (never plaintext)
4. **Sync** across machines: `chezmoi git -- pull` then `chezmoi diff` to review
5. **Apply** (user responsibility): `chezmoi apply` after reviewing diff

## Related Skills

- **chezmoi-config** — Go template syntax and password manager integration
- **chezmoi-workflows** — Cross-machine sync workflows
- **chezmoi-advanced-config** — Encryption setup for secrets
- **chezmoi-troubleshooting** — Debug template rendering issues

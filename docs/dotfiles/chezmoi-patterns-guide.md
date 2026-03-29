# Chezmoi Patterns Guide

Patterns and conventions for this project's chezmoi+mise+hk dotfiles stack.
Adapted from community best practices (Drewtopia, bramswenson, twpayne, rio)
and validated against our specific architecture: a mixed Python package + chezmoi
source repository.

## Architecture Overview

```
macos-development-environment/          # Python package repo root
  .chezmoisource/                       # chezmoi source state (custom sourceDir)
    .chezmoi.toml.tmpl                  # Bootstrap config template
    .chezmoidata/                       # Structured data files (YAML)
      tools.yaml                        # 110 mise tool definitions, 19 categories
    .chezmoiexternals/                  # External sources (archives, git repos)
    .chezmoiignore                      # Exclusion patterns for mixed-repo safety
    .chezmoiscripts/                    # Lifecycle scripts (run_onchange_)
    Brewfile.tmpl                       # Homebrew casks + brew-only formulas
    dot_config/mise/config.toml.tmpl    # mise configuration (data-driven template)
    dot_gitconfig.tmpl                  # Git configuration with template variables
    dot_gitignore_global                # Global gitignore
    dot_oh-my-zsh/custom/              # Oh My Zsh custom plugins and themes
    dot_tmux.conf                       # tmux configuration
    dot_zprofile.d/                     # Shell profile snippets
    dot_zshrc.tmpl                      # Zsh configuration (managed entry point)
    private_dot_ssh/                    # SSH config (0700 auto-applied)
  src/mde/                              # Python automation package
  tests/                                # pytest suite
```

### Why a Subdirectory Source?

Most chezmoi repos use the repo root as the source directory. This project is a
Python package that also manages dotfiles, so `.chezmoisource/` is a subdirectory.
The `sourceDir` key in `~/.config/chezmoi/chezmoi.toml` points to it.

Alternative: the `.chezmoiroot` file (used by twpayne's own dotfiles) lets chezmoi
discover the subdirectory automatically. We use `sourceDir` instead because:
- The bootstrap template (`.chezmoi.toml.tmpl`) already self-references sourceDir
- The mixed-repo layout predates `.chezmoiroot` adoption
- Both approaches are officially supported

## Template Patterns

### Data-Driven Templates

Templates consume structured data from `.chezmoidata/` files instead of
hardcoded values. This separates tool definitions from template logic.

```yaml
# .chezmoidata/tools.yaml
mise:
  tools:
    core_runtimes:
      - { name: "core:python", version: latest }
      - { name: "core:node", version: latest }
    security:
      - { name: gitleaks, version: latest }
```

```
{{/* config.toml.tmpl */}}
{{ range $cat, $tools := .mise.tools }}
# --- {{ $cat }} ---
{{ range $tools }}
{{ template "render-tools" . }}
{{ end }}
{{ end }}
```

**Benefits:**
- Tool additions require only a YAML edit, not template changes
- Category grouping enables selective rendering (e.g., platform-gated sections)
- Renovate/Dependabot can auto-update version pins in data files

### Template Variables from Config

The bootstrap template (`.chezmoi.toml.tmpl`) populates variables available to
all templates:

```toml
# ~/.config/chezmoi/chezmoi.toml (generated from .chezmoi.toml.tmpl)
sourceDir = "/path/to/.chezmoisource"

[data.git]
  name = "Your Name"
  email = "your@email.com"
```

Templates reference these via `{{ .git.name }}`, `{{ .git.email }}`.

### TOML Key Quoting

Tool names containing `:`, `/`, `@`, or spaces require TOML quoting:

```
{{- define "toml-key" -}}
  {{- if regexMatch "[:/@ ]" . }}"{{ . }}"{{ else }}{{ . }}{{ end -}}
{{- end -}}
```

Examples: `"core:python"`, `"npm:@langchain/langgraph-cli"`, `gitleaks`.

### Platform Conditionals

Use `{{ .chezmoi.os }}` to gate platform-specific sections:

```
{{- if eq .chezmoi.os "darwin" }}
# macOS-only tools
1password-cli = "latest"
xcodegen = "latest"
{{- end }}
```

Convention: categories with a `_darwin` suffix are wrapped in OS conditionals.

### Config Value Types

The template distinguishes between TOML value types for tool configuration:

| Field | Type | Example |
|-------|------|---------|
| `version` | string | `version = "latest"` |
| `extras` | string | `extras = "browser"` |
| `symlink_bins` | boolean | `symlink_bins = true` |

Boolean fields must not be quoted in YAML data files. Use `true`/`false` without
quotes to emit correct TOML.

## File Naming Conventions

| chezmoi prefix | Target | Permissions |
|---------------|--------|-------------|
| `dot_` | `~/.filename` | default (0644) |
| `private_dot_` | `~/.filename` | 0700 (dirs) / 0600 (files) |
| `executable_` | executable file | 0755 |
| `.tmpl` suffix | templated file | rendered by chezmoi |

**Key convention:** `private_dot_ssh/` ensures `~/.ssh/` has 0700 automatically.

## Script Patterns

### run_onchange vs run_once

| Prefix | When it runs | Use case |
|--------|-------------|----------|
| `run_once_` | Once per unique content (SHA256) | One-time installs |
| `run_onchange_` | When file content hash changes | Re-run on config change |
| `run_` | Every `chezmoi apply` | Always-run checks |

This project uses `run_onchange_` for mise install scripts: when the config
template changes (e.g., new tool added), the install script re-runs.

```bash
# .chezmoiscripts/run_onchange_after_install_mise.sh.tmpl
#!/bin/bash
# Hash: {{ include "dot_config/mise/config.toml.tmpl" | sha256sum }}
mise install --yes
```

The hash comment triggers re-execution when the template changes.

### Script Ordering

Scripts run in alphabetical order within their prefix group. Use numeric prefixes
for explicit ordering:

```
run_once_before_01-install-mise.sh
run_once_before_02-bootstrap-shell.sh
run_onchange_after_install_mise.sh.tmpl
```

`before_` scripts run before file deployment; `after_` scripts run after.

## Ignore Patterns

`.chezmoiignore` prevents chezmoi from deploying specified files:

```
# Python package files (mixed-repo safety)
src/
tests/
docs/
pyproject.toml

# OS-specific excludions
{{ if ne .chezmoi.os "darwin" }}
Brewfile
{{ end }}

# Secrets (never deploy plaintext)
**/*.key
**/*.pem
**/id_*
```

Critical for mixed-repo layouts where non-dotfile directories exist alongside
the chezmoi source.

## Secrets Integration

This project uses Doppler as the source of truth for secrets:

```
Doppler (cloud) -> sync -> fnox (macOS Keychain) -> mise (env) -> tools
```

In chezmoi templates, secrets are resolved via the `doppler` template function:

```
# dot_gitconfig.tmpl
[user]
    signingkey = {{ doppler "GIT_SIGNING_KEY" }}
```

Or via environment variables that mise injects from fnox:

```
# Resolved at shell init, not chezmoi apply time
export GITHUB_TOKEN="${GITHUB_TOKEN}"
```

See `secrets-management.md` in `.claude/rules/` for the full flow.

## External Sources

`.chezmoiexternals/` imports files from outside the repo:

```toml
# .chezmoiexternals/mise.toml
[".mise.toml"]
    type = "file"
    url = "https://raw.githubusercontent.com/.../mise.toml"
    refreshPeriod = "168h"
```

Use `refreshPeriod` to cache external sources and avoid network calls on every apply.

## Daily Operations

```bash
chezmoi diff              # Preview pending changes
chezmoi apply             # Apply all changes
chezmoi apply --dry-run   # Dry run (show what would change)
chezmoi edit ~/.zshrc     # Edit source, auto-apply on exit
chezmoi cd                # cd into source directory
chezmoi data              # Show template data (debug)
chezmoi doctor            # Health check
chezmoi verify            # Exit 0 if target matches source, 1 if drift
```

### Useful Aliases

```bash
alias cm='chezmoi'
alias cma='chezmoi apply'
alias cmd='chezmoi diff'
alias cme='chezmoi edit --apply'
alias cmcd='chezmoi cd'
```

## Bootstrap (New Machine)

```bash
# 1. Install chezmoi
sh -c "$(curl -fsLS get.chezmoi.io)"

# 2. Init from repo (clones to default location)
chezmoi init ray-manaloto/macos-development-environment

# 3. Configure local data (one-time)
cat >> ~/.config/chezmoi/chezmoi.toml << 'EOF'
sourceDir = "/path/to/macos-development-environment/.chezmoisource"

[data.git]
  name = "Your Name"
  email = "your@email.com"

[doppler]
  project = "dotfiles"
  config = "dev"
EOF

# 4. Apply
chezmoi apply
```

**Bootstrap gap:** The `.chezmoi.toml.tmpl` self-references `sourceDir`, so on a
fresh machine the default `~/.local/share/chezmoi` path is written unless you
manually set `sourceDir` first. This is a known limitation of the mixed-repo layout.

## Community References

These repos informed our patterns:

| Repo | Stack | Key pattern adopted |
|------|-------|-------------------|
| [bramswenson/dotfiles](https://github.com/bramswenson/dotfiles) | chezmoi+mise+hk | `private_dot_` for SSH, modular shell RC |
| [Drewtopia/dotfiles](https://github.com/Drewtopia/dotfiles) | chezmoi+mise+1Password | `.chezmoidata/`, feature flags, auth architecture |
| [twpayne/dotfiles](https://github.com/twpayne/dotfiles) | chezmoi (author) | `.chezmoiroot` subdirectory pattern |
| [rio/dotfiles](https://github.com/rio/dotfiles) | chezmoi+mise | Environment detection, DevPod/Codespaces support |
| [martinemde/dotfiles](https://github.com/martinemde/dotfiles) | chezmoi+mise | Minimal portable config, fast shell startup |
| [felipecrs/dotfiles](https://github.com/felipecrs/dotfiles) | chezmoi | Single-command bootstrap, container support |

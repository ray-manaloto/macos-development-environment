---
name: mde-dotfiles-lifecycle
description: >
  Coordinates the full chezmoi + mise lifecycle for cross-system changes.
  Use when adding a tool that needs both mise config and shell config changes,
  changing env vars that must propagate across machines, provisioning a fresh
  machine, or debugging a mismatch between mise tool state and shell startup.
  Key files: .chezmoisource/dot_config/mise/config.toml.tmpl,
  .chezmoisource/dot_oh-my-zsh/custom/10-mde-core.zsh,
  .chezmoisource/dot_zprofile.d/macos-dev-env.zsh.
---

# MDE Dotfiles Lifecycle

Cross-system coordination guide for changes that span chezmoi-managed dotfiles
and mise tool state. For template syntax and file authoring, see
`mde-chezmoi-dotfiles`. For backend selection when adding tools, see
`mise-tool-management`.

## Use This Skill When

- Adding a tool that requires both a `[tools]` entry in mise config and a shell
  alias or env var in an oh-my-zsh custom file
- Changing or adding env vars that must be consistent across machines
  (e.g. `EDITOR`, `DOCKER_HOST`, API tokens)
- Running bootstrap or provisioning on a fresh machine
- Debugging a mismatch: a tool is installed via mise but its env var is missing
  from shell startup, or vice versa

## Decision Tree

```
Change needed
  |
  +-- Does it add/remove a CLI tool?
  |     YES --> mise config (dot_config/mise/config.toml.tmpl)
  |              |
  |              +-- Does the tool need a shell alias or env var?
  |                    YES --> also edit shell rc (10-mde-core.zsh or 20-mde-aliases.zsh)
  |                    NO  --> mise only
  |
  +-- Does it set an env var only (no new tool)?
  |     YES --> see Env Var Coordination table below
  |
  +-- Does it install a GUI app (cask)?
  |     YES --> Brewfile.tmpl only (triggers brew bundle via chezmoi onchange script)
  |              See mde-homebrew skill
  |
  +-- Does it change shell startup behavior (aliases, prompt, PATH)?
        YES --> chezmoi only (dot_oh-my-zsh/custom/*.zsh or dot_zprofile.d/)
```

## Full Lifecycle — Adding a Tool That Spans Both Systems

Use this sequence when a change touches mise config AND shell config.

```bash
# 1. Edit mise global config (chezmoi-managed)
$EDITOR .chezmoisource/dot_config/mise/config.toml.tmpl

# 2. Edit shell config if needed (aliases, env vars, PATH additions)
$EDITOR .chezmoisource/dot_oh-my-zsh/custom/10-mde-core.zsh   # env vars
$EDITOR .chezmoisource/dot_oh-my-zsh/custom/20-mde-aliases.zsh # aliases

# 3. Preview what chezmoi will change
chezmoi diff

# 4. Apply dotfiles to home directory
chezmoi apply

# 5. Install tools declared in mise config
mise install --yes

# 6. Lock tool versions (creates/updates mise.lock)
mise lock

# 7. Regenerate shims so new binaries are on PATH
mise reshim

# 8. Validate — must pass before committing
uv run mde-py validate --all
```

For Brewfile changes within the same PR, `chezmoi apply` in step 4 will
automatically trigger `run_onchange_before_install-packages-darwin.sh.tmpl`,
which runs `brew bundle`. No separate `brew bundle` invocation is needed.

## Bootstrap Sequence — Fresh Machine

Run this sequence on a new machine after cloning the repo.

```bash
# 1. Initialize chezmoi from the repo (sets up source dir and config)
chezmoi init --source /path/to/macos-development-environment

# 2. Apply all dotfiles to home directory
chezmoi apply

# 3. Install all mise-managed tools
mise install --yes

# 4. Lock versions and generate shims
mise lock
mise reshim

# 5. Verify system state
mise run mde:agent:preflight   # comprehensive preflight check
mise run mde:verify            # verify tool versions match locked config
mise run mde:drift             # check for config drift

# 6. Validate mde quality gate (should show 6/6 passed)
uv run mde-py quality
```

On a fresh machine, `chezmoi apply` will also trigger `brew bundle` for the
Brewfile if Homebrew is installed. If Homebrew is not yet installed, install it
first before running `chezmoi apply`.

## Env Var Coordination

Use this table to decide where to place an env var.

| Location | File | Use when |
|----------|------|----------|
| `mise [env]` | `.chezmoisource/dot_config/mise/config.toml.tmpl` | Var is needed only within mise-activated sessions; tool-specific (e.g. `GOPATH`, `CARGO_HOME`) |
| Core shell startup | `.chezmoisource/dot_oh-my-zsh/custom/10-mde-core.zsh` | Var must be available before mise activates or in all shells; foundational (e.g. `EDITOR`, `PAGER`, `XDG_*`) |
| Login-shell PATH | `.chezmoisource/dot_zprofile.d/macos-dev-env.zsh` | Var affects login-shell PATH ordering; needed by GUI apps launched from macOS (e.g. adding `/usr/local/bin` before system paths) |
| Template with remote guard | Either of the above, inside `{{ if not .remote }}` | Var is only meaningful on a local workstation (e.g. `DISPLAY`, GUI-app paths, Keychain tokens) |

Rules:
- Prefer `mise [env]` for tool-specific vars so they only activate in
  mise-managed shells.
- Use `10-mde-core.zsh` for vars that must be set before `eval "$(mise activate
  zsh)"` runs.
- Never set the same var in both `mise [env]` and a shell rc file — pick one
  owner or the last-writer wins silently.
- Secrets go in `mise [env]` via Keychain lookup, not hardcoded:

```toml
[env]
GITHUB_TOKEN = "{{ keyring \"github\" \"token\" }}"
```

## Remote-Aware Templates

The `.remote` boolean is `true` in Codespaces, CI, SSH sessions, Docker, and
Kubernetes. Use it to guard anything that requires local GUI or interactive
infrastructure.

```toml
# .chezmoisource/dot_config/mise/config.toml.tmpl
{{ if not .remote -}}
[env]
DOCKER_HOST = "unix:///var/run/docker.sock"
{{- end }}
```

```zsh
# .chezmoisource/dot_oh-my-zsh/custom/10-mde-core.zsh
{{ if not .remote -}}
export DISPLAY=:0
{{- end }}
```

Guard rules:
- GUI app launch paths: always guard with `{{ if not .remote }}`
- Keychain lookups: guard so CI does not fail with missing entries
- brew cask installs: `run_onchange_before_install-packages-darwin.sh.tmpl`
  already skips on non-Darwin; add `.remote` guard for headless Darwin CI

## Shell Startup Performance

Slow shell startup is usually caused by heavy work in `10-mde-core.zsh` or
`90-starship.zsh`. Profile before and after any significant shell config change.

```bash
# Measure interactive shell startup time
time zsh -i -c exit

# Acceptable: < 300ms
# Investigate: 300ms - 1s
# Fix required: > 1s
```

To identify the slow line:

```zsh
# Add to the TOP of ~/.zshrc (temporarily):
zmodload zsh/zprof

# Add to the BOTTOM of ~/.zshrc:
zprof
```

Then open a new terminal and read the `zprof` report. Common culprits:
- `nvm` or `rbenv` slow init — use mise instead
- `eval "$(command)"` repeated on every shell — cache the output or use mise
- Synchronous network calls (e.g. `curl` in rc files)

After fixing, remove `zmodload zsh/zprof` and `zprof` and re-time.

## Cross-References

| Skill | When to use it |
|-------|---------------|
| `mde-chezmoi-dotfiles` | Template syntax, secret injection, drift debugging, managed file map |
| `mise-tool-management` | Backend selection, adding a single tool, drift detection |
| `mde-homebrew` | Cask management, brew vs mise ownership conflicts, Brewfile editing |

---
name: mde-chezmoi-dotfiles
description: >
  Repo-specific chezmoi editing guide for macos-development-environment.
  Use when editing .chezmoisource/ files, adding shell aliases or env vars,
  injecting secrets via keychain or age, debugging drift between source and home
  directory, or authoring templates for Brewfile, mise config, oh-my-zsh customs,
  tmux, or zprofile.d. Key files: .chezmoisource/.chezmoi.toml.tmpl,
  .chezmoisource/Brewfile.tmpl, src/mde/validate/chezmoi.py.
---

# MDE Chezmoi Dotfiles

Repo-specific guide for editing chezmoi-managed dotfiles in this repo. For
generic chezmoi syntax and command reference, see the `chezmoi-config` and
`chezmoi-workflows` ecosystem skills. This skill covers only what is specific to
this repo.

## Use This Skill When

- Editing any file under `.chezmoisource/`
- Adding a shell alias, env var, or PATH entry
- Injecting a secret from macOS Keychain or an age-encrypted file
- Debugging drift: `chezmoi verify` exits non-zero or `uv run mde-py validate --all` reports chezmoi issues
- Authoring or reviewing templates that use the `.remote` data variable

## Contract

1. Never edit deployed files directly (e.g. `~/.tmux.conf`, `~/.oh-my-zsh/custom/*.zsh`).
2. All changes go into `.chezmoisource/` first, then `chezmoi apply`.
3. Drift is detected by `uv run mde-py validate --all` (includes chezmoi drift check via `chezmoi verify --exclude=scripts`).
4. The Brewfile is managed by chezmoi: edit `.chezmoisource/Brewfile.tmpl`, not `~/Brewfile`.
5. Scripts under `.chezmoisource/.chezmoiscripts/` run via chezmoi lifecycle hooks — do not run them manually.

## Managed File Map

| Source path (in `.chezmoisource/`) | Deployed target |
|------------------------------------|----------------|
| `Brewfile.tmpl` | `~/Brewfile` |
| `dot_config/mise/config.toml.tmpl` | `~/.config/mise/config.toml` |
| `dot_oh-my-zsh/custom/10-mde-core.zsh` | `~/.oh-my-zsh/custom/10-mde-core.zsh` |
| `dot_oh-my-zsh/custom/15-mde-platform.zsh` | `~/.oh-my-zsh/custom/15-mde-platform.zsh` |
| `dot_oh-my-zsh/custom/20-mde-aliases.zsh` | `~/.oh-my-zsh/custom/20-mde-aliases.zsh` |
| `dot_oh-my-zsh/custom/90-starship.zsh` | `~/.oh-my-zsh/custom/90-starship.zsh` |
| `dot_oh-my-zsh/custom/aliases.zsh` | `~/.oh-my-zsh/custom/aliases.zsh` |
| `dot_oh-my-zsh/custom/llvm.zsh` | `~/.oh-my-zsh/custom/llvm.zsh` |
| `dot_oh-my-zsh/custom/macos-env.zsh` | `~/.oh-my-zsh/custom/macos-env.zsh` |
| `dot_tmux.conf` | `~/.tmux.conf` |
| `dot_zprofile.d/macos-dev-env.zsh` | `~/.zprofile.d/macos-dev-env.zsh` |

Configuration bootstrap (not a deployed target): `.chezmoi.toml.tmpl` is read by
chezmoi at init to produce `~/.config/chezmoi/chezmoi.toml`. It is not listed by
`chezmoi managed` and is not checked by `chezmoi verify`.

Scripts (not deployed files):

| Source path | When it runs |
|-------------|-------------|
| `.chezmoiscripts/run_onchange_before_install-packages-darwin.sh.tmpl` | Before apply, when Brewfile content changes |
| `.chezmoiscripts/run_onchange_after_install_mise.sh.tmpl` | After apply, when mise config changes |

## Template Authoring

### Available data variables

Run `chezmoi data` to see all variables. Key custom variable:

| Variable | Type | Description |
|----------|------|-------------|
| `.remote` | `bool` | `true` when running in Codespaces, SSH, Docker, Kubernetes, or REMOTE_CONTAINERS |
| `.chezmoi.os` | `string` | `"darwin"` on macOS |
| `.chezmoi.arch` | `string` | `"arm64"` on Apple Silicon |
| `.chezmoi.homeDir` | `string` | Absolute path to home directory |

### OS conditional

```
{{ if eq .chezmoi.os "darwin" -}}
# macOS-only block
{{- end }}
```

### Remote/CI detection

Use `.remote`, not `.chezmoi.container`. The `.remote` variable is computed in
`.chezmoisource/.chezmoi.toml.tmpl` from five environment variables and the
presence of `/.dockerenv`:

```
{{- $remote := or (env "CODESPACES" | not | not) (env "SSH_CONNECTION" | not | not) (env "KUBERNETES_SERVICE_HOST" | not | not) (env "container" | not | not) (env "REMOTE_CONTAINERS" | not | not) (stat "/.dockerenv" | not | not) -}}
```

Example usage in a template:

```
{{ if not .remote -}}
# local-only block (skip in CI, Codespaces, SSH)
{{- end }}
```

### Preview template output

```bash
chezmoi execute-template < .chezmoisource/Brewfile.tmpl
chezmoi data    # inspect all variables
```

## Secret Injection

### macOS Keychain

```
{{ keyring "service-name" "account-name" }}
```

Example in `.chezmoisource/dot_config/mise/config.toml.tmpl`:

```
[env]
GITHUB_TOKEN = "{{ keyring "github" "token" }}"
```

Store the secret first:

```bash
security add-generic-password -s "github" -a "token" -w "ghp_..."
```

### Age-encrypted files

Prefix the source file with `encrypted_` and add `.age` extension:

```
.chezmoisource/encrypted_dot_config/secret.age
```

Decryption is automatic during `chezmoi apply` if age is configured in
`.chezmoi.toml`. See `chezmoi-config` skill for encryption setup details.

## External Sources

`.chezmoisource/.chezmoiexternals/mise.toml.tmpl` installs the `mise` binary
into `~/.local/bin/mise` when `mise` is not already on PATH:

```toml
{{- if not (lookPath "mise") -}}
[".local/bin/mise"]
type = "file"
executable = true
url = "https://mise.jdx.dev/mise-latest-{{ .chezmoi.os }}-{{ .chezmoi.arch }}"
{{- end -}}
```

To add a new external (e.g. an oh-my-zsh plugin or tmux plugin manager), edit
`.chezmoisource/.chezmoiexternals/mise.toml.tmpl` or create a new `.toml.tmpl`
file in `.chezmoiexternals/`. External archives support `refreshPeriod` to
control how often chezmoi re-fetches.

## Standard Workflow

```bash
# 1. Edit the source file
$EDITOR .chezmoisource/<path>

# 2. Preview the diff before applying
chezmoi diff

# 3. Apply to home directory
chezmoi apply

# 4. Validate — must pass (includes chezmoi drift check)
uv run mde-py validate --all
```

For Brewfile changes, `chezmoi apply` triggers the `run_onchange_before` script
automatically, which runs `brew bundle`. No manual `brew bundle` invocation is
needed.

## Health Check

```bash
# Check chezmoi setup
chezmoi doctor

# Check for drift (scripts excluded — they are not idempotent)
chezmoi verify --exclude=scripts

# Same check via mde quality gate (chezmoi is part of --all)
uv run mde-py validate --all

# Show all managed files
chezmoi managed

# Show what would change
chezmoi diff
```

## CI / Agent Context

- Pass `--no-tty` to chezmoi when running in non-interactive contexts:
  `chezmoi apply --no-tty`
- The `.remote` variable is `true` automatically when `SSH_CONNECTION`,
  `CODESPACES`, `KUBERNETES_SERVICE_HOST`, `REMOTE_CONTAINERS`, or `container`
  env vars are set, or when `/.dockerenv` exists. No manual override is needed.
- In CI, `HOMEBREW_NO_AUTO_UPDATE=1` should be set before any brew operations
  triggered by `chezmoi apply`.
- `chezmoi verify --exclude=scripts` is safe to run in CI; it does not apply
  changes.

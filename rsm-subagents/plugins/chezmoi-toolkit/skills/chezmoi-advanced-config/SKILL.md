---
name: chezmoi-advanced-config
description: Advanced chezmoi configuration beyond basic templates. Use when setting up monorepo dotfiles with .chezmoiroot, removing old files with .chezmoiremove, configuring git autoCommit/autoPush, setting up age or GPG encryption, managing encryption keys, using multiple config formats (YAML/JSON/TOML), or creating custom chezmoi commands.
---

# Chezmoi Advanced Configuration

Reference guide for advanced chezmoi features: monorepo support, cleanup, git automation, encryption, and format options.

## 1. Monorepo with .chezmoiroot

**Problem:** Dotfiles live in a subdirectory of a larger repo.

**Solution:** Create `.chezmoiroot` in repo root containing the relative path:

```
company-infra/
├── terraform/
├── kubernetes/
├── .chezmoiroot          # Contains: "dotfiles"
├── dotfiles/
│   ├── .chezmoi.toml.tmpl
│   ├── dot_zshrc
│   └── ...
└── README.md
```

`.chezmoiroot` content (just one line):
```
dotfiles
```

**Initialize:**
```bash
chezmoi init https://github.com/org/company-infra.git
```

**Decision:** Use .chezmoiroot when dotfiles are in a subdirectory. Skip if dotfiles are at repo root (the default).

## 2. Cleanup with .chezmoiremove

**Problem:** Need to remove deprecated dotfiles on apply.

**Create `.chezmoiremove`** (or `.chezmoiremove.tmpl` for conditionals):
```text
~/.config/old-tool/config
~/.oh-my-zsh/custom/deprecated.zsh
~/.vim/old-plugins/*
```

**Conditional removal:**
```go
{{- if eq .chezmoi.os "darwin" }}
~/.kube/config-old
{{- end }}
```

**Safety — always preview first:**
```bash
chezmoi apply --dry-run    # Shows what would be removed
chezmoi diff               # Shows file-level changes
```

**Decision:** Use .chezmoiremove when migrating tools (e.g., antigen → zplug) or cleaning deprecated paths. Skip for manual one-off deletions.

## 3. Git Automation

### Auto-commit
```toml
[git]
    autoCommit = true
```
Automatically commits after `chezmoi add` / `chezmoi edit`.

### Auto-push
```toml
[git]
    autoCommit = true
    autoPush = true
```
Pushes to remote after each commit. Requires autoCommit.

### Custom commit message
```toml
[git]
    autoCommit = true
    commitMessageTemplate = "dotfiles: {{ .targetPath }}"
```

### Interactive commit message
```toml
[git]
    autoCommit = true
    commitMessageTemplate = "{{ promptString \"Commit message\" }}"
```

**Decision:** Enable autoCommit for single-user repos. Enable autoPush only after verifying the remote (`chezmoi git -- remote -v`). Skip for team repos or when batching changes.

## 4. Age Encryption

### Setup
```toml
# ~/.config/chezmoi/chezmoi.toml
encryption = "age"
[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age1..."
```

### Generate key pair
```bash
age-keygen -o ~/.config/chezmoi/key.txt
# Copy the public key (age1...) to the recipient field
cat ~/.config/chezmoi/key.txt | grep "^# public key:"
```

### Encrypt a file
```bash
chezmoi add --encrypt ~/.ssh/config
# Stored as: encrypted_dot_ssh_config.age
# Automatically decrypted during apply
```

### Verify encryption works
```bash
chezmoi apply --dry-run    # Should decrypt without error
chezmoi verify             # Verify all encrypted files
```

**Key management:** Store age key in macOS Keychain or 1Password. Never commit the private key to git.

### GPG Alternative
```toml
encryption = "gpg"
[gpg]
    recipient = "my-key-id"
```

**Decision:** Use age (simpler, modern) unless you already have GPG infrastructure. Always encrypt files containing secrets (API keys, SSH keys, tokens).

## 5. File Format Options

Chezmoi supports TOML, YAML, and JSON for config and data:

**YAML config:**
```yaml
# ~/.config/chezmoi/chezmoi.yaml
data:
  name: John Doe
  email: john@example.com
encryption: age
age:
  identity: ~/.config/chezmoi/key.txt
  recipient: age1abc...
```

**Mixed data formats:**
```
.chezmoidata/
├── config.json       # JSON
├── packages.yaml     # YAML
└── work.toml         # TOML
```
All formats supported in the same directory. Files load in lexical order.

## 6. Advanced Ignore Patterns

**.chezmoiignore.tmpl** (template-aware):
```go
README.md
*.log
LICENSE

{{- if ne .chezmoi.hostname "work-laptop" }}
.work-config
{{- end }}

{{- if eq .chezmoi.os "windows" }}
Documents/*
!Documents/*PowerShell/
{{- end }}
```

## Decision Trees

**Should I use .chezmoiroot?**
- YES: dotfiles in subdirectory, monorepo
- NO: dotfiles at repo root (default layout)

**Should I enable autoCommit?**
- YES: single user, want always-synced repo
- NO: team dotfiles, prefer explicit commits

**Should I encrypt?**
- YES: dotfiles contain secrets
- NO: public dotfiles only

**Should I use .chezmoiremove?**
- YES: deprecated files need cleanup on apply
- NO: all cleanup already done manually

## Related Skills

- **chezmoi-config** — Basic template syntax and configuration
- **chezmoi-workflows** — Daily operations
- **chezmoi-troubleshooting** — Debug advanced config issues
- **chezmoi-agent-config** — AI agent config patterns

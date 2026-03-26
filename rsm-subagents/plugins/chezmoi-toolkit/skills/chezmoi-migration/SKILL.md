---
name: chezmoi-migration
description: This skill should be used when the user asks to adopt chezmoi on new machines or migrate from other dotfile managers, such as setting up dotfiles on a new Mac, doing a fresh chezmoi install, migrating from stow/yadm/bare-git repos, setting up multi-account GitHub SSH, deploying dotfiles in CI/Docker with one-shot mode, or onboarding team members to chezmoi.
---

# Chezmoi Migration & Onboarding

Workflows for adopting chezmoi on new machines and migrating from other dotfile managers.

## 1. Fresh Install (New Machine)

### One-line install + apply
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply $GITHUB_USERNAME
```
This installs chezmoi, clones `github.com/$USER/dotfiles`, and applies.

### Step-by-step install
```bash
brew install chezmoi                          # 1. Install
chezmoi init https://github.com/$USER/dotfiles.git  # 2. Clone repo
chezmoi diff                                  # 3. Review changes (SAFE)
chezmoi apply                                 # 4. Deploy (user responsibility)
chezmoi doctor                                # 5. Verify setup
```

### Post-install configuration
```toml
# ~/.config/chezmoi/chezmoi.toml
[git]
    autoCommit = true    # Auto-commit after chezmoi add/edit
    autoPush = true      # Auto-push after commit (optional)
```

## 2. Migration from Stow

**Overview:** Stow uses symlinks; chezmoi uses file copies with templates.

```bash
# 1. List stow packages
ls ~/.dotfiles/

# 2. Add each managed file to chezmoi
for pkg in ~/.dotfiles/*/; do
    for file in "$pkg".*; do
        target="$HOME/$(basename "$file")"
        [ -L "$target" ] && chezmoi add "$target"
    done
done

# 3. Review what was added
chezmoi managed

# 4. Convert platform-specific configs to templates
chezmoi cd
# Edit files: add {{ if eq .chezmoi.os "darwin" }} conditionals

# 5. Commit and push
chezmoi git -- add -A
chezmoi git -- commit -m "Import from stow"
chezmoi git -- push

# 6. Remove stow (symlinks replaced by actual files after apply)
brew uninstall stow
```

## 3. Migration from Yadm

```bash
# 1. Export yadm-managed files
yadm list > /tmp/yadm-files.txt

# 2. Add each to chezmoi
while IFS= read -r file; do
    chezmoi add "$HOME/$file"
done < /tmp/yadm-files.txt

# 3. Handle yadm encryption → chezmoi age
# If using yadm encrypt: re-encrypt with chezmoi age
chezmoi add --encrypt ~/.ssh/config

# 4. Verify and commit
chezmoi diff
chezmoi git -- add -A && chezmoi git -- commit -m "Import from yadm"
```

## 4. Migration from Bare Git Repo

```bash
# 1. Clone bare repo temporarily
git clone --bare https://github.com/$USER/dotfiles.git /tmp/dotfiles-bare
git --git-dir=/tmp/dotfiles-bare --work-tree=/tmp/dotfiles-export checkout

# 2. Copy exported files to $HOME (so chezmoi add can find them)
for file in /tmp/dotfiles-export/.*; do
    [ -f "$file" ] && cp "$file" "$HOME/$(basename "$file")"
done

# 3. Initialize chezmoi and add the files
chezmoi init
for file in /tmp/dotfiles-export/.*; do
    [ -f "$file" ] && chezmoi add "$HOME/$(basename "$file")"
done

# 4. Clean up export directory
rm -rf /tmp/dotfiles-bare /tmp/dotfiles-export
```

## 5. Multi-Account GitHub SSH

**Problem:** Different SSH keys for personal and work GitHub accounts.

```bash
# ~/.ssh/config
Host github.com-personal
    HostName github.com
    IdentityFile ~/.ssh/id_personal
    User git

Host github.com-work
    HostName github.com
    IdentityFile ~/.ssh/id_work
    User git
```

```bash
# Personal machine
chezmoi init git@github.com-personal:user/dotfiles.git

# Work machine
chezmoi init git@github.com-work:workorg/dotfiles.git
```

**Alternative: Override in chezmoi config**
```toml
[git]
    command = "git"
    args = ["-c", "core.sshCommand=ssh -i ~/.ssh/id_work"]
```

## 6. One-Shot Mode (CI/Docker)

For ephemeral environments — install, apply, then clean up:

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --one-shot $GITHUB_USERNAME
```

This does: install → init → apply → remove chezmoi binary and source.

**In Dockerfile:**
```dockerfile
RUN sh -c "$(curl -fsLS get.chezmoi.io)" -- init --one-shot github-username
```

## 7. Team Onboarding

**Shared team dotfiles with per-role customization:**

```toml
# .chezmoi.toml.tmpl
[data]
    name = "{{ promptString "Your name" }}"
    role = "{{ promptChoice "Your role" (list "dev" "devops" "design") }}"
```

```go
// dot_zshrc.tmpl
{{ if eq .role "devops" -}}
source ~/.config/zsh/devops-tools.zsh
{{ end -}}
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Network error on init | Bad URL or no SSH key | Verify repo URL, `ssh-add -l` |
| Stow symlinks conflict | Symlinks not replaced | Remove symlinks first, then `chezmoi apply` |
| Wrong SSH key used | SSH config routing | `ssh -T git@github.com` to verify |
| One-shot didn't clean up | Interrupted process | Manual: `rm -rf ~/.local/share/chezmoi` |

## Related Skills

- **chezmoi-workflows** — Daily operations after migration
- **chezmoi-config** — Template syntax reference
- **chezmoi-troubleshooting** — Diagnose migration issues
- **chezmoi-agent-config** — Set up AI agent config distribution

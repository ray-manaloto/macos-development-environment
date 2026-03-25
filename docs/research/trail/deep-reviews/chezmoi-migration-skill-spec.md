# Chezmoi Migration & Onboarding Skill Specification

**Finding ID:** finding-chezmoi-plugin-skills-gaps (HIGH PRIORITY)

## Purpose

Comprehensive skill for adopting chezmoi on new machines and migrating from other dotfile managers. Fills gap: no current skill covers onboarding workflows or migration from stow/yadm/bare git setups.

## Use Cases Addressed

1. **New Machine Setup**
   - "I want to set up my dotfiles on a new Mac"
   - "Install chezmoi and my dotfiles in one command"
   - "First time using chezmoi"

2. **Migration from Other Tools**
   - "I'm using stow, how do I switch to chezmoi?"
   - "Migrate from yadm to chezmoi"
   - "Convert bare git repo to chezmoi"

3. **Multi-Account GitHub Setup**
   - "I need dotfiles on personal and work machines"
   - "Different GitHub accounts for different repos"
   - "SSH key switching for dotfiles"

4. **Team/Shared Dotfiles**
   - "Set up shared team dotfiles"
   - "Different configs per role (dev, devops, design)"
   - "Onboard new team members"

5. **One-Shot / Ephemeral Environments**
   - "Install dotfiles in CI/Docker without leaving traces"
   - "Temporary environment setup (containers)"

## Skill Structure (280 lines)

### Part 1: Fresh Install Workflow (90 lines)

**Scenario: New machine with GitHub dotfiles repo**

1. Install chezmoi
   ```bash
   brew install chezmoi  # or native binary
   ```

2. Initialize from repo
   ```bash
   chezmoi init https://github.com/$USER/dotfiles.git
   chezmoi diff          # Review changes
   chezmoi apply         # Deploy dotfiles
   ```

3. Verify setup
   ```bash
   chezmoi doctor        # Check for issues
   chezmoi verify        # Confirm all files match source
   ```

4. Optional: Auto-commit & push setup
   ```bash
   # Edit ~/.config/chezmoi/chezmoi.toml
   # [git]
   #   autoCommit = true
   #   autoPush = true
   ```

**One-line install + apply (if repo is github.com/$USER/dotfiles):**
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply $GITHUB_USERNAME
```

### Part 2: Migration Workflows (130 lines)

**Migration Path A: Stow → Chezmoi**

1. Export stow packages as chezmoi templates:
   ```bash
   # Manual process: For each stow package,
   # add files to chezmoi source as templates
   for pkg in ~/.dotfiles/*/; do
       chezmoi add "~/${pkg##*/}"  # e.g., ~/.zshrc
   done
   chezmoi git -- commit -m "Import from stow"
   ```

2. Review templates for platform-specific content
   ```bash
   # Stow symlinks may have hardcoded paths
   # Convert to chezmoi templates with conditionals:
   {{ if eq .chezmoi.os "darwin" }}...{{ end }}
   ```

3. Remove stow
   ```bash
   brew uninstall stow
   chezmoi apply          # Replace symlinks with actual files
   ```

**Migration Path B: Yadm → Chezmoi**

1. Export yadm state:
   ```bash
   # yadm stores dotfiles in ~/.local/share/yadm/repo.git
   cd ~/.local/share/yadm
   git clone repo.git ~/chezmoi-import
   cd ~/chezmoi-import
   git ls-tree -r HEAD | awk '{print $4}' > /tmp/yadm-files.txt
   ```

2. Import into chezmoi source:
   ```bash
   chezmoi init ~/chezmoi-import
   # Manually copy files from imported state into chezmoi source
   # Review for .yadm-specific encryption (age/gpg keys)
   ```

3. Test and clean up:
   ```bash
   chezmoi diff
   chezmoi apply
   # Uninstall yadm
   ```

**Migration Path C: Bare Git → Chezmoi**

1. Clone bare repo as chezmoi source:
   ```bash
   mkdir -p ~/.local/share/chezmoi
   git clone --bare https://github.com/$USER/dotfiles.git \
     ~/.local/share/chezmoi/.git
   git --git-dir=~/.local/share/chezmoi/.git \
       --work-tree=~/.local/share/chezmoi checkout
   ```

2. Convert to chezmoi structure:
   - Rename files: `zshrc` → `dot_zshrc` (or `dot_zshrc.tmpl`)
   - Add `.chezmoi.toml.tmpl` for config
   - Update `.gitignore` to exclude `.chezmoi.toml`

3. Test and deploy:
   ```bash
   chezmoi doctor        # Verify structure
   chezmoi apply
   ```

### Part 3: Multi-Account GitHub (80 lines)

**Problem:** One SSH key per GitHub account; need different keys for personal and work dotfiles.

**Solution: SSH Config + Multiple Deploy Keys**

1. Add personal and work SSH identities:
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

2. Clone dotfiles from appropriate account:
   ```bash
   chezmoi init git@github.com-personal:username/dotfiles.git
   ```

3. For work machine, use different SSH identity:
   ```bash
   chezmoi init git@github.com-work:workaccount/dotfiles.git
   ```

4. Update remote in source:
   ```bash
   chezmoi git -- remote set-url origin git@github.com-work:workaccount/dotfiles.git
   chezmoi git -- push -u origin main
   ```

**Alternative: Override SSH key in chezmoi config**
```toml
# ~/.config/chezmoi/chezmoi.toml
[git]
    command = "git"
    args = ["-c", "core.sshCommand=ssh -i ~/.ssh/id_work"]
```

### Part 4: One-Shot Mode (20 lines)

For ephemeral environments (CI, containers, short-lived VMs):

```bash
# Install chezmoi, apply dotfiles, clean up
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --one-shot $GITHUB_USERNAME
```

This does:
1. Install chezmoi
2. Initialize from repo
3. Apply dotfiles
4. Remove chezmoi binary and source directory
5. Leave only deployed files

**Use in Docker:**
```dockerfile
RUN sh -c "$(curl -fsLS get.chezmoi.io)" -- \
    init --one-shot github-username
```

## Integration Points

**Depends On:**
- chezmoi-workflows (prerequisite: understand chezmoi basics)
- chezmoi-config (reference: understand config file structure)

**Consumed By:**
- New users evaluating chezmoi
- Teams onboarding to chezmoi
- Users switching from stow/yadm/bare-git

## Safety Constraints

All migration paths are SAFE (read-only until final `chezmoi apply`):
- Cloning repos: safe
- Reviewing templates: safe
- Testing with `chezmoi diff`: safe
- Final `chezmoi apply`: user responsibility (advised to run after review)

## Common Issues & Fixes

### "chezmoi init failed with network error"
- Check internet connection
- Verify repo URL is correct
- Verify SSH keys are loaded (`ssh-add -l`)

### "Stow files conflict with chezmoi files"
- Remove stow symlinks first
- Run `chezmoi apply` to replace with actual files
- Clean up `~/.dotfiles` or stow directory

### "Wrong SSH key used for GitHub"
- Verify SSH identity with `ssh -T git@github.com`
- Check ~/.ssh/config routing
- Verify key is loaded: `ssh-add -l`

### "One-shot mode didn't clean up"
- Verify chezmoi binary actually ran
- Check `~/.local/share/chezmoi` exists (if one-shot failed)
- Manual cleanup: `rm -rf ~/.local/share/chezmoi ~/.config/chezmoi`

## Related Skills

- **chezmoi-workflows** — daily operations after migration complete
- **chezmoi-config** — understand .chezmoi.toml options
- **chezmoi-troubleshooting** — diagnose migration issues
- **mde-chezmoi-dotfiles** — repo-specific onboarding patterns

## Not Covered

- "How do I write a template?" → chezmoi-config
- "How do I troubleshoot doctor errors?" → chezmoi-troubleshooting
- "How do I set up encryption?" → chezmoi-config
- "How do I manage 50 machines?" → chezmoi-workflows (team strategies)

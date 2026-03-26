# Chezmoi Advanced Configuration Skill Specification

**Finding ID:** finding-chezmoi-plugin-skills-gaps (HIGH PRIORITY)

## Purpose

Reference guide for advanced chezmoi configuration options beyond basic .chezmoi.toml. Fills gap: current skills only cover ~40% of configuration surface area (prompts, basic data); missing monorepo support, cleanup workflows, plugins, git automation, and encryption management.

## Use Cases Addressed

1. **Monorepo & Multi-Repo Setups**
   - "Store dotfiles in subdirectory of larger repo"
   - "Multiple chezmoi repos (personal, work, shared)"
   - ".chezmoiroot for non-standard layouts"

2. **Cleanup & Removal Workflows**
   - "Remove old dotfiles on apply"
   - ".chezmoiremove for managed uninstall"
   - "Clean up symlinks when migrating"

3. **Advanced Git Workflows**
   - "Auto-commit changes to dotfiles"
   - "Auto-push to GitHub"
   - "Custom commit message templates"
   - "Conditional git operations"

4. **Encryption & Secret Management**
   - "Set up and manage age encryption keys"
   - "GPG key rotation"
   - "Encrypt only specific files"

5. **Plugin System & Custom Hooks**
   - "Create custom chezmoi commands"
   - "Hook into apply lifecycle"
   - "Integrate external tools"

6. **Ignore & Target Rules**
   - ".chezmoiignore templating"
   - "Platform-specific ignore rules"
   - "Exclude files from certain machines"

7. **File Format Selection**
   - "Use YAML instead of TOML"
   - "Use JSON for .chezmoidata"
   - "Format conversion"

## Skill Structure (310 lines)

### Part 1: .chezmoiroot for Monorepo (50 lines)

**Problem:** Chezmoi expects source at `~/.local/share/chezmoi`, but you want it elsewhere (subdirectory, monorepo, or non-standard path).

**Solution: .chezmoiroot**

1. Create `.chezmoiroot` file in repo root:
   ```
   ~/.local/share/chezmoi/
   ├── .chezmoiroot
   ├── dotfiles/          # <-- source state is HERE
   │   ├── .chezmoi.toml.tmpl
   │   ├── dot_zshrc
   │   └── ...
   └── README.md
   ```

2. Content of `.chezmoiroot`:
   ```text
   dotfiles
   ```
   (Just the relative path from repo root to source state directory.)

3. Initialize with custom source path:
   ```bash
   chezmoi init --source-dir ~/monorepo/dotfiles https://github.com/user/monorepo.git
   ```

**Use Case: Monorepo**
```
company-infra/
├── terraform/
├── kubernetes/
├── .chezmoiroot        # Contains: "dotfiles-config"
├── dotfiles-config/
│   ├── .chezmoi.toml.tmpl
│   ├── dot_zshrc
│   └── ...
└── README.md
```

### Part 2: .chezmoiremove for Cleanup (60 lines)

**Problem:** When updating dotfiles, need to remove old files that are no longer managed (e.g., deprecated config paths, old shell aliases).

**Solution: .chezmoiremove**

1. Create `.chezmoiremove` (or `.chezmoiremove.tmpl` for templating):
   ```text
   ~/.config/old-tool/config
   ~/.oh-my-zsh/custom/deprecated.zsh
   ~/.vim/old-plugins/*
   ```

2. These files will be DELETED during `chezmoi apply`:
   ```bash
   chezmoi apply
   # Files listed in .chezmoiremove are removed from home directory
   ```

3. Templated version (remove only on certain machines):
   ```go
   {{- if eq .chezmoi.os "darwin" }}
   ~/.kube/config-old
   {{- end }}
   ```

**Safe Testing:**
```bash
chezmoi diff --include=.chezmoiremove
chezmoi apply --dry-run  # Preview what would be removed
```

**Common Patterns:**
- Remove deprecated paths when refactoring
- Clean up old shell frameworks (antigen → zplug migration)
- Remove editor plugin managers when switching (vim-plug → packer.nvim)

### Part 3: Git Automation (80 lines)

**Problem:** Manually committing and pushing dotfile changes is tedious.

**Solution: [git] configuration section**

1. Enable auto-commit:
   ```toml
   [git]
       autoCommit = true
   ```
   - Automatically commits changes after `chezmoi add`/`chezmoi edit`
   - Default message: "changes to `<files>`"

2. Enable auto-push:
   ```toml
   [git]
       autoCommit = true
       autoPush = true
   ```
   - Requires autoCommit (autoPush implies autoCommit)
   - Pushes to remote after commit
   - ⚠️ Be careful: secrets accidentally added will be pushed!

3. Custom commit message:
   ```toml
   [git]
       autoCommit = true
       commitMessageTemplate = "dotfiles: {{ .targetPath }}"
   ```
   Available variables: `.targetPath`, `.sourceFiles`, `.chezmoi.*`

4. Interactive commit message:
   ```toml
   [git]
       autoCommit = true
       commitMessageTemplate = "{{ promptString \"Commit message\" }}"
   ```

5. Commit message from file:
   ```toml
   [git]
       autoCommit = true
       commitMessageTemplateFile = ".commit_template"
   ```
   (Path relative to source directory.)

**Careful Usage:**
```bash
# Review before adding (shows what will be committed)
chezmoi diff

# After edit, review commit message that will be used
chezmoi edit ~/.zshrc  # Prompts for message if using promptString

# If auto-push enabled, commit is automatically pushed
# Verify remote before enabling autoPush for first time
chezmoi git -- remote -v
```

### Part 4: Encryption Setup (60 lines)

**Problem:** Dotfiles may contain secrets; need to encrypt some files.

**Solution: Age or GPG encryption**

1. Enable age encryption in `.chezmoi.toml.tmpl`:
   ```toml
   encryption = "age"
   [age]
       identity = "~/.config/chezmoi/key.txt"
       recipient = "age1..."  # Public key
   ```

2. Generate age key pair:
   ```bash
   age-keygen -o -f ~/.config/chezmoi/key.txt
   cat ~/.config/chezmoi/key.txt | grep "^# public key:"
   ```
   Copy the public key to `recipient` field.

3. Encrypt a file:
   ```bash
   chezmoi add --encrypt ~/.ssh/config
   # File will be stored as: encrypted_dot_ssh_config.age
   # Automatically decrypted during apply
   ```

4. Alternative: GPG encryption:
   ```toml
   encryption = "gpg"
   [gpg]
       recipient = "my-key-id"
   ```

5. Verify encryption works:
   ```bash
   chezmoi apply --dry-run  # Should decrypt without error
   chezmoi verify           # Verify all encrypted files decrypt
   ```

**Key Management:**
- Age key: Keep in Keychain or age-encrypted vault
- GPG: Use existing GPG setup (often already on system)
- Never commit unencrypted .key.txt to GitHub

### Part 5: File Format Options (40 lines)

**Use YAML instead of TOML:**
```bash
# Create ~/.config/chezmoi/chezmoi.yaml
# instead of chezmoi.toml
```

**Example YAML:**
```yaml
data:
  name: John Doe
  email: john@example.com

encryption: age
age:
  identity: ~/.config/chezmoi/key.txt
  recipient: age1abc...
```

**JSON for .chezmoidata:**
```
.chezmoidata/
├── config.json
├── packages.yaml
└── work.toml
```
All formats supported in same directory.

### Part 6: Plugin System (Overview) (20 lines)

**Note:** Plugin system is advanced; links to official docs.

Plugins enable:
- Custom commands (`chezmoi mycommand`)
- Hooks into apply lifecycle
- Integration with external tools

**Not detailed here** — refer to chezmoi plugin documentation and chezmoi-config skill for custom template functions.

## Integration Points

**Depends On:**
- chezmoi-config (basic .chezmoi.toml, template functions)
- chezmoi-workflows (daily operations)

**Consumed By:**
- Advanced users requiring monorepo setup
- Teams needing git automation
- Users managing sensitive data
- mde-chezmoi-dotfiles (can reference for .chezmoiroot patterns)

## Safety Constraints

CAREFUL OPERATIONS:
- `.chezmoiremove` deletes files → use `chezmoi diff` first
- `autoPush = true` pushes immediately → verify remote first
- Encrypted files must have keys available → test with `chezmoi apply --dry-run`

SAFE OPERATIONS:
- Reviewing `.chezmoiremove` with `chezmoi diff --include=.chezmoiremove`
- Testing commits before enabling autoPush
- Key generation (does not modify system files)

## Decision Trees

**Should I use .chezmoiroot?**
- ✓ YES if: dotfiles in subdirectory, monorepo, non-standard path
- ✗ NO if: dotfiles at repo root, using default `~/.local/share/chezmoi`

**Should I enable autoCommit?**
- ✓ YES if: single user, simple workflow, want always-synced repo
- ✗ NO if: team dotfiles, need to batch changes, prefer explicit commits

**Should I use .chezmoiremove?**
- ✓ YES if: deprecated files exist, cleaning up old paths, major refactors
- ✗ NO if: all old files have been manually cleaned, or want explicit deletion

**Should I encrypt?**
- ✓ YES if: dotfiles contain secrets (API keys, SSH keys, tokens)
- ✗ NO if: public dotfiles, no sensitive data

## Related Skills

- **chezmoi-config** — basic configuration, template functions
- **chezmoi-workflows** — daily operations, sync, update
- **chezmoi-troubleshooting** — diagnose advanced config issues
- **chezmoi-template-advanced** — template functions for plugins

## Not Covered

- "How do I write a template?" → chezmoi-config
- "How do I debug a template?" → chezmoi-troubleshooting
- "How do I sync across machines?" → chezmoi-workflows
- "How do I build a plugin?" → chezmoi plugin documentation

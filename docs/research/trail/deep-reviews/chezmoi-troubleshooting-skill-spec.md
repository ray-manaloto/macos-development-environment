# Chezmoi Troubleshooting Skill Specification

**Finding ID:** finding-chezmoi-plugin-skills-gaps (HIGH PRIORITY)

## Purpose

Systematic diagnostic and remediation skill for common chezmoi failures, state issues, and configuration problems. Fills gap: no current skill covers `chezmoi doctor` interpretation, state dump/reset, or diff debugging workflows.

## Use Cases Addressed

1. **Setup Failures**
   - "chezmoi doctor shows errors"
   - "chezmoi init didn't work"
   - "can't initialize on a new machine"

2. **State Problems**
   - "Script should have run but didn't" (run_once state)
   - "Script runs every time instead of once" (run_onchange state)
   - "Need to reset script execution state"

3. **Drift Detection & Resolution**
   - "chezmoi verify failing"
   - "chezmoi diff shows unexpected changes"
   - "What would change if I apply?"

4. **Merge Conflicts**
   - "Git merge conflict in source"
   - "Need to resolve dotfile conflicts"

5. **Version Compatibility**
   - "chezmoi version too old for feature X"
   - ".chezmoiversion enforcement"

## Skill Structure (225 lines)

### Part 1: Doctor Interpretation (85 lines)
- Overview of what `chezmoi doctor` checks
- Table: check name → what to verify → common failures → fix
- Color-coded output explanation (ok, warning, error)
- Examples of doctor output for specific configs

Example table structure:
```
| Check | Expected | Failure Meaning | Fix |
|-------|----------|-----------------|-----|
| git-command | found /opt/homebrew/bin/git | Git not in PATH | brew install git |
| config-file | found ~/.config/chezmoi/chezmoi.toml | Config missing | chezmoi init |
| age-identity | ok (optional) | age not configured | chezmoi doctor & check encryption docs |
| 1password | ok (optional) | op CLI missing | op plugin setup or chezmoi-config skill |
```

### Part 2: State Management (70 lines)
- What `chezmoi state dump` shows
- State buckets: scriptState (run_once), entryState (run_onchange)
- When to reset state (script bug fixes, idempotency issues)
- Commands:
  - `chezmoi state dump` - view current state
  - `chezmoi state delete-bucket --bucket=scriptState` - reset run_once
  - `chezmoi state delete-bucket --bucket=entryState` - reset run_onchange

### Part 3: Diff Debugging (70 lines)
- Interpreting `chezmoi diff` output (file added, modified, removed, mode, permissions)
- `chezmoi diff --exclude` patterns (skip system-managed files)
- `chezmoi diff --include` patterns (inspect specific files)
- Debugging template expansion: `chezmoi execute-template < file.tmpl`
- Comparing computed vs actual state without applying

## Integration Points

**Depends On:**
- chezmoi-config (reference for .chezmoi.toml settings)
- chezmoi-workflows (prerequisite: understand add/apply cycle)

**Consumed By:**
- mde-chezmoi-dotfiles (MDE-specific troubleshooting)
- Any user debugging dotfile setup

## Forbidden Operations (Safety Constraints)

MUST NOT execute:
- `chezmoi apply` (dangerous without user review)
- `chezmoi update` (auto-merge can hide conflicts)

SAFE operations (read-only):
- `chezmoi doctor`
- `chezmoi state dump`
- `chezmoi diff`
- `chezmoi verify`
- `chezmoi execute-template`

## Common Issue Reference

### Run_once Scripts Not Running
- Cause 1: Script already executed (state recorded)
  - Fix: `chezmoi state delete-bucket --bucket=scriptState` + `chezmoi apply`
- Cause 2: Script error on first run (state FAILED)
  - Fix: Inspect script, fix bug, delete state, rerun
- Cause 3: Script condition prevents execution
  - Debug: `chezmoi execute-template < script.sh.tmpl`

### Diff Shows Unexpected Changes
- Cause 1: Template syntax error
  - Debug: `chezmoi execute-template < file.tmpl`
- Cause 2: Data variable mismatch
  - Debug: `chezmoi data` and review `.chezmoidata/` files
- Cause 3: Local file edited manually (drift)
  - Fix: Manual resolution or `chezmoi apply --force`

### Doctor Showing Warnings
- For optional tools (age, gpg, 1Password):
  - OK to ignore unless you use encryption/secrets
- For required tools (git, config-file):
  - Must fix before chezmoi can operate

## Related Skills

- **chezmoi-config** — what each .chezmoi.toml option does (use to understand doctor output)
- **chezmoi-workflows** — daily use patterns (prerequisite understanding)
- **chezmoi-migration** — setup issues specific to new machines
- **mde-chezmoi-dotfiles** — repo-specific troubleshooting

## Not Covered

- "How do I write a template?" → chezmoi-config
- "How do I sync my dotfiles?" → chezmoi-workflows
- "How do I migrate from stow?" → chezmoi-migration
- "How do I set up encryption?" → chezmoi-config

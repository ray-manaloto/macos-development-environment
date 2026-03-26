---
name: chezmoi-troubleshooting
description: This skill should be used when the user encounters chezmoi failures, state issues, or configuration problems, such as when chezmoi doctor shows errors, scripts don't run as expected, chezmoi verify fails, chezmoi diff shows unexpected changes, state needs resetting, or merge conflicts occur in chezmoi source.
---

# Chezmoi Troubleshooting

Systematic diagnostic workflows for chezmoi failures, state corruption, drift, and configuration problems.

## Safety Constraints

**SAFE operations only — never modify the system without user approval:**
- `chezmoi doctor` — Full diagnostic
- `chezmoi state dump` — View script execution state
- `chezmoi diff` — Preview what would change
- `chezmoi verify` — Check files match source
- `chezmoi execute-template` — Preview template output
- `chezmoi data` — View template variables

**FORBIDDEN without explicit approval:** `chezmoi apply`, `chezmoi update`

## 1. Doctor Interpretation

Run `chezmoi doctor` and interpret the output:

| Check | Expected | Failure Meaning | Fix |
|-------|----------|-----------------|-----|
| version | latest | Outdated chezmoi | `brew upgrade chezmoi` |
| config-file | found path | Config missing | `chezmoi init` or create manually |
| source-dir | git working tree (clean) | Source dirty or not git | `chezmoi cd && git status` |
| git-command | found path | Git not in PATH | Install git via mise/brew |
| edit-command | found path | Editor not configured | Set `$EDITOR` or configure in chezmoi.toml |
| 1password | found path (optional) | op CLI missing | Only needed if using 1Password templates |
| age | found path (optional) | age not installed | Only needed if using age encryption |
| gpg | found path (optional) | gpg not found | Only needed if using GPG encryption |

**Filter for problems only:**
```bash
chezmoi doctor | grep -v "^ok"
```

**Color codes:** `ok` = green (pass), `warning` = yellow (optional), `error` = red (must fix)

## 2. State Management

Chezmoi tracks script execution in two state buckets:

| Bucket | Controls | When to Reset |
|--------|----------|---------------|
| `scriptState` | `run_once_*` scripts | Script was fixed after failed first run |
| `entryState` | `run_onchange_*` scripts | Script content hash mismatch |

**View current state:**
```bash
chezmoi state dump
```

**Reset run_once state** (scripts will re-run on next apply):
```bash
chezmoi state delete-bucket --bucket=scriptState
```

**Reset run_onchange state** (both run_once and run_onchange are in scriptState):
```bash
chezmoi state delete-bucket --bucket=scriptState
```
Note: `entryState` tracks managed FILE state, not scripts. Deleting `entryState`
would force a full re-apply of all managed files — use with extreme caution.

### Common State Issues

**run_once script doesn't run:**
1. Check if already executed: `chezmoi state dump | grep script_name`
2. If state exists but script was fixed: reset scriptState bucket
3. If template condition blocks it: `chezmoi execute-template < script.sh.tmpl`

**run_onchange runs every time:**
1. Check for non-deterministic template output (timestamps, random values)
2. Verify data inputs are stable: `chezmoi data`
3. Reset entryState and re-apply

## 3. Diff Debugging

**Interpret diff output:**
```bash
chezmoi diff                          # All changes
chezmoi diff ~/.zshrc                 # Single file
chezmoi diff --exclude=scripts        # Skip scripts
chezmoi diff --include=files          # Files only
```

**Unexpected changes — common causes:**

| Symptom | Cause | Debug Command |
|---------|-------|---------------|
| Template renders wrong | Syntax error | `chezmoi execute-template < file.tmpl` |
| Wrong variable value | Data mismatch | `chezmoi data \| grep variable_name` |
| File appears modified | Local manual edit (drift) | `chezmoi verify` to confirm |
| Permission changes | Mode mismatch | Check source file prefix (`executable_`, `private_`) |

**Debug template expansion:**
```bash
# Preview what a template would render to
chezmoi execute-template < "$(chezmoi source-path)/dot_zshrc.tmpl"

# Compare with deployed file
diff <(chezmoi execute-template < "$(chezmoi source-path)/dot_zshrc.tmpl") ~/.zshrc
```

## 4. Merge Conflict Resolution

```bash
chezmoi cd                            # Enter source directory
git status                            # See conflicted files
git diff                              # Review conflicts
# Manually edit conflicted files
git add <resolved-files>
git commit -m "Resolve merge conflict"
# Then: chezmoi diff to verify, chezmoi apply to deploy
```

## 5. Version Compatibility

**Enforce minimum version** with `.chezmoiversion`:
```
2.40.0
```
Place in source root. Chezmoi will refuse to operate if version is too old.

## Diagnostic Flowchart

1. Start: `chezmoi doctor` — any errors? Fix those first
2. Then: `chezmoi verify` — any drift? Review with `chezmoi diff`
3. Then: `chezmoi state dump` — any stuck scripts? Reset relevant bucket
4. Then: `chezmoi execute-template` — template rendering correctly?
5. Still broken? Check `chezmoi data` for variable issues

## Related Skills

- **chezmoi-config** — Template syntax and configuration reference
- **chezmoi-workflows** — Daily operations (prerequisite understanding)
- **chezmoi-migration** — Setup issues on new machines
- **chezmoi-advanced-config** — Encryption, git automation issues

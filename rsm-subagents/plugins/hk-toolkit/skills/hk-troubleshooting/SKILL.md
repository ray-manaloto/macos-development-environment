---
name: hk-troubleshooting
description: >
  Debug and fix hk hook failures including stash restoration errors, step failures,
  environment issues, and configuration problems. Use when pre-commit hooks fail,
  when hk behaves unexpectedly, or when hooks pass/fail inconsistently.
---

# hk Troubleshooting

## Self-Improving Debug Protocol

Follow this cycle iteratively until the issue is resolved:

### 1. Gather Evidence

```bash
# Effective config
hk config dump --json

# Specific setting source
hk config explain stash
hk config explain stash_untracked

# Validate config syntax
hk validate

# Version check
hk --version

# Verbose run
hk run pre-commit --verbose

# Trace for performance
hk run pre-commit --trace
```

### 2. Common Failure Patterns

#### Stash Restore Failure

**Symptom**: `fatal: path '<file>' exists on disk, but not in 'stash@{0}^1'`

**Root cause**: `stash_untracked=true` (default) includes ALL untracked files in the stash.
When new files are staged but don't exist in the prior commit tree, git can't find them
for restoration.

**Fix**:
```bash
git config --local hk.stashUntracked false
```

**Why this is safe**: Hooks only check staged files. Untracked files don't affect hook results.

**If stash is stuck**: `git stash drop` to clear the preserved stash.

#### Hook Passes But Manual Run Fails

**Check these in order**:
1. **Stash behavior**: Hook sees only staged files, manual sees everything
2. **exclude patterns**: hk.pkl excludes may differ from tool config
3. **PATH**: hk may not find mise-managed tools — check `mise = true` in config
4. **Working directory**: Hook runs from repo root, manual may not

#### Step Timeout

**Default timeout**: None (steps run until completion)
**Fix**: Add timeout to step definition or split into smaller steps.

#### Permission Denied on Hook Scripts

```bash
chmod +x .git/hooks/pre-commit
hk install
```

### 3. Nuclear Options (last resort)

```bash
# Skip hooks for one commit (document why!)
git commit --no-verify -m "message"

# Reinstall hooks
hk uninstall && hk install

# Reset hk state
rm -rf .git/hk/
```

### 4. Report Upstream

If the issue is in hk itself:
```bash
gh issue create --repo jdx/hk --title "<title>" --body "<reproduction steps>"
```

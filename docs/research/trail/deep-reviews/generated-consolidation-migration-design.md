# Migration Design: .generated/ Consolidation

**Author:** migration-designer agent
**Date:** 2026-03-26
**Status:** DESIGN (ready for review)

---

## 1. Directory Layout

```
.generated/
├── remember/           ← symlink target for .remember → .generated/remember
│   ├── logs/
│   │   └── autonomous/
│   ├── tmp/
│   ├── .gitignore      (contains '*')
│   ├── now.md
│   ├── today-YYYY-MM-DD.md
│   ├── recent.md
│   ├── archive.md
│   ├── core-memories.md
│   └── remember.md
├── artifacts/          ← current .artifacts/ contents
│   ├── agent-state.jsonl
│   ├── compact-events.jsonl
│   ├── daily-totals.json
│   ├── edit-outcomes.jsonl
│   ├── mde-events.jsonl
│   ├── statusline-events.jsonl
│   ├── statusline-mode
│   ├── statusline-widgets.json
│   └── reference-mirror/
└── reports/            ← current reports/ contents
    ├── agent-policy/
    ├── mde-autoresearch/
    ├── mde-domain-sdlc/
    └── ...
```

## 2. Migration Module

### Location
`src/mde/migrate/generated_consolidation.py`

Also create `src/mde/migrate/__init__.py`.

### CLI Integration
Add to cli.py dispatch table via new `migrate` subcommand:

```
uv run mde-py migrate consolidate-generated [--dry-run] [--backup] [--verify]
```

**Do NOT edit cli.py directly for this.** Instead, follow the pattern used by `research` and `observability` — add a `src/mde/migrate/cli.py` with an `add_subparsers()` function, and import it in `cli.py`'s `_build_parser()`.

### Flags
- `--dry-run`: Print planned operations, create nothing
- `--backup`: Create timestamped tarball of source dirs before moving
- `--verify`: After migration, check all path references resolve

### Idempotency Rules
- If `.generated/` already exists with content, skip already-migrated dirs
- If symlink `.remember → .generated/remember` already exists, skip
- If `.artifacts/` doesn't exist, skip that step (no error)
- If `reports/` doesn't exist, skip that step

## 3. Migration Steps (in order)

### Step 1: Pre-flight Checks
- **What:** Verify no processes hold locks in `.remember/tmp/` or `.artifacts/`
- **What could go wrong:** A background `save-session.sh` holds `.remember/tmp/save.lock`
- **How to verify:** Check for `save.lock`, `consolidation.lock`, `save-session.pid`
- **How to rollback:** N/A (read-only step)

### Step 2: Create Backup (if --backup)
- **What:** `tar czf .generated-migration-backup-{timestamp}.tar.gz .remember .artifacts reports`
- **What could go wrong:** Disk space insufficient; `.artifacts/mde-events.jsonl` can be 10MB+
- **How to verify:** `tar tzf` the backup file
- **How to rollback:** N/A (additive step)

### Step 3: Create .generated/ Directory
- **What:** `mkdir -p .generated/{remember,artifacts,reports}`
- **What could go wrong:** Permission denied
- **How to verify:** `os.path.isdir(".generated/remember")`
- **How to rollback:** `rm -rf .generated/`

### Step 4: Move .artifacts/ → .generated/artifacts/
- **What:** Move all files and subdirectories from `.artifacts/` to `.generated/artifacts/`
- **What could go wrong:** Files in use by statusline hooks writing to `.artifacts/agent-state.jsonl`
- **How to verify:** All files exist in new location, old dir is empty/gone
- **How to rollback:** Move files back to `.artifacts/`
- **Note:** Use `shutil.move()` for each item, not the whole directory (preserves partial state on failure)

### Step 5: Move reports/ → .generated/reports/
- **What:** Move all subdirectories from `reports/` to `.generated/reports/`
- **What could go wrong:** Minimal — reports are read-only historical data
- **How to verify:** All subdirs exist in new location
- **How to rollback:** Move files back to `reports/`

### Step 6: Move .remember/ → .generated/remember/
- **What:** Move all files from `.remember/` to `.generated/remember/`
- **What could go wrong:** Remember plugin writes to `.remember/` during move
- **How to verify:** All files exist in `.generated/remember/`, no orphans
- **How to rollback:** Move files back to `.remember/`
- **Critical:** Must clear any lock files in `tmp/` first

### Step 7: Create .remember Symlink
- **What:** `os.symlink(".generated/remember", ".remember")`
- **What could go wrong:** `.remember` dir still exists (Step 6 incomplete)
- **How to verify:** `os.path.islink(".remember")` and `os.readlink(".remember") == ".generated/remember"`
- **How to rollback:** `os.unlink(".remember")` then restore original directory

### Step 8: Update Path References in src/mde/
- **What:** Update hardcoded `.artifacts/` paths in source code to `.generated/artifacts/`
- **Files affected (16 references in 7 files):**
  - `src/mde/hooks/log_agent_event.py:29` — `_AGENT_STATE_FILE`
  - `src/mde/hooks/log_outcome.py:27` — `_OUTCOME_FILE`
  - `src/mde/hooks/post_compact.py:46` — compact-events.jsonl path
  - `src/mde/statusline/widget_toggle.py:14` — `_WIDGET_CONFIG_FILE`
  - `src/mde/statusline/widgets.py:21` — `_DAILY_TOTALS_FILE`
  - `src/mde/statusline/toggle.py:10` — `_MODE_FILE`
  - `src/mde/statusline/render.py:20-22` — `_MODE_FILE`, `_AGENT_STATE_FILE`, `_EVENT_LOG_FILE`
  - `src/mde/observability.py:146` — `log_file` default
- **What could go wrong:** Missed a reference → file writes to non-existent path
- **How to verify:** `grep -r '\.artifacts' src/mde/` returns 0 results
- **How to rollback:** `git checkout src/mde/` (all changes are in tracked files)

### Step 9: Update .gitignore
- **What:** Replace `.artifacts/`, `reports/` entries with `.generated/`
- **How to verify:** `.generated/` is in .gitignore; old entries removed
- **How to rollback:** `git checkout .gitignore`

## 4. Symlink Strategy

### Key Finding: `data_dir` Config is a Dead Letter

The remember plugin's `config.example.json` documents `data_dir: ".remember"`, but **NO script actually reads this value.** All 4 shell scripts hardcode `$PROJECT/.remember`:

| Script | Hardcoded Path |
|--------|---------------|
| `session-start-hook.sh` | `$PROJECT/.remember/tmp`, `$PROJECT/.remember/core-memories.md`, etc. |
| `save-session.sh` | `REMEMBER_DATA="${PROJECT_DIR}/.remember"` |
| `post-tool-hook.sh` | `$PROJECT/.remember/tmp/last-save.json`, `$PROJECT/.remember/tmp/save-session.pid` |
| `run-consolidation.sh` | `STAGING_DIR="${PROJECT_DIR}/.remember"` |

### Recommended Approach: Symlink

Create `.remember → .generated/remember` symlink. This works because:

1. **Bash scripts follow symlinks transparently** — `$PROJECT/.remember/now.md` resolves through the symlink
2. **Python `Path` objects follow symlinks by default** — no code changes needed for remember paths
3. **`mkdir -p`** works through symlinks
4. **Lock files (noclobber)** work through symlinks
5. **No plugin fork needed** — the plugin continues working unmodified

### Symlink Risks
- `rm -rf .remember` would delete the symlink, not the target (safe)
- `git` ignores symlinks to gitignored dirs (`.generated/` will be gitignored, so this is fine)
- If the symlink is accidentally deleted, the plugin creates a new `.remember/` directory (data split risk — migration module should detect and warn)

### Alternative (NOT recommended): Fork the Plugin
Would require forking `claude-remember`, adding `cfg ".data_dir"` reads to all 4 scripts, maintaining the fork. This is far more work than a symlink.

## 5. .gitignore Updates

### Remove
```
reports/
.artifacts/
.artifacts/reference-mirror/
```

### Add
```
.generated/
```

### Keep (unchanged)
```
.remember is NOT in .gitignore — the plugin creates its own .remember/.gitignore with '*'
```

### Final .gitignore (relevant section)
```gitignore
.DS_Store
firebase-debug.log
.env
fnox.local.toml
node_modules/
.bun/
.generated/
.swarm/
.worktrees/
```

## 6. Verification Plan

### 6.1 Remember Plugin Verification

**SessionStart hook reads memory files:**
```bash
# Simulate what session-start-hook.sh does:
test -f .remember/core-memories.md && echo "OK: core-memories"
test -f .remember/recent.md && echo "OK: recent"
test -f .remember/archive.md && echo "OK: archive"
test -f .remember/remember.md && echo "OK: handoff"
test -d .remember/tmp && echo "OK: tmp dir"
test -d .remember/logs/autonomous && echo "OK: logs dir"
```

**PostToolUse hook writes save logs:**
```bash
# Verify the path resolves through symlink:
touch .remember/logs/autonomous/test-migration.log
test -f .generated/remember/logs/autonomous/test-migration.log && echo "OK: write-through works"
rm .remember/logs/autonomous/test-migration.log
```

**Lock files work through symlink:**
```bash
# noclobber test:
(set -o noclobber; echo $$ > .remember/tmp/test.lock) 2>/dev/null && echo "OK: lock works"
rm -f .remember/tmp/test.lock
```

**`/remember` skill writes handoff note:**
```bash
echo "test" > .remember/remember.md
test -f .generated/remember/remember.md && echo "OK: handoff write-through"
: > .remember/remember.md
```

### 6.2 Artifacts Verification

```bash
# All src/mde/ references should resolve:
for f in .generated/artifacts/agent-state.jsonl \
         .generated/artifacts/edit-outcomes.jsonl \
         .generated/artifacts/compact-events.jsonl \
         .generated/artifacts/daily-totals.json \
         .generated/artifacts/statusline-mode \
         .generated/artifacts/statusline-widgets.json \
         .generated/artifacts/statusline-events.jsonl \
         .generated/artifacts/mde-events.jsonl; do
    test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

### 6.3 Post-Migration Grep Check
```bash
# Should return 0 results:
grep -r '\.artifacts/' src/mde/ | grep -v '\.generated/artifacts'
# Should return only the new paths:
grep -r '\.generated/artifacts' src/mde/
```

## 7. Enforcement

### 7.1 New Policy File: `.claude/rules/generated-code-policy.md`

```markdown
# Generated/Transient Data Policy

- ALL generated, transient, and runtime data MUST go under .generated/
- Subdirectories: remember/ (memory pipeline), artifacts/ (runtime state), reports/ (archived reports)
- .remember/ is a symlink to .generated/remember/ — NEVER delete or replace it with a directory
- The remember plugin writes to .remember/ — do NOT change its paths, the symlink handles redirection
- NEVER commit files under .generated/ — it's gitignored
- If .remember/ exists as a directory (not symlink), run `uv run mde-py migrate consolidate-generated` to fix
- .artifacts/ path references in src/mde/ should use .generated/artifacts/ — grep and fix if found
```

### 7.2 CLAUDE.md Updates

Add to Architecture section:
```
- `.generated/` — All runtime/transient data (gitignored). Subdirs: remember/, artifacts/, reports/
- `.remember` — Symlink to `.generated/remember/` (remember plugin compatibility)
```

### 7.3 No New Hooks Needed

The migration is a one-time CLI command. Ongoing enforcement is handled by:
- `.gitignore` (prevents committing generated data)
- Policy file (prevents agents from creating files in old locations)
- `--verify` flag can be run periodically to check health

## 8. Rollback Plan

### Full Rollback (restore everything)

```bash
# 1. Remove symlink
rm -f .remember

# 2. Move data back
mv .generated/remember .remember
mv .generated/artifacts .artifacts
mv .generated/reports reports

# 3. Remove .generated/ if empty
rmdir .generated 2>/dev/null

# 4. Restore .gitignore and source code
git checkout .gitignore src/mde/

# 5. Remove policy file
rm -f .claude/rules/generated-code-policy.md
```

### Partial Rollback (just remember)

If only the remember plugin has issues:
```bash
rm -f .remember
mv .generated/remember .remember
```
The symlink strategy means this is completely safe — the plugin never knew it was writing through a symlink.

### Rollback from Backup

If `--backup` was used:
```bash
tar xzf .generated-migration-backup-{timestamp}.tar.gz
rm -f .remember  # remove symlink
# .remember/ directory is restored from tarball
```

## 9. Implementation Notes

### Module Structure
```
src/mde/migrate/
├── __init__.py
├── cli.py              # add_subparsers() for 'migrate' command
└── generated_consolidation.py  # main migration logic
```

### Key Implementation Details

1. **Use `pathlib.Path` throughout** — consistent with project conventions
2. **Lock check before move:** Read `.remember/tmp/save.lock` and `.remember/tmp/consolidation.lock` — abort if either exists and PID is alive
3. **Atomic-ish moves:** Use `shutil.move()` per-item, not per-directory, so partial failures leave state inspectable
4. **Symlink must be relative:** `.remember → .generated/remember` (not absolute path) so the repo can be moved
5. **`--dry-run` output format:** Print each planned operation as `[DRY RUN] mv .artifacts/agent-state.jsonl → .generated/artifacts/agent-state.jsonl`
6. **Exit codes:** 0 = success or no-op (idempotent), 1 = error, 2 = lock held (retry later)

### Source Code Changes Required

All changes are simple Path constant updates (`.artifacts/` → `.generated/artifacts/`):

| File | Line | Current | New |
|------|------|---------|-----|
| `hooks/log_agent_event.py` | 29 | `Path(".artifacts/agent-state.jsonl")` | `Path(".generated/artifacts/agent-state.jsonl")` |
| `hooks/log_outcome.py` | 27 | `Path(".artifacts/edit-outcomes.jsonl")` | `Path(".generated/artifacts/edit-outcomes.jsonl")` |
| `hooks/post_compact.py` | 46 | `".artifacts" / "compact-events.jsonl"` | `".generated/artifacts" / "compact-events.jsonl"` |
| `statusline/widget_toggle.py` | 14 | `Path(".artifacts/statusline-widgets.json")` | `Path(".generated/artifacts/statusline-widgets.json")` |
| `statusline/widgets.py` | 21 | `Path(".artifacts/daily-totals.json")` | `Path(".generated/artifacts/daily-totals.json")` |
| `statusline/toggle.py` | 10 | `Path(".artifacts/statusline-mode")` | `Path(".generated/artifacts/statusline-mode")` |
| `statusline/render.py` | 20 | `Path(".artifacts/statusline-mode")` | `Path(".generated/artifacts/statusline-mode")` |
| `statusline/render.py` | 21 | `Path(".artifacts/agent-state.jsonl")` | `Path(".generated/artifacts/agent-state.jsonl")` |
| `statusline/render.py` | 22 | `Path(".artifacts/statusline-events.jsonl")` | `Path(".generated/artifacts/statusline-events.jsonl")` |
| `observability.py` | 146 | `".artifacts/mde-events.jsonl"` | `".generated/artifacts/mde-events.jsonl"` |

No `.remember/` path changes are needed in `src/mde/` — the project's hooks don't reference `.remember` at all (the remember plugin handles its own paths).

## 10. Pre-Migration Cleanup

### Critical: .remember/.gitignore is MISSING

The remember plugin's `.remember/.gitignore` (which should contain `*`) was never created because `save-session.sh` only creates it on first successful save run (line 77). This caused 2,003 autonomous save logs to be tracked by git.

**Step 0 (before migration):**
1. `git rm --cached -r .remember/logs/` — untrack the 2,003 log files
2. `git rm --cached .remember/tmp/save-session.pid` — untrack stale PID file
3. Create `.remember/.gitignore` with `*` content (the plugin will re-create this through the symlink after migration)
4. Commit the cleanup separately before running the migration

### Current .remember/ State (as of 2026-03-26)
- **NO memory summaries exist** — now.md, today-*.md, recent.md, archive.md, core-memories.md are all absent
- `remember.md` exists but is 0 bytes (empty)
- Only content: 7,920 autonomous save logs (2.6MB total) in `logs/autonomous/`
- **Migration risk: EXTREMELY LOW** — no critical data to preserve, just transient logs

This simplifies Step 6 significantly: moving `.remember/` to `.generated/remember/` loses nothing of value. The logs can optionally be deleted rather than moved.

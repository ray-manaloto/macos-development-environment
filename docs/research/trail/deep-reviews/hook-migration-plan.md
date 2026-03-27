# Shell Script to Python Hook Migration Plan

**Date:** 2026-03-25
**Status:** Draft -- awaiting review before implementation

## Background

Project policy (`.claude/rules/no-shell-scripts.md`) requires all automation to
be Python modules in `src/mde/`. Three shell scripts remain in
`rsm-subagents/plugins/` that need migration.

## Current State

### Shell scripts to migrate

| # | Script | Plugin | Hook event | What it does |
|---|--------|--------|-----------|-------------|
| 1 | `mise-toolkit/hooks/scripts/guard-install.sh` | mise-toolkit | PreToolUse (Bash) | Blocks global installs (brew, npm -g, pipx, cargo, etc.) and direnv activation |
| 2 | `chezmoi-toolkit/hooks/scripts/guard-direct-dotfile-edit.sh` | chezmoi-toolkit | PreToolUse (Bash) | Blocks direct edits to chezmoi-managed dotfiles in `~/` |
| 3 | `chezmoi-toolkit/hooks/scripts/remind-chezmoi-commit.sh` | chezmoi-toolkit | PostToolUse (Bash) | Reminds to commit after `chezmoi apply/re-add/add` |

### Existing Python hooks in `src/mde/hooks/`

| Module | CLI subcommand | Hook event | Notes |
|--------|---------------|-----------|-------|
| `guard_install.py` | `guard-install` | PreToolUse | **Already exists** -- partial overlap with script #1 |
| `log_outcome.py` | `log-edit-outcome` | PostToolUse | Existing |
| `log_agent_event.py` | `log-agent-event` | SubagentStart/Stop | Existing |
| `session_start.py` | `session-start` | SessionStart | Existing |
| `post_compact.py` | `post-compact` | PostCompact | Existing |
| `validate_agents.py` | (not in dispatch) | PostToolUse | Existing |
| `team_quality_gates.py` | `team-quality-gate` | PostToolUse | Existing |
| `_common.py` | -- | -- | Shared utilities |
| `agent_frontmatter_model.py` | -- | -- | Pydantic model |
| `__init__.py` | -- | -- | Package docstring |

### How existing Python hooks work

1. Claude Code sends hook JSON to **stdin** (not env vars)
2. The hook reads stdin via `parse_hook_stdin()` from `_common.py`
3. For PreToolUse Bash hooks, the command is at `data["tool_input"]["command"]`
4. The hook returns a JSON dict to stdout with `permissionDecision: "deny"` to block
5. Exit code 0 always (denial is via JSON output, not exit codes)
6. Entry points are registered in `_HOOKS_DISPATCH` in `cli.py` and invoked as
   `uv run mde-py hooks <subcommand>`

### How the shell scripts work (differently)

1. Shell scripts read `TOOL_INPUT_COMMAND` from **environment variable**
2. They block via **exit code 1** and print messages to **stderr/stdout**
3. They use `${CLAUDE_PLUGIN_ROOT}` for path resolution
4. They extract first-line only to prevent multi-line bypass

**Key difference:** The shell scripts use `TOOL_INPUT_COMMAND` env var, but the
Python hooks read structured JSON from stdin. The plugin hooks.json dispatches
via `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/...` while the project
settings.json dispatches via `uv run mde-py hooks ...`.

## Migration Plan

### Script 1: guard-install.sh --> guard_install.py (MERGE)

**Status:** Python module already exists with most functionality.

**Gap analysis between shell script and Python module:**

| Feature | Shell script | Python module | Action needed |
|---------|-------------|--------------|---------------|
| brew install | yes | yes | None |
| npm install -g | yes | yes | None |
| npm i -g | yes | yes | None |
| bun add/install -g | yes | yes | None |
| pipx install | yes | yes | None |
| cargo install | yes | yes | None |
| go install | yes | yes | None |
| pip install --user | yes | no (blocks all pip install) | **Verify Python is broader** |
| gem install | yes | no | **Add pattern** |
| pip install -e (allow) | yes | yes (different regex) | None |
| direnv activation block | yes | no | **Add direnv guard** |
| First-line-only defense | yes (bash substring) | no (matches full command) | **Add first-line extraction** |
| yarn global add | no | yes | Python is broader |
| pip3 install | no | yes | Python is broader |
| uv tool install | no | yes | Python is broader |
| uv pip install (allow) | no | yes | Python is broader |
| uv sync (allow) | no | yes | Python is broader |
| uv add (allow) | no | yes | Python is broader |
| mise install (allow) | no | yes | Python is broader |
| brew bundle (allow) | no | yes | Python is broader |

**Changes to `src/mde/hooks/guard_install.py`:**

1. Add `gem install` to `_BLOCK_PATTERNS`
2. Add direnv activation guard (`direnv allow|hook|exec`) to `_BLOCK_PATTERNS`
   or as a separate check
3. Add first-line extraction to `check_install_command()` -- split on `\n` and
   check only the first line, to prevent multi-line bypass
4. Verify `pip install --user` is covered (currently `pip install` without `-e`
   or `.` is blocked, which is broader than `--user` only)

**No new module needed.** The existing guard_install.py is the target.

### Script 2: guard-direct-dotfile-edit.sh --> NEW guard_dotfile_edit.py

**New module:** `src/mde/hooks/guard_dotfile_edit.py`
**New CLI subcommand:** `uv run mde-py hooks guard-dotfile-edit`

**Logic to port:**

1. Read JSON from stdin via `parse_hook_stdin()`
2. Extract `command` from `data["tool_input"]["command"]`
3. Take first line only (multi-line defense)
4. Allow if command starts with `chezmoi edit|cd|add|source-path`
5. Allow if command contains `.local/share/chezmoi`
6. Block patterns for direct editor access to `~/.*`:
   - `vim ~/.`, `nvim ~/.`, `nano ~/.`, `hx ~/.`, `code ~/.`
   - `sed -i.* ~/.`, `perl -pi.* ~/.`, `tee ~/.`
7. Block redirect patterns:
   - `echo .* >> ~/.`, `cat .* > ~/.`, `cp .* ~/.`, `mv .* ~/.`
8. Return JSON deny decision (same schema as guard_install.py)

**Design decisions:**
- Use `re.compile()` patterns like guard_install.py (not bash `=~`)
- Use `_common.parse_hook_stdin()` and `hook_span()` for consistency
- Return `permissionDecision: "deny"` JSON output, not exit code 1

### Script 3: remind-chezmoi-commit.sh --> NEW remind_chezmoi_commit.py

**New module:** `src/mde/hooks/remind_chezmoi_commit.py`
**New CLI subcommand:** `uv run mde-py hooks remind-chezmoi-commit`

**Logic to port:**

1. Read JSON from stdin via `parse_hook_stdin()`
2. Extract `command` from `data["tool_input"]["command"]`
3. Take first line only
4. Only trigger if first line matches `^chezmoi (apply|re-add|add)( |$)`
5. Skip if `--dry-run` is in the command
6. Run `chezmoi source-path` to find the source directory
7. Run `git status --porcelain` in that directory
8. If there are uncommitted changes, print a reminder to stderr
9. Always return exit 0 (informational, never blocks)

**Design decisions:**
- Use `subprocess.run()` for the git/chezmoi commands (like team_quality_gates.py)
- Print reminder to stderr (not stdout) since PostToolUse hooks should not
  interfere with tool output
- No JSON output needed (PostToolUse informational hooks don't need deny decisions)

## CLI Registration Changes

### `src/mde/cli.py` -- add subparsers

```python
# In _build_parser(), add to hooks_sub:
hooks_sub.add_parser("guard-dotfile-edit", help="PreToolUse chezmoi dotfile guard")
hooks_sub.add_parser("remind-chezmoi-commit", help="PostToolUse chezmoi commit reminder")
```

### `src/mde/cli.py` -- add to _HOOKS_DISPATCH

```python
_HOOKS_DISPATCH: dict[str, tuple[str, str]] = {
    # ... existing entries ...
    "guard-dotfile-edit": ("mde.hooks.guard_dotfile_edit", "guard_dotfile_edit"),
    "remind-chezmoi-commit": ("mde.hooks.remind_chezmoi_commit", "remind_chezmoi_commit"),
}
```

## Plugin hooks.json Updates

### mise-toolkit/hooks/hooks.json

**Before:**
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/guard-install.sh",
        "timeout": 5000
      }]
    }]
  }
}
```

**After:**
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "uv run mde-py hooks guard-install",
        "timeout": 5000
      }]
    }]
  }
}
```

**Note:** The project-level `settings.json` ALREADY has `guard-install` via
`uv run mde-py hooks guard-install`. This creates a **duplicate invocation** --
both the plugin hook and the project hook fire on PreToolUse/Bash. After
migration, we should either:
- (a) Remove the plugin hook entry entirely (since settings.json already covers it), OR
- (b) Remove the settings.json entry and keep only the plugin

**Recommendation:** Option (a) -- remove the PreToolUse section from
`mise-toolkit/hooks/hooks.json` entirely, since `settings.json` already
dispatches to the Python module. The plugin's guard-install.sh was the
*original* and settings.json was the *migration target*. With the shell script
deleted, the plugin hook entry pointing to it would break anyway.

### chezmoi-toolkit/hooks/hooks.json

**Before:**
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/guard-direct-dotfile-edit.sh",
        "timeout": 5000
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/remind-chezmoi-commit.sh",
        "timeout": 3000
      }]
    }]
  }
}
```

**After (Option A -- move to settings.json):**
```json
{
  "hooks": {}
}
```

And add to `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      // existing guard-install entry...
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "uv run mde-py hooks guard-dotfile-edit"
        }]
      }
    ],
    "PostToolUse": [
      // existing log-edit-outcome entry...
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "uv run mde-py hooks remind-chezmoi-commit"
        }]
      }
    ]
  }
}
```

**After (Option B -- keep in plugin hooks.json):**
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "uv run mde-py hooks guard-dotfile-edit",
        "timeout": 5000
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "uv run mde-py hooks remind-chezmoi-commit",
        "timeout": 3000
      }]
    }]
  }
}
```

**Recommendation:** Option A (centralize in settings.json) for consistency with
how guard-install already works. This also avoids the `uv run` dependency
problem -- plugins may be used in contexts where `uv` is not available, but
settings.json is always project-local.

## Files to Delete After Migration

1. `rsm-subagents/plugins/mise-toolkit/hooks/scripts/guard-install.sh`
2. `rsm-subagents/plugins/chezmoi-toolkit/hooks/scripts/guard-direct-dotfile-edit.sh`
3. `rsm-subagents/plugins/chezmoi-toolkit/hooks/scripts/remind-chezmoi-commit.sh`
4. `rsm-subagents/plugins/mise-toolkit/hooks/scripts/` (directory, if empty)
5. `rsm-subagents/plugins/chezmoi-toolkit/hooks/scripts/` (directory, if empty)

## Test Plan (TDD)

Following the TDD skill, tests must be written BEFORE implementation.

### Tests for guard_install.py additions

In `tests/test_guard_install.py`, add:

1. `test_blocks_gem_install` -- `gem install rails` should be blocked
2. `test_blocks_direnv_allow` -- `direnv allow` should be blocked
3. `test_blocks_direnv_hook` -- `direnv hook bash` should be blocked
4. `test_allows_direnv_in_comment` -- normal commands mentioning direnv should pass
5. `test_multiline_bypass_prevented` -- `ls\nbrew install jq` should check
   first line only and pass (the dangerous command is on line 2)

### Tests for guard_dotfile_edit.py (new)

In `tests/test_guard_dotfile_edit.py`:

1. `test_blocks_vim_dotfile` -- `vim ~/.bashrc` should be blocked
2. `test_blocks_nvim_dotfile` -- `nvim ~/.zshrc` should be blocked
3. `test_blocks_cp_to_dotfile` -- `cp foo ~/.gitconfig` should be blocked
4. `test_blocks_echo_append_dotfile` -- `echo foo >> ~/.bashrc` should be blocked
5. `test_allows_chezmoi_edit` -- `chezmoi edit ~/.bashrc` should pass
6. `test_allows_chezmoi_source_path` -- edits in `.local/share/chezmoi` should pass
7. `test_allows_unrelated_command` -- `git status` should pass
8. `test_allows_vim_non_dotfile` -- `vim /tmp/test.py` should pass
9. `test_multiline_bypass_prevented` -- multi-line command, dangerous on line 2
10. `test_empty_command` -- empty command should pass
11. `test_hook_entry_point` -- full stdin/stdout integration via `guard_dotfile_edit()`

### Tests for remind_chezmoi_commit.py (new)

In `tests/test_remind_chezmoi_commit.py`:

1. `test_triggers_on_chezmoi_apply` -- should check for uncommitted changes
2. `test_triggers_on_chezmoi_re_add` -- should trigger
3. `test_ignores_non_chezmoi_commands` -- `git status` should no-op
4. `test_ignores_chezmoi_diff` -- `chezmoi diff` should not trigger
5. `test_skips_dry_run` -- `chezmoi apply --dry-run` should not trigger
6. `test_handles_missing_source_dir` -- graceful when `chezmoi source-path` fails
7. `test_no_output_when_clean` -- no reminder if git status is clean
8. `test_reminder_on_dirty_source` -- prints reminder if uncommitted changes exist
9. `test_hook_entry_point` -- full stdin/stdout integration

## Edge Cases

### CLAUDE_PLUGIN_ROOT

The shell scripts use `${CLAUDE_PLUGIN_ROOT}` for path resolution. The Python
modules do not need this since they are invoked as `uv run mde-py hooks ...`
which resolves paths via the Python package. No changes needed.

### Duplicate guard-install invocation

Currently BOTH `settings.json` and `mise-toolkit/hooks/hooks.json` register a
PreToolUse guard for Bash commands. The settings.json calls the Python module;
the plugin calls the shell script. After migration, only one should remain.

### Plugin portability

If the plugins are ever used outside this project (e.g., published to a
marketplace), the `uv run mde-py` dependency would break. The current migration
assumes these plugins are project-local only. If marketplace publishing is
planned, the hooks should stay in the plugin with their own implementation (but
still as Python, not shell).

### remind-chezmoi-commit subprocess calls

The Python version will call `chezmoi source-path` and `git status --porcelain`
via `subprocess.run()`. Tests should mock these calls (like
`test_team_quality_gates.py` does) to avoid requiring chezmoi/git in the test
environment.

## Implementation Order

1. Write failing tests for guard_install.py additions (gem, direnv, multiline)
2. Implement guard_install.py additions -- make tests pass
3. Write failing tests for guard_dotfile_edit.py
4. Implement guard_dotfile_edit.py -- make tests pass
5. Write failing tests for remind_chezmoi_commit.py
6. Implement remind_chezmoi_commit.py -- make tests pass
7. Register new subcommands in cli.py (subparsers + dispatch)
8. Update hooks.json files (mise-toolkit + chezmoi-toolkit)
9. Update settings.json (add new hook entries)
10. Delete shell scripts
11. Run `uv run mde-py quality` (full 6-check gate)
12. Commit

## Update to __init__.py

The `src/mde/hooks/__init__.py` docstring should be updated to list the new
subcommands:

```python
"""Claude Code hook handlers for the mde CLI.

Subcommands (dispatched via _HOOKS_DISPATCH in cli.py):
- guard-install: PreToolUse install guard (exit 2 blocks)
- guard-dotfile-edit: PreToolUse chezmoi dotfile guard (deny via JSON)
- remind-chezmoi-commit: PostToolUse chezmoi commit reminder (informational)
- log-edit-outcome: PostToolUse logger (always exit 0)
- log-agent-event: SubagentStart/SubagentStop logger (always exit 0)
- session-start: SessionStart context setup (always exit 0)
- post-compact: PostCompact research state save (always exit 0)
- validate-agents: PostToolUse validator for .claude/agents/ frontmatter (exit 1 blocks)
- team-quality-gate: Per-team quality gate validation (exit 1 on failure)
"""
```

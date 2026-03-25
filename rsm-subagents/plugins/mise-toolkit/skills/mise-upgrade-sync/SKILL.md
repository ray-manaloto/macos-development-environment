---
name: mise-upgrade-sync
description: >
  This skill should be used when the user asks to "upgrade mise tools", "check for
  outdated tools", "clean up old versions", "sync from nvm/pyenv/rbenv", "run mise
  doctor", "self-update mise", "prune unused tools", or mentions mise upgrade,
  mise outdated, mise prune, mise sync, mise self-update, mise doctor, mise prepare,
  or mise watch.
---

# Mise Upgrade, Sync & Health

Manage tool upgrades, health checks, version syncing, and cleanup workflows.

## Health Checks

```bash
mise doctor                     # Full health check
mise doctor --json              # JSON output for automation
mise outdated                   # Show outdated tools
mise prepare                    # Ensure dependencies are ready (experimental)
mise prepare --explain          # Show what prepare would do
```

### What `mise doctor` Checks

- PATH precedence (mise shims before other tool paths)
- Plugin installation state
- Config file presence and trust status
- Backend availability
- Shell activation status
- Self-update availability

## Upgrade Workflow

```bash
mise outdated                   # 1. Identify outdated tools
mise upgrade                    # 2. Upgrade all outdated tools
mise upgrade node               # 2a. Or upgrade specific tool
mise upgrade --interactive      # 2b. Or choose interactively
mise lock                       # 3. Update lockfile
mise reshim                     # 4. Update PATH shims
mise doctor                     # 5. Verify health
```

## Self-Update

```bash
mise self-update                # Update mise itself
mise self-update --yes          # Skip confirmation
mise self-update --no-plugins   # Don't auto-update plugins
mise --version                  # Check current version
```

Note: `self-update` only works if mise was not installed via a package manager (brew, apt, etc.).

## Cleanup

```bash
mise prune                      # Remove unused tool versions
mise prune --dry-run            # Preview what would be removed
mise cache clear                # Clear download cache
```

## Sync from Other Version Managers

Migrate from nvm, pyenv, or rbenv by symlinking their installed versions into mise:

```bash
mise sync node                  # Import nvm-installed node versions
mise sync python                # Import pyenv-installed python versions
mise sync ruby                  # Import rbenv-installed ruby versions
```

## Watch Mode

Re-run tasks automatically when files change:

```bash
mise watch build                # Watch and re-run build task
mise watch test                 # Watch and re-run tests
mise watch build ::: test       # Watch multiple tasks in parallel
```

Requires `watchexec`: `mise use -g watchexec@latest`

## Lockfile Management

```bash
mise lock                       # Update lockfile checksums and URLs
mise install --locked           # Install only from lockfile (no API calls)
```

Run `mise lock` after ANY config change. Use `--locked` in CI for reproducible builds.

## Anti-Patterns

- Never skip `mise lock` after config changes — stale lockfiles cause CI failures
- Never skip `mise reshim` after tool install — stale shims point to old versions
- Avoid `mise upgrade` without checking `mise outdated` first
- In CI, always use `--locked` to prevent API calls during install

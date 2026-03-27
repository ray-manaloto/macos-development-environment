# Plugin Health Policy

## Validation
- `uv run mde-py validate --plugins-health` checks installation health (broken paths, stale cache, MCP dedup, LSP binaries)
- Included automatically in `validate --all`
- Only **enabled** plugins are checked for LSP binaries (reads `enabledPlugins` from settings.json)
- Zero errors = pass; warnings for stale dirs and MCP collisions

## Error Categories

### 1. Broken Install Paths
**Symptom**: Plugin listed in `installed_plugins.json` but cache directory missing.
**Cause**: Manual deletion, interrupted update, or failed uninstall.
**Fix**:
```bash
# Remove the plugin entry and reinstall
claude plugin uninstall <name>@<marketplace>
claude plugin install <name>@<marketplace>
```

### 2. Stale temp_git_* Directories
**Symptom**: `temp_git_*` dirs under `~/.claude/plugins/cache/<marketplace>/`.
**Cause**: Interrupted `git clone` during plugin install/update.
**Fix**:
```bash
rm -rf ~/.claude/plugins/cache/<marketplace>/temp_git_*
```

### 3. MCP Server Dedup Conflicts
**Symptom**: Multiple plugins or `.mcp.json` register the same MCP server name.
**Cause**: Plugin hooks.json and project .mcp.json both declare a server, or two plugins register the same name.
**Fix**: Disable the duplicate source — either remove from `.mcp.json` or disable the conflicting plugin.

### 4. Missing LSP Binary Commands
**Symptom**: `/plugin` shows `spawn <binary> ENOENT` error for an LSP plugin.
**Cause**: LSP plugin declares a `command` in `.lsp.json` but the binary is not installed on PATH.
**Fix**:
```bash
# Option A: Install the missing binary
mise use <tool>                    # if available in mise registry
npm install -g <package>           # for node-based LSP servers

# Option B: Disable the plugin if you don't need it
# Set to false in .claude/settings.json enabledPlugins
```
**Note**: The validator only checks enabled plugins. Disabling a plugin in settings.json stops both the ENOENT error and the validation warning.

## Investigation Playbook
1. Run `uv run mde-py validate --plugins-health` for automated checks
2. Run `claude plugins list` and look for missing/errored entries
3. Check `~/.claude/plugins/installed_plugins.json` for orphaned entries
4. Check `~/.claude/plugins/cache/` for stale temp dirs
5. If a plugin fails to load: delete its cache (`rm -rf ~/.claude/plugins/cache/<mkt>/<name>`) and reinstall

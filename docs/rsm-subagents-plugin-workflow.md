# rsm-subagents Plugin Development Workflow

## Architecture

The rsm-subagents marketplace is a **local directory marketplace** at `rsm-subagents/` in the project root.

```
rsm-subagents/
  .claude-plugin/
    marketplace.json        # Marketplace manifest listing all plugins
  plugins/
    mise-toolkit/           # Each plugin in its own directory
    chezmoi-toolkit/
    hk-toolkit/
    devcontainer-toolkit/
```

### How Claude Code discovers plugins

1. **Marketplace registration**: `.claude/settings.json` (project) has `extraKnownMarketplaces.rsm-subagents` with `source: "directory"` pointing to the local path
2. **Plugin listing**: `rsm-subagents/.claude-plugin/marketplace.json` lists all available plugins with `source: "./plugins/<name>"`
3. **Enabling**: `enabledPlugins` in either project (`.claude/settings.json`) or user (`~/.claude/settings.json`) settings enables specific plugins
4. **Installation**: `/plugin` command reads the marketplace, copies enabled plugins to cache at `~/.claude/plugins/cache/rsm-subagents/<name>/<version>/`
5. **Tracking**: `~/.claude/plugins/installed_plugins.json` records install path, version, timestamp
6. **Loading**: `/reload-plugins` reads installed plugins from cache and loads skills/agents/hooks

### Key insight

Claude Code does NOT auto-discover plugins from `.claude/plugins/`. That directory is for the project-level plugin _source_. Plugins must flow through the marketplace -> cache -> installed_plugins.json pipeline.

### commands/ vs skills/ (critical distinction)

Plugins can contain two kinds of user-facing content:

| Directory | What it is | How it triggers | Frontmatter |
|-----------|-----------|-----------------|-------------|
| `commands/` | Slash commands | User types `/plugin:command` | `argument-hint`, `allowed-tools` |
| `skills/` | Auto-triggered knowledge | Context match on description keywords | `name`, `description` only |

- **commands/** files are `.md` files directly in the directory (e.g., `commands/setup.md`). They appear as `/plugin-name:setup` in the slash command list.
- **skills/** are subdirectories containing `SKILL.md` (e.g., `skills/setup/SKILL.md`). They load automatically when conversation context matches the description's trigger phrases.

**Common mistake**: Putting a slash command in `skills/` means it never appears as a `/` command. Putting an auto-trigger skill in `commands/` means it never auto-activates.

## Plugin Lifecycle

```
Source (rsm-subagents/plugins/<name>/)
  ↓ /plugin command
Cache (~/.claude/plugins/cache/rsm-subagents/<name>/<version>/)
  ↓ /reload-plugins
Loaded (skills appear as <plugin>:<skill>, agents in agent list)
```

## Developing a New Plugin

### 1. Create plugin structure

```bash
mkdir -p rsm-subagents/plugins/<name>/.claude-plugin
mkdir -p rsm-subagents/plugins/<name>/agents
mkdir -p rsm-subagents/plugins/<name>/skills/<skill-name>/references
```

### 2. Write plugin.json

```json
{
  "name": "<name>",
  "version": "0.1.0",
  "description": "...",
  "author": { "name": "Ray Manaloto" },
  "keywords": [...]
}
```

### 3. Write components (agents, skills)

Follow the plugin-dev skill guidance:
- **Agent**: `agents/<name>.md` with frontmatter (name, description with `<example>` blocks, model, color, tools)
- **Skills**: `skills/<skill>/SKILL.md` with frontmatter (name, description with trigger phrases)
- **References**: `skills/<skill>/references/*.md` for progressive disclosure

### 4. Add to marketplace.json

Edit `rsm-subagents/.claude-plugin/marketplace.json` to add the plugin to the `plugins` array:

```json
{
  "name": "<name>",
  "source": "./plugins/<name>",
  "description": "...",
  "version": "0.1.0",
  "category": "devtools",
  "tags": [...],
  "repository": "https://github.com/ray-manaloto/rsm-subagents"
}
```

### 5. Enable in settings

Add to `.claude/settings.json` (project) or `~/.claude/settings.json` (user):

```json
{
  "enabledPlugins": {
    "<name>@rsm-subagents": true
  }
}
```

### 6. Install and test

```bash
# Install (copies source to cache)
/plugin

# Reload (loads from cache)
/reload-plugins

# Test skill invocation
/<name>:<skill-name>
```

## Validation

### Authoritative validation (required)

```bash
claude plugin validate rsm-subagents/plugins/<name>
```

This is the **single source of truth** for plugin correctness. Run it after every change and before every commit. All other validation methods below are supplementary.

**minVersion gotcha**: Do NOT add `minVersion` or other unrecognized keys to plugin.json. The validator rejects unknown fields and validation will fail silently or with a cryptic error.

### Supplementary: Plugin-dev validator agent

```
"Validate the plugin at rsm-subagents/plugins/<name>/"
```

### Supplementary: Agent validation script

```bash
bash ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/agent-development/scripts/validate-agent.sh rsm-subagents/plugins/<name>/agents/<agent>.md
```

**Note**: The validate-agent.sh script can't parse YAML multi-line scalars (`>` or `|`). False-positive warnings about short descriptions are expected when using these. Claude Code's YAML parser handles them correctly.

### Supplementary: Skill review

Use the plugin-dev skill-reviewer agent:
```
"Review all skills in rsm-subagents/plugins/<name>/skills/"
```

### Reference file check

Verify all files referenced in SKILL.md actually exist:
```bash
for skill_dir in rsm-subagents/plugins/<name>/skills/*/; do
  skill=$(basename "$skill_dir")
  grep -o 'references/[a-z-]*\.md' "$skill_dir/SKILL.md" | sort -u | while read ref; do
    [ -f "$skill_dir/$ref" ] && echo "OK: $skill/$ref" || echo "MISSING: $skill/$ref"
  done
done
```

## Updating an Existing Plugin

1. Edit files in `rsm-subagents/plugins/<name>/`
2. Run `claude plugin validate rsm-subagents/plugins/<name>` to verify changes
3. **Clear the cache** (mandatory): `rm -rf ~/.claude/plugins/cache/rsm-subagents/<name>`
4. Remove from installed_plugins.json (or it will use stale cache)
5. Run `/plugin` then `/reload-plugins`

**Cache clearing is mandatory** after any source change. Without it, `/plugin` installs the stale cached version. Bumping the version in plugin.json is recommended but not strictly required for local directory marketplaces.

## Troubleshooting

### Skills not loading after /reload-plugins

1. Check plugin is in installed_plugins.json: `grep "<name>@rsm-subagents" ~/.claude/plugins/installed_plugins.json`
2. Check cache exists: `ls ~/.claude/plugins/cache/rsm-subagents/<name>/`
3. Check enabled: `grep "<name>@rsm-subagents" ~/.claude/settings.json .claude/settings.json`
4. Check marketplace.json has the plugin entry

### Name collision

If a plugin name matches one from another marketplace, the later-loaded version wins. Use unique names or check for conflicts.

### Stale cache

After updating plugin source, always clear cache before `/plugin`:
```bash
rm -rf ~/.claude/plugins/cache/rsm-subagents/<name>
```

# mise-toolkit

Claude Code plugin for comprehensive mise expertise: tool management, task orchestration, environment configuration, and mise-first policy enforcement.

## Installation

```bash
# From marketplace (when published)
/plugin marketplace add ray-manaloto/mise-toolkit
/plugin install mise-toolkit

# Local development
cc --plugin-dir /path/to/mise-toolkit
```

## Components

### Agent
- **mise-specialist** — Routes to the right skill based on the task

### Skills (8)
| Skill | Purpose |
|-------|---------|
| mise-tool-management | Backend selection, tool add/remove, registry, search |
| mise-tasks | Task orchestration, deps, watch, validate, task-docs |
| mise-enforcement | Policy enforcement, anti-patterns, disallowed installers |
| mise-env-config | [env] section, set/unset, _.file, secrets, multi-env |
| mise-config-settings | mise config/settings/fmt/trust, IDE integration |
| mise-codegen | mise generate (github-action, devcontainer, bootstrap, git-pre-commit, task-docs, task-stubs, config, tool-stub) |
| mise-upgrade-sync | mise upgrade/outdated/prune/sync/self-update/doctor |
| mise-jdx-ecosystem | pitchfork, fnox, hk, usage integration patterns |

### Hooks (1)
- **guard-install** — PreToolUse:Bash hook that blocks direct global installers (brew, npm -g, pipx, etc.) and suggests mise alternatives

## Prerequisites

- [mise](https://mise.jdx.dev/) installed and activated
- Claude Code 2.x+

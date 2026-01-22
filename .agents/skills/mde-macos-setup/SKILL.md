---
name: mde-macos-setup
description: MacBook dev-environment runbook for this repo (mise/bun/uv-first installs, secrets, tmux/oh-my-zsh, SkyPilot/OpenLIT, validation + maintenance).
---

# MacOS Development Environment (MDE) Skill

Use when installing, repairing, or validating the MacBook dev setup maintained in this repo.

## Tooling priority
- Runtime managers: mise → bun (node) → uv (python tools) → pixi (python env) → pip (last resort).
- Avoid npm/yarn global installs; prefer bun global or project deps.
- Keep PATH from templates/oh-my-zsh/aliases.zsh (mise shims, bun, pixi, mde bin).

## One-shot install
- `scripts/install-agent-stack.sh` (uses mise runtimes, installs langchain/langgraph/langsmith tools, sky, claude/codex/gemini CLIs, fabric). Respect TOOL_PYTHON_VERSION/PIXI_ENV if set.
- Secrets: run `scripts/setup-secrets-env.sh --open` (fills ~/.config/macos-development-environment/secrets.env); reload shell.
- Managed configs: `scripts/ensure-managed-configs.sh` (oh-my-zsh aliases, launchd plist, etc.).

## Validation (run often)
- `scripts/verify-tooling.sh` – checks runtimes, key CLIs, SkyPilot install.
- `scripts/verify-langchain-tools.sh` – langchain/langgraph/langsmith CLI smoke + API key check.
- `scripts/verify-openai-key.py` / `verify-anthropic-key.py` – confirm keys.
- `scripts/verify-openlit.sh` – ensure OpenLIT endpoint set and reachable.
- `scripts/status-dashboard.sh --json` – consolidated health (includes openlit/gemini/tmux, etc.).
- `scripts/sky-status.sh` – SkyPilot status + AWS EC2 snapshot; kills stale API servers automatically.

## SkyPilot / OpenLIT
- Install via our stack scripts only (no ad-hoc uv). Use `scripts/setup-skypilot-aws.sh --init-config` after AWS creds are in secrets.env.
- Deploy/manage OpenLIT: `scripts/openlit-control.sh deploy|status|endpoints|env --write-env` (uses configs/openlit-skypilot.yaml and docker-compose overrides).
- If Sky API port is stuck (46580), rerun `scripts/sky-status.sh` to kill stale PID then restart API server.

## Shell / tmux
- oh-my-zsh aliases: reload after managed configs; key aliases include `openlit`, `openlit-status`, maintenance.
- tmux: run `scripts/optimize-tmux.sh` via install-agent-stack; verification hook in `scripts/status-dashboard.sh`.

## Secrets & env
- Primary source: `~/.config/macos-development-environment/secrets.env` (created by setup-secrets-env.sh). Avoid checking in secrets; MDE_SECRET_OVERRIDE=0 forces reading env over keychain.
- Key labels in Keychain: mde-openai-api-key, mde-anthropic-api-key, mde-github-token, mde-langsmith-api-key, mde-gemini-api-key, etc.

## Maintenance
- Launchd job com.ray-manaloto.macos-dev-maintenance handles updates (brew/mise/bun/uv/pixi) and log rotation; config under ~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance.
- Manual trigger: `launchctl start com.ray-manaloto.macos-dev-maintenance`.

## Enforcement tips
- After changes, run: verify-tooling.sh → sky-status.sh → status-dashboard.sh --json.
- Keep bun.lock/package.json committed for JS tools; avoid stray global npm installs.
- Keep SkyPilot install managed by install-agent-stack and patch-skypilot.sh (no manual uv tool installs).

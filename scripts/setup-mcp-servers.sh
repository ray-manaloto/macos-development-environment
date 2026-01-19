#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_SRC_DIR="$REPO_ROOT/scripts/mcp"
MCP_BIN_DIR="$HOME/.local/bin"
CLAUDE_DESKTOP_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_DESKTOP_CONFIG="$CLAUDE_DESKTOP_DIR/claude_desktop_config.json"

MDE_MCP_SCOPE="${MDE_MCP_SCOPE:-user}"
MDE_MCP_CONFIG="${MDE_MCP_CONFIG:-$REPO_ROOT/configs/mcp-servers.mcp.json}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

build_normalized_config() {
  if [[ ! -f "$MDE_MCP_CONFIG" ]]; then
    log "MCP config not found: $MDE_MCP_CONFIG"
    exit 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    log "python3 not found; cannot parse MCP config."
    exit 1
  fi

  MDE_MCP_NORMALIZED="$(MCP_BIN_DIR="$MCP_BIN_DIR" MDE_MCP_CONFIG="$MDE_MCP_CONFIG" \
    python3 - <<'PY'
import json
import os
import shutil
from pathlib import Path

config_path = Path(os.environ["MDE_MCP_CONFIG"])
data = json.loads(config_path.read_text())
servers = data.get("mcpServers", data)
if not isinstance(servers, dict):
    raise SystemExit("Invalid MCP config: expected object mapping server names.")

def expand_string(value: str) -> str:
    return os.path.expandvars(os.path.expanduser(value))

def resolve_command(cmd: str):
    if not cmd:
        return cmd
    cmd = expand_string(cmd)
    if os.path.isabs(cmd):
        return cmd
    resolved = shutil.which(cmd)
    if resolved:
        return resolved
    mcp_bin = os.environ.get("MCP_BIN_DIR") or os.path.expanduser("~/.local/bin")
    candidate = os.path.join(mcp_bin, cmd)
    if os.path.exists(candidate):
        return candidate
    return cmd

normalized = {}
for name, cfg in servers.items():
    if not isinstance(cfg, dict):
        continue
    entry = dict(cfg)
    command = entry.get("command")
    if command:
        entry["command"] = resolve_command(command)

    args = entry.get("args")
    if isinstance(args, str):
        args = [args]
    if isinstance(args, list):
        entry["args"] = [expand_string(item) if isinstance(item, str) else item for item in args]

    url = entry.get("url")
    if isinstance(url, str):
        entry["url"] = expand_string(url)

    normalized[name] = entry

print(json.dumps({"mcpServers": normalized}))
PY
)"

  export MDE_MCP_NORMALIZED
}

install_wrappers() {
  mkdir -p "$MCP_BIN_DIR"

  local files=(
    "mde-mcp-common.sh"
    "mde-mcp-github"
    "mde-mcp-langsmith"
    "mde-mcp-notebooklm"
    "mde-mcp-context7"
    "mde-mcp-brave-search"
    "mde-mcp-filesystem"
    "mde-mcp-docker"
  )

  for file in "${files[@]}"; do
    if [[ ! -f "$MCP_SRC_DIR/$file" ]]; then
      log "Missing MCP wrapper source: $MCP_SRC_DIR/$file"
      exit 1
    fi
    install -m 0755 "$MCP_SRC_DIR/$file" "$MCP_BIN_DIR/$file"
  done
}

write_claude_desktop_config() {
  mkdir -p "$CLAUDE_DESKTOP_DIR"

  if [[ -f "$CLAUDE_DESKTOP_CONFIG" ]]; then
    local ts
    ts="$(date '+%Y%m%d_%H%M%S')"
    cp "$CLAUDE_DESKTOP_CONFIG" "$CLAUDE_DESKTOP_CONFIG.backup.$ts"
  fi

  export CLAUDE_DESKTOP_CONFIG

  python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["CLAUDE_DESKTOP_CONFIG"])
normalized = json.loads(os.environ.get("MDE_MCP_NORMALIZED", "{}"))
servers = normalized.get("mcpServers", {})

config = {}
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        config = {}

mcp_servers = config.get("mcpServers")
if not isinstance(mcp_servers, dict):
    mcp_servers = {}

mcp_servers.update(servers)
config["mcpServers"] = mcp_servers

config_path.write_text(json.dumps(config, indent=2) + "\n")
PY
}

sync_claude_code() {
  if ! command -v claude >/dev/null 2>&1; then
    log "Claude Code CLI not found; skipping Claude Code MCP sync."
    return 0
  fi

  MDE_MCP_SCOPE="$MDE_MCP_SCOPE" python3 - <<'PY'
import json
import os
import subprocess

normalized = json.loads(os.environ.get("MDE_MCP_NORMALIZED", "{}"))
servers = normalized.get("mcpServers", {})
scope = os.environ.get("MDE_MCP_SCOPE", "user")

for name, cfg in servers.items():
    if not isinstance(cfg, dict):
        continue
    cmd = cfg.get("command")
    url = cfg.get("url")
    transport = cfg.get("type", "http")
    args = cfg.get("args") or []
    headers = cfg.get("headers") or {}

    subprocess.run(["claude", "mcp", "remove", "--scope", scope, name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if cmd:
        subprocess.run(["claude", "mcp", "add", "--scope", scope, name, "--", cmd, *args], check=True)
        continue
    if url:
        add_cmd = ["claude", "mcp", "add", "--scope", scope, "--transport", transport, name, url]
        for key, value in headers.items():
            add_cmd.extend(["-H", f"{key}: {value}"])
        subprocess.run(add_cmd, check=True)
        continue
PY
}

sync_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    log "Codex CLI not found; skipping Codex MCP sync."
    return 0
  fi

  python3 - <<'PY'
import json
import os
import subprocess

normalized = json.loads(os.environ.get("MDE_MCP_NORMALIZED", "{}"))
servers = normalized.get("mcpServers", {})

for name, cfg in servers.items():
    if not isinstance(cfg, dict):
        continue
    cmd = cfg.get("command")
    url = cfg.get("url")
    args = cfg.get("args") or []
    bearer_env = cfg.get("bearerTokenEnvVar")

    subprocess.run(["codex", "mcp", "remove", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if cmd:
        subprocess.run(["codex", "mcp", "add", name, "--", cmd, *args], check=True)
        continue
    if url:
        add_cmd = ["codex", "mcp", "add", name, "--url", url]
        if bearer_env:
            add_cmd.extend(["--bearer-token-env-var", bearer_env])
        subprocess.run(add_cmd, check=True)
        continue
PY
}

main() {
  setup_path

  install_wrappers
  build_normalized_config
  write_claude_desktop_config
  sync_claude_code
  sync_codex

  log "MCP server setup complete."
}

main "$@"

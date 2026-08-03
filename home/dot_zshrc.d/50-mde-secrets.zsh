# mde secrets shell integration.
# Framework-neutral: survives any oh-my-zsh / starship / plain-zsh migration
# because this file is sourced by ~/.zshrc via the ~/.zshrc.d/ loader, not by
# any specific shell framework.
#
# Provides:
#   1. Automatic secret env loading via `fnox activate zsh` (chpwd + precmd
#      hooks that decrypt the age-encrypted sync cache into env vars).
#   2. CRUD wrapper functions for `mde-py secrets add/update/rm` that
#      propagate changes to the CURRENT shell via `eval "$(...)"`.
#
# Architecture: docs/secrets-workflow.md

# ---------------------------------------------------------------------------
# Resolve MDE_PROJECT_DIR from the canonical global mise config so wrappers
# can locate the repo venv regardless of cwd. mise activate is not assumed
# to have fired (oh-my-zsh's mise plugin only adds completions).
# ---------------------------------------------------------------------------
if [[ -z "${MDE_PROJECT_DIR:-}" && -r "$HOME/.config/mise/config.toml" ]]; then
  export MDE_PROJECT_DIR="$(sed -n 's/^MDE_PROJECT_DIR = "\(.*\)"$/\1/p' \
    "$HOME/.config/mise/config.toml" 2>/dev/null)"
fi

# ---------------------------------------------------------------------------
# fnox activate: installs chpwd/precmd hooks that resolve secrets into env.
# ---------------------------------------------------------------------------
if command -v fnox >/dev/null 2>&1; then
  eval "$(fnox activate zsh 2>/dev/null)"
fi

# ---------------------------------------------------------------------------
# CRUD wrappers: eval the CLI's stdout so `export KEY=...` / `unset KEY`
# lines take effect in the current shell instead of a child process.
# ---------------------------------------------------------------------------
_mde_secret_wrap() {
  # Run a `mde-py secrets` subcommand, capturing stdout and its exit code
  # separately so a failing CLI does not get silently upgraded to success
  # by `eval "$(...)"`. Only evaluate the emitted shell fragment on rc=0.
  local _subcmd="$1"
  shift
  if [[ -z "${MDE_PROJECT_DIR:-}" ]]; then
    print -u2 "mde-secret: MDE_PROJECT_DIR not set — is ~/.config/mise/config.toml present?"
    return 127
  fi
  local _bin="$MDE_PROJECT_DIR/.venv/bin/mde-py"
  if [[ ! -x "$_bin" ]]; then
    print -u2 "mde-secret: $_bin missing — run \`cd \$MDE_PROJECT_DIR && uv sync\`"
    return 127
  fi
  local _out _rc
  _out="$("$_bin" secrets "$_subcmd" "$@")"
  _rc=$?
  if (( _rc != 0 )); then
    return $_rc
  fi
  eval "$_out"
}

mde-secret-add() {
  if [[ -z "$1" ]]; then
    print -u2 "usage: mde-secret-add KEY [--value VALUE]"
    return 2
  fi
  _mde_secret_wrap add "$@"
}

mde-secret-update() {
  if [[ -z "$1" ]]; then
    print -u2 "usage: mde-secret-update KEY [--value VALUE]"
    return 2
  fi
  _mde_secret_wrap update "$@"
}

mde-secret-remove() {
  if [[ -z "$1" ]]; then
    print -u2 "usage: mde-secret-remove KEY"
    return 2
  fi
  _mde_secret_wrap rm "$@"
}

alias mde-secret-rm=mde-secret-remove

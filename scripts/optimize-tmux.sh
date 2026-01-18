#!/usr/bin/env bash
set -euo pipefail

TMUX_INSTALL="${TMUX_INSTALL:-auto}"

install_tmux() {
  if [[ "$TMUX_INSTALL" == "pixi" ]]; then
    if command -v pixi >/dev/null 2>&1; then
      pixi global install tmux
      return 0
    fi
    echo "pixi not found; cannot install tmux via pixi" >&2
    return 1
  fi

  if command -v brew >/dev/null 2>&1; then
    brew install tmux
    return 0
  fi

  if command -v pixi >/dev/null 2>&1; then
    pixi global install tmux
    return 0
  fi

  echo "tmux install failed: brew or pixi required" >&2
  return 1
}

install_skypilot() {
  if command -v uv >/dev/null 2>&1; then
    uv tool install --upgrade "skypilot[aws]"
    return 0
  fi
  if command -v pip >/dev/null 2>&1; then
    pip install --upgrade "skypilot[aws]"
    return 0
  fi
  echo "skypilot install failed: uv or pip required" >&2
  return 1
}

install_tpm() {
  local tpm_dir="$HOME/.tmux/plugins/tpm"
  if [ ! -d "$tpm_dir" ]; then
    git clone https://github.com/tmux-plugins/tpm "$tpm_dir"
  fi
}

write_tmux_conf() {
  local conf="$HOME/.tmux.conf"
  local backup="${conf}.bak.$(date +%Y%m%d%H%M%S)"
  if [ -f "$conf" ]; then
    cp "$conf" "$backup"
  fi

  cat <<'TMUXCONF' > "$conf"
# AGENT OPS TMUX CONFIG

# Terminal + color
set -g default-terminal "tmux-256color"
set -as terminal-overrides ",*:RGB"
set -g set-clipboard on

# UX
set -g mouse on
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on
set -g history-limit 100000

# Prefixes (keep default, add alternative)
set -g prefix C-b
set -g prefix2 C-a

# Split panes in current path
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Vim-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Status bar
set -g status-position top
set -g status-right-length 100
set -g status-right "☁️  #(echo $AWS_PROFILE) | %H:%M "

# Plugins
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-restore 'on'

# Initialize TPM (keep at bottom)
run '~/.tmux/plugins/tpm/tpm'
TMUXCONF
}

install_tmux
install_skypilot
install_tpm
write_tmux_conf

echo "tmux + skypilot setup complete."
echo "Open tmux and press prefix + I to install plugins."

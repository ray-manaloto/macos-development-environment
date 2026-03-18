"""Tmux setup: mise-managed tmux + TPM + managed config."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

TEMPLATE_CONF = Path(__file__).resolve().parents[3] / "templates" / "tmux.conf"
MANAGED_MARKER = "Managed by macos-development-environment"
TPM_DIR = Path.home() / ".tmux" / "plugins" / "tpm"
TMUX_CONF = Path.home() / ".tmux.conf"


def install_tmux() -> int:
    """Install and configure tmux via mise.

    Returns:
        Exit code.
    """
    print("==> Setting up tmux")

    if not shutil.which("mise"):
        print("ERROR: mise is required")
        return 1

    # Ensure tmux is installed via mise
    if not shutil.which("tmux"):
        print("Installing tmux via mise...")
        proc = subprocess.run(
            ["mise", "install", "tmux"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            print(f"ERROR: mise install tmux failed: {proc.stderr}")
            return 1

    # Install TPM
    if not TPM_DIR.exists():
        print("Installing TPM...")
        proc = subprocess.run(
            ["git", "clone", "https://github.com/tmux-plugins/tpm", str(TPM_DIR)],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if proc.returncode != 0:
            print(f"WARNING: TPM clone failed: {proc.stderr}")

    # Write managed tmux.conf
    _write_tmux_conf()

    # Install TPM plugins
    _install_tpm_plugins()

    print("tmux setup complete.")
    return 0


def _write_tmux_conf() -> None:
    """Write the managed tmux.conf from template."""
    if not TEMPLATE_CONF.exists():
        print(f"WARNING: tmux template not found at {TEMPLATE_CONF}")
        return

    if TMUX_CONF.exists() and MANAGED_MARKER not in TMUX_CONF.read_text():
        print("tmux.conf exists and is not managed; skipping")
        return

    shutil.copy2(TEMPLATE_CONF, TMUX_CONF)
    print(f"Wrote {TMUX_CONF}")


def _install_tpm_plugins() -> None:
    """Install TPM plugins if tpm is available."""
    install_script = TPM_DIR / "bin" / "install_plugins"
    if not install_script.exists():
        return

    if not shutil.which("tmux"):
        return

    if not TMUX_CONF.exists():
        return

    # Start a temporary session for plugin install
    session = "mde-bootstrap"
    created = False
    try:
        check = subprocess.run(
            ["tmux", "list-sessions"],
            capture_output=True,
            timeout=5,
        )
        if check.returncode != 0:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session],
                capture_output=True,
                timeout=10,
            )
            created = True

        subprocess.run(
            ["tmux", "source-file", str(TMUX_CONF)],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            [str(install_script)],
            capture_output=True,
            timeout=60,
        )
    finally:
        if created:
            subprocess.run(
                ["tmux", "kill-session", "-t", session],
                capture_output=True,
                timeout=5,
            )

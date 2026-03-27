"""SessionEnd hook — triggers remember plugin save before /clear destroys context.

Called by Claude Code when a session ends. When the reason is "clear",
forces the remember plugin's save-session.sh to run so that session memory
is captured before the context window is wiped.

Always exits 0 (never blocks session end).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SessionEnd memory save before /clear",
    "entry": "save_memory_on_clear",
}

import json
import subprocess
import sys
from pathlib import Path

from mde.log import get_tracer, logger

_tracer = get_tracer(__name__)

_PLUGIN_CACHE = (
    Path.home() / ".claude" / "plugins" / "cache" / "claude-plugins-official" / "remember"
)


def _find_save_script() -> Path | None:
    """Locate the remember plugin's save-session.sh in the plugin cache."""
    if not _PLUGIN_CACHE.exists():
        return None
    for version_dir in sorted(_PLUGIN_CACHE.iterdir(), reverse=True):
        script = version_dir / "scripts" / "save-session.sh"
        if script.is_file():
            return script
    return None


def save_memory_on_clear() -> int:
    """Force-save remember memory when session ends due to /clear."""
    with _tracer.start_as_current_span("mde.hook.save_memory_on_clear") as span:
        span.set_attribute("hook.event", "SessionEnd")

        # Read stdin for session end event data
        try:
            raw = sys.stdin.read()
            event = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            event = {}

        reason = event.get("reason", "")
        span.set_attribute("hook.reason", reason)

        # Only force-save on /clear — normal exits are handled by Stop hook
        if reason != "clear":
            logger.bind(hook="save_memory_on_clear", reason=reason).debug("skipped_non_clear")
            return 0

        save_script = _find_save_script()
        if not save_script:
            logger.bind(hook="save_memory_on_clear").warning("remember_plugin_not_found")
            print(
                "SessionEnd: remember plugin save-session.sh not found, memory NOT saved",
                file=sys.stderr,
            )
            return 0

        # Set CLAUDE_PROJECT_DIR so save-session.sh resolves paths correctly
        try:
            repo_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            project_dir = repo_root.stdout.strip() if repo_root.returncode == 0 else str(Path.cwd())
        except (subprocess.TimeoutExpired, OSError):
            project_dir = str(Path.cwd())

        plugin_root = str(save_script.parent.parent)
        env = {
            "CLAUDE_PROJECT_DIR": project_dir,
            "CLAUDE_PLUGIN_ROOT": plugin_root,
            "HOME": str(Path.home()),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }

        logger.bind(
            hook="save_memory_on_clear",
            script=str(save_script),
            project_dir=project_dir,
        ).info("forcing_remember_save")

        try:
            result = subprocess.run(
                ["bash", str(save_script), "--force"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            if result.returncode == 0:
                logger.bind(hook="save_memory_on_clear").info("save_completed")
                print("SessionEnd: memory saved before /clear")
            else:
                logger.bind(
                    hook="save_memory_on_clear",
                    exit_code=result.returncode,
                    stderr=result.stderr[:500] if result.stderr else "",
                ).warning("save_failed")
                print(
                    f"SessionEnd: memory save failed (exit {result.returncode})",
                    file=sys.stderr,
                )
        except subprocess.TimeoutExpired:
            logger.bind(hook="save_memory_on_clear").warning("save_timeout")
            print("SessionEnd: memory save timed out", file=sys.stderr)
        except OSError as exc:
            logger.bind(hook="save_memory_on_clear", error=str(exc)).warning("save_error")
            print(f"SessionEnd: memory save error: {exc}", file=sys.stderr)

        return 0

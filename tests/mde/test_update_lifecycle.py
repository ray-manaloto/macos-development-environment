"""Integration tests for the mde update lifecycle.

Validates that the update lifecycle produces no missing tools,
no foreign platform entries in lockfiles, and no hidden errors.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
def test_mise_doctor_no_problems() -> None:
    """Mise doctor must report no problems after a healthy state."""
    if not shutil.which("mise"):
        pytest.skip("mise not available")
    proc = subprocess.run(
        ["mise", "doctor"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Check for problems (not warnings — warnings may be env-specific)
    for line in proc.stdout.splitlines():
        line_lower = line.lower()
        if "problem found" in line_lower and "no" not in line_lower:
            pytest.fail(f"mise doctor reported problems:\n{proc.stdout}")


@pytest.mark.integration
def test_mise_no_missing_tools() -> None:
    """No configured tools should be in a '(missing)' state."""
    if not shutil.which("mise"):
        pytest.skip("mise not available")
    proc = subprocess.run(
        ["mise", "ls"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    missing = [line for line in proc.stdout.splitlines() if "(missing)" in line]
    if missing:
        pytest.fail(f"{len(missing)} missing tool(s):\n" + "\n".join(missing))


@pytest.mark.integration
def test_project_lockfile_single_platform() -> None:
    """Project mise.lock must only contain entries for the current platform."""
    import platform as _platform
    import tomllib

    lock_path = Path.cwd() / "mise.lock"
    if not lock_path.exists():
        pytest.skip("No project mise.lock")

    system = _platform.system().lower()
    machine = _platform.machine().lower()
    os_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    arch_map = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}
    current = f"{os_map.get(system, system)}-{arch_map.get(machine, machine)}"

    data = tomllib.loads(lock_path.read_text())
    foreign: set[str] = set()
    for tool_entries in data.get("tools", {}).values():
        entries = tool_entries if isinstance(tool_entries, list) else [tool_entries]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key in entry:
                if key.startswith("platforms."):
                    plat = key.removeprefix("platforms.")
                    if plat != current:
                        foreign.add(plat)

    if foreign:
        pytest.fail(
            f"mise.lock has {len(foreign)} foreign platform(s): {sorted(foreign)}. "
            f"Run: mise lock --platform {current}"
        )


@pytest.mark.integration
def test_update_step_ordering() -> None:
    """Verify the update lifecycle has the correct step order."""
    # Import and inspect the steps list via source code
    import inspect

    from mde.maintain import update
    from mde.maintain.update import run_update  # noqa: F401

    source = inspect.getsource(update.run_update)

    # Verify ordering: upgrade before lock, lock before prune, prune before install
    upgrade_pos = source.find("mise upgrade")
    lock_pos = source.find("mise lock")
    prune_pos = source.find("mise prune")
    install_pos = source.find("mise install")
    reshim_pos = source.find("mise reshim")

    assert upgrade_pos < lock_pos, "mise upgrade must come before mise lock"
    assert lock_pos < prune_pos, "mise lock must come before mise prune"
    assert prune_pos < install_pos, "mise prune must come before mise install"
    assert install_pos < reshim_pos, "mise install must come before mise reshim"


@pytest.mark.integration
def test_detect_platform_matches_system() -> None:
    """_detect_platform returns the correct platform string."""
    import platform as _platform

    from mde.maintain.update import _detect_platform

    result = _detect_platform()
    system = _platform.system().lower()
    machine = _platform.machine().lower()

    if system == "darwin":
        assert result.startswith("macos-"), f"Expected macos-*, got {result}"
    elif system == "linux":
        assert result.startswith("linux-"), f"Expected linux-*, got {result}"

    if machine in ("arm64", "aarch64"):
        assert result.endswith("-arm64"), f"Expected *-arm64, got {result}"
    elif machine in ("x86_64", "amd64"):
        assert result.endswith("-x64"), f"Expected *-x64, got {result}"


def test_run_mise_lock_logs_and_returns_first_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """_run_mise_lock logs failures and propagates a non-zero exit code."""
    from mde.maintain import update

    monkeypatch.setattr(update.shutil, "which", lambda _: "/usr/bin/mise")
    monkeypatch.setattr(update, "_detect_platform", lambda: "macos-arm64")

    responses = iter(
        [
            subprocess.CompletedProcess(["mise", "lock", "--platform", "macos-arm64"], 23),
            subprocess.CompletedProcess(
                ["mise", "lock", "--global", "--platform", "macos-arm64"],
                0,
            ),
        ]
    )

    def fake_run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
        assert timeout == 120
        assert command[0:2] == ["mise", "lock"]
        return next(responses)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    result = update._run_mise_lock()

    assert result == 23
    captured = capsys.readouterr()
    assert "mise lock --platform macos-arm64 exited 23" in captured.out


def test_run_mise_lock_logs_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """_run_mise_lock logs exceptions instead of swallowing them silently."""
    from mde.maintain import update

    monkeypatch.setattr(update.shutil, "which", lambda _: "/usr/bin/mise")
    monkeypatch.setattr(update, "_detect_platform", lambda: "macos-arm64")

    calls = {"count": 0}

    def fake_run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
        del timeout
        calls["count"] += 1
        if calls["count"] == 1:
            message = "boom"
            raise OSError(message)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    result = update._run_mise_lock()

    assert result == 1
    captured = capsys.readouterr()
    assert "mise lock --platform macos-arm64 failed: boom" in captured.out

"""Docker runtime validation."""

from __future__ import annotations

import shutil
import subprocess

from mde.domain.docker_stacks import DOCKER_DIR, ROOT_COMPOSE
from mde.models.result import Severity, ValidationResult

# Minimum Compose version required for the `include:` directive.
_MIN_COMPOSE_MAJOR = 2
_MIN_COMPOSE_MINOR = 20
_MIN_VERSION_PARTS = 2


def validate_docker() -> ValidationResult:
    """Validate Docker CLI, daemon, compose version, and infrastructure."""
    result = ValidationResult()
    if not shutil.which("docker"):
        result.add(
            "docker",
            "docker CLI is not installed",
            severity=Severity.WARNING,
            rule="docker.not-installed",
        )
        return result
    _check_docker_version(result)
    _check_docker_compose(result)
    _check_compose_version(result)
    _check_compose_structure(result)
    _check_legacy_compose_files(result)
    return result


def _check_docker_version(result: ValidationResult) -> None:
    try:
        proc = subprocess.run(
            ["docker", "version", "--format", "{{.Client.Version}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result.files_checked += 1
        if proc.returncode != 0:
            result.add_warning(
                "docker",
                "docker version failed — daemon may not be running",
                rule="docker.daemon",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def _check_docker_compose(result: ValidationResult) -> None:
    if not shutil.which("docker-compose") and not shutil.which("docker"):
        return
    try:
        proc = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result.files_checked += 1
        if proc.returncode != 0:
            result.add_warning(
                "docker",
                "docker compose not available",
                rule="docker.compose-missing",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def _check_compose_version(result: ValidationResult) -> None:
    """Verify Docker Compose version supports include directive (v2.20+).

    Docker Desktop reports version as 5.x.x (always >= 2.20).
    Linux reports 2.x.x. Both formats are handled.
    """
    try:
        proc = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result.files_checked += 1
        if proc.returncode == 0:
            version_str = proc.stdout.strip().lstrip("v")
            parts = version_str.split(".")
            if len(parts) >= _MIN_VERSION_PARTS:
                major, minor = int(parts[0]), int(parts[1])
                # Docker Desktop uses 5.x.x (always fine)
                # Linux Compose uses 2.x.x (need >= 2.20)
                if major == _MIN_COMPOSE_MAJOR and minor < _MIN_COMPOSE_MINOR:
                    result.add_warning(
                        "docker",
                        f"Docker Compose {version_str} < 2.20.0 — include: directive unavailable",
                        rule="docker.compose-version",
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass


def _check_compose_structure(result: ValidationResult) -> None:
    """Verify root compose.yaml exists."""
    result.files_checked += 1
    if not ROOT_COMPOSE.is_file():
        result.add_warning(
            str(ROOT_COMPOSE),
            "Root compose.yaml not found — docker infrastructure incomplete",
            rule="docker.root-compose-missing",
        )


def _check_legacy_compose_files(result: ValidationResult) -> None:
    """Warn if legacy docker-compose.yml files remain."""
    for pattern in ("docker-compose.yml", "docker-compose.yaml"):
        for path in DOCKER_DIR.rglob(pattern):
            result.add_warning(
                str(path),
                f"Legacy {pattern} found — rename to compose.yaml",
                rule="docker.legacy-compose-file",
            )

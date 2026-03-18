"""Docker runtime validation."""

from __future__ import annotations

import shutil
import subprocess

from mde.models.result import Severity, ValidationResult


def validate_docker() -> ValidationResult:
    """Validate Docker CLI and daemon availability."""
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

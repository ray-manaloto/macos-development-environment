"""Tests for shared Docker stack path constants."""

from __future__ import annotations

from mde.domain.docker_stacks import (
    DOCKER_DIR,
    MEMORY_COMPOSE,
    OBSERVABILITY_COMPOSE,
    ROOT_COMPOSE,
)


class TestPathConstants:
    """Verify Docker path constants resolve correctly."""

    def test_docker_dir_exists(self) -> None:
        assert DOCKER_DIR.is_dir()

    def test_observability_compose_path(self) -> None:
        assert OBSERVABILITY_COMPOSE.name == "compose.yaml"
        assert "docker/observability" in str(OBSERVABILITY_COMPOSE)

    def test_memory_compose_path(self) -> None:
        assert MEMORY_COMPOSE.name == "compose.yaml"
        assert "docker/memory" in str(MEMORY_COMPOSE)

    def test_root_compose_path(self) -> None:
        assert ROOT_COMPOSE.name == "compose.yaml"
        assert ROOT_COMPOSE.parent == DOCKER_DIR

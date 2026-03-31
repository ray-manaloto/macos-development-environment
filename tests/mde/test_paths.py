"""Tests for centralized MdePaths model."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clear_paths_cache(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clear get_paths() lru_cache and MDE_* env vars before/after each test.

    Without this, MDE_* env vars set by mise (after chezmoi apply) leak into
    tests and override the cascading defaults we're verifying.
    """
    from mde.lib.paths import get_paths

    for key in list(os.environ):
        if key.startswith("MDE_"):
            monkeypatch.delenv(key, raising=False)
    get_paths.cache_clear()
    yield
    get_paths.cache_clear()


class TestMdePathsCascade:
    """Cascading default behavior."""

    def test_cascade_from_project_dir(self, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path)
        assert paths.generated_dir == tmp_path / ".generated"
        assert paths.dir_remember == tmp_path / ".generated" / "remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"
        assert paths.dir_transcripts == tmp_path / ".generated" / "transcripts"
        assert paths.dir_schemas == tmp_path / ".generated" / "schemas"
        assert paths.dir_reports == tmp_path / ".generated" / "reports"
        assert paths.dir_context == tmp_path / ".generated" / "context"
        assert paths.dir_dream == tmp_path / ".generated" / "dream"

    def test_override_generated_dir_cascades(self, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        custom_gen = tmp_path / "custom-gen"
        paths = MdePaths(project_dir=tmp_path, generated_dir=custom_gen)
        assert paths.dir_remember == custom_gen / "remember"
        assert paths.dir_dream == custom_gen / "dream"
        assert paths.dir_learnings == custom_gen / "learnings"

    def test_override_individual_child(self, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path, dir_remember=tmp_path / "my-remember")
        assert paths.dir_remember == tmp_path / "my-remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"


class TestMdePathsEnvVars:
    """Environment variable loading via BaseSettings."""

    def test_env_var_loading(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("MDE_GENERATED_DIR", str(tmp_path / "gen"))
        paths = MdePaths()
        assert paths.project_dir == tmp_path
        assert paths.generated_dir == tmp_path / "gen"
        assert paths.dir_remember == tmp_path / "gen" / "remember"

    def test_env_var_for_child_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("MDE_DIR_REMEMBER", str(tmp_path / "custom-remember"))
        paths = MdePaths()
        assert paths.dir_remember == tmp_path / "custom-remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"

    def test_fallback_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from mde.lib.paths import MdePaths

        for key in list(os.environ):
            if key.startswith("MDE_"):
                monkeypatch.delenv(key, raising=False)
        paths = MdePaths()
        assert paths.project_dir is not None
        assert paths.generated_dir == paths.project_dir / ".generated"


class TestMdePathsTypeSafety:
    """Type coercion and field types."""

    def test_all_fields_are_path(self, tmp_path: Path) -> None:
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path)
        for name in (
            "project_dir",
            "generated_dir",
            "dir_remember",
            "dir_learnings",
            "dir_transcripts",
            "dir_schemas",
            "dir_reports",
            "dir_context",
            "dir_dream",
        ):
            assert isinstance(getattr(paths, name), Path), f"{name} is not a Path"

    def test_string_env_coerced_to_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        paths = MdePaths()
        assert isinstance(paths.project_dir, Path)


class TestBackwardCompat:
    """Backward-compatible function aliases."""

    def test_repo_root_alias(self) -> None:
        from mde.lib.paths import get_paths, repo_root

        assert repo_root() == get_paths().project_dir

    def test_generated_dir_alias(self) -> None:
        from mde.lib.paths import generated_dir, get_paths

        assert generated_dir() == get_paths().generated_dir

    def test_common_repo_root_is_paths_repo_root(self) -> None:
        from mde.hooks._common import repo_root as common_rr
        from mde.lib.paths import repo_root as paths_rr

        assert common_rr is paths_rr


class TestGetPathsSingleton:
    """get_paths() caching behavior."""

    def test_get_paths_returns_same_instance(self) -> None:
        from mde.lib.paths import get_paths

        assert get_paths() is get_paths()

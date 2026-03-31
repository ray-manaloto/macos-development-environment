"""Tests for the paths validator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mde.validate.paths import validate_paths

if TYPE_CHECKING:
    import pytest


class TestValidatePathsEnvVarMissing:
    """Check 1: paths.env-var-missing."""

    def test_warns_when_mde_generated_dir_unset(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        for key in ("MDE_PROJECT_DIR", "MDE_GENERATED_DIR"):
            monkeypatch.delenv(key, raising=False)
        result = validate_paths(root=tmp_path)
        msgs = [f.message for f in result.findings]
        assert any("MDE_GENERATED_DIR" in m for m in msgs)


class TestValidatePathsRememberSymlink:
    """Check 3: paths.remember-symlink."""

    def test_error_when_remember_is_dir(self, tmp_path: Path) -> None:
        (tmp_path / ".remember").mkdir()
        result = validate_paths(root=tmp_path)
        assert not result.passed
        msgs = [f.message for f in result.findings]
        assert any("symlink" in m.lower() for m in msgs)

    def test_pass_when_remember_is_symlink(self, tmp_path: Path) -> None:
        target = tmp_path / ".generated" / "remember"
        target.mkdir(parents=True)
        (tmp_path / ".remember").symlink_to(target)
        result = validate_paths(root=tmp_path)
        symlink_errors = [
            f
            for f in result.findings
            if "symlink" in f.message.lower() and f.severity.value == "error"
        ]
        assert len(symlink_errors) == 0


class TestValidatePathsHardcodedRef:
    """Check 6: paths.hardcoded-ref."""

    def test_warns_on_hardcoded_generated(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src" / "mde"
        src_dir.mkdir(parents=True)
        (src_dir / "bad.py").write_text('x = repo_root() / ".generated" / "foo"\n')
        result = validate_paths(root=tmp_path)
        msgs = [f.message for f in result.findings]
        assert any("hardcoded" in m.lower() or ".generated" in m for m in msgs)


class TestValidatePathsCompositionViolation:
    """Check 8: paths.composition-violation."""

    def test_error_on_chezmoi_template_in_child_var(self, tmp_path: Path) -> None:
        tpl_dir = tmp_path / "home" / "dot_config" / "mise"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "config.toml.tmpl").write_text(
            "[env]\n"
            'MDE_PROJECT_DIR = "{{ .chezmoi.sourceDir | dir }}"\n'
            'MDE_DIR_REMEMBER = "{{ .chezmoi.sourceDir | dir }}/.generated/remember"\n'
        )
        result = validate_paths(root=tmp_path)
        assert not result.passed
        msgs = [f.message for f in result.findings]
        assert any("composition" in m.lower() for m in msgs)

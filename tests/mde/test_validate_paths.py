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


class TestValidatePathsDirMissing:
    """Check 2: paths.dir-missing."""

    def test_warns_when_env_var_points_to_nonexistent_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path / "no_such_dir"))
        monkeypatch.setenv("MDE_GENERATED_DIR", str(tmp_path / "also_missing"))
        result = validate_paths(root=tmp_path)
        dir_missing = [f for f in result.findings if f.rule == "paths.dir-missing"]
        assert len(dir_missing) == 2

    def test_pass_when_env_var_points_to_existing_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        proj = tmp_path / "project"
        gen = tmp_path / "generated"
        proj.mkdir()
        gen.mkdir()
        monkeypatch.setenv("MDE_PROJECT_DIR", str(proj))
        monkeypatch.setenv("MDE_GENERATED_DIR", str(gen))
        result = validate_paths(root=tmp_path)
        dir_missing = [f for f in result.findings if f.rule == "paths.dir-missing"]
        assert len(dir_missing) == 0


class TestValidatePathsMiseGlobalMissing:
    """Check 4: paths.mise-global-missing."""

    def test_error_when_mise_config_lacks_mde_project_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text("[settings]\nenv_shell_expand = true\n")
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        mise_errors = [f for f in result.findings if f.rule == "paths.mise-global-missing"]
        assert len(mise_errors) == 1

    def test_pass_when_mise_config_has_mde_project_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text(
            '[env]\nMDE_PROJECT_DIR = "/some/path"\n[settings]\nenv_shell_expand = true\n'
        )
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        mise_errors = [f for f in result.findings if f.rule == "paths.mise-global-missing"]
        assert len(mise_errors) == 0

    def test_error_when_mde_project_dir_in_wrong_section(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text(
            '[settings]\nenv_shell_expand = true\nMDE_PROJECT_DIR = "/some/path"\n'
        )
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        mise_errors = [f for f in result.findings if f.rule == "paths.mise-global-missing"]
        assert len(mise_errors) == 1


class TestValidatePathsChezmoiTemplateMissing:
    """Check 5: paths.chezmoi-template-missing."""

    def test_error_when_template_lacks_mde_project_dir(self, tmp_path: Path) -> None:
        tpl_dir = tmp_path / "home" / "dot_config" / "mise"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "config.toml.tmpl").write_text('[env]\nSOME_VAR = "hello"\n')
        result = validate_paths(root=tmp_path)
        tpl_errors = [f for f in result.findings if f.rule == "paths.chezmoi-template-missing"]
        assert len(tpl_errors) == 1

    def test_pass_when_template_has_mde_project_dir(self, tmp_path: Path) -> None:
        tpl_dir = tmp_path / "home" / "dot_config" / "mise"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "config.toml.tmpl").write_text(
            '[env]\nMDE_PROJECT_DIR = "{{ .chezmoi.sourceDir | dir }}"\n'
        )
        result = validate_paths(root=tmp_path)
        tpl_errors = [f for f in result.findings if f.rule == "paths.chezmoi-template-missing"]
        assert len(tpl_errors) == 0


class TestValidatePathsReferenceDocMissing:
    """Check 7: paths.reference-doc-missing."""

    def test_error_when_reference_doc_absent(self, tmp_path: Path) -> None:
        result = validate_paths(root=tmp_path)
        doc_errors = [f for f in result.findings if f.rule == "paths.reference-doc-missing"]
        assert len(doc_errors) == 1

    def test_pass_when_reference_doc_exists(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "generated-paths.md").write_text("# Path docs\n")
        result = validate_paths(root=tmp_path)
        doc_errors = [f for f in result.findings if f.rule == "paths.reference-doc-missing"]
        assert len(doc_errors) == 0


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


class TestValidatePathsEnvShellExpandMissing:
    """Check 9: paths.env-shell-expand-missing."""

    def test_error_when_env_shell_expand_absent(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text('[env]\nMDE_PROJECT_DIR = "/some/path"\n')
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        expand_errors = [f for f in result.findings if f.rule == "paths.env-shell-expand-missing"]
        assert len(expand_errors) == 1

    def test_pass_when_env_shell_expand_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text(
            '[env]\nMDE_PROJECT_DIR = "/some/path"\n[settings]\nenv_shell_expand = true\n'
        )
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        expand_errors = [f for f in result.findings if f.rule == "paths.env-shell-expand-missing"]
        assert len(expand_errors) == 0

    def test_error_when_env_shell_expand_is_false(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fake_home = tmp_path / "fakehome"
        mise_dir = fake_home / ".config" / "mise"
        mise_dir.mkdir(parents=True)
        (mise_dir / "config.toml").write_text(
            '[env]\nMDE_PROJECT_DIR = "/some/path"\n[settings]\nenv_shell_expand = false\n'
        )
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        result = validate_paths(root=tmp_path)
        expand_errors = [f for f in result.findings if f.rule == "paths.env-shell-expand-missing"]
        assert len(expand_errors) == 1

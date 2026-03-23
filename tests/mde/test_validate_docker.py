"""Tests for expanded Docker validation checks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from mde.validate.docker import validate_docker


class TestComposeVersionCheck:
    """Test Compose version >= 2.20.0 validation."""

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_accepts_modern_compose(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.32.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = []
        result = validate_docker()
        version_findings = [f for f in result.findings if f.rule == "docker.compose-version"]
        assert len(version_findings) == 0

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_accepts_docker_desktop_version(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        """Docker Desktop reports 5.x.x which is always >= 2.20."""
        mock_run.return_value = MagicMock(returncode=0, stdout="5.1.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = []
        result = validate_docker()
        version_findings = [f for f in result.findings if f.rule == "docker.compose-version"]
        assert len(version_findings) == 0

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_warns_on_old_compose(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.19.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = []
        result = validate_docker()
        version_findings = [f for f in result.findings if f.rule == "docker.compose-version"]
        assert len(version_findings) == 1


class TestComposeStructureCheck:
    """Test root compose.yaml existence check."""

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_passes_when_root_compose_exists(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.32.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = []
        result = validate_docker()
        structure_findings = [f for f in result.findings if f.rule == "docker.root-compose-missing"]
        assert len(structure_findings) == 0

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_warns_when_root_compose_missing(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.32.0\n")
        mock_root.is_file.return_value = False
        mock_dir.rglob.return_value = []
        result = validate_docker()
        structure_findings = [f for f in result.findings if f.rule == "docker.root-compose-missing"]
        assert len(structure_findings) == 1


class TestLegacyComposeCheck:
    """Test legacy docker-compose.yml detection."""

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_warns_on_legacy_files(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.32.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = [Path("docker/old/docker-compose.yml")]
        result = validate_docker()
        legacy_findings = [f for f in result.findings if f.rule == "docker.legacy-compose-file"]
        assert len(legacy_findings) >= 1

    @patch("mde.validate.docker.DOCKER_DIR")
    @patch("mde.validate.docker.ROOT_COMPOSE")
    @patch("shutil.which", return_value="/usr/bin/docker")
    @patch("subprocess.run")
    def test_no_warning_without_legacy_files(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_root: MagicMock,
        mock_dir: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.32.0\n")
        mock_root.is_file.return_value = True
        mock_dir.rglob.return_value = []
        result = validate_docker()
        legacy_findings = [f for f in result.findings if f.rule == "docker.legacy-compose-file"]
        assert len(legacy_findings) == 0

"""Tests for dream pipeline pattern extraction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mde.dream.extract import _scan_transcripts, _slugify


@pytest.fixture
def transcripts_dir(tmp_path: Path) -> Path:
    """Create a temporary transcripts directory with sample files."""
    t_dir = tmp_path / "transcripts"
    t_dir.mkdir()
    return t_dir


class TestScanTranscripts:
    """Tests for _scan_transcripts()."""

    def test_empty_dir(self, transcripts_dir: Path) -> None:
        """Returns empty list when no transcripts exist."""
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        assert result == []

    def test_missing_dir(self, tmp_path: Path) -> None:
        """Returns empty list when transcripts dir doesn't exist."""
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = tmp_path / "nonexistent"
            result = _scan_transcripts()
        assert result == []

    def test_severity_critical_with_file(self, transcripts_dir: Path) -> None:
        """Extracts critical severity findings with file references."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "SEVERITY: critical\nFILE: `src/main.py`\nFINDING: bad thing\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        assert "transcript.critical.main" in result

    def test_severity_high_with_file(self, transcripts_dir: Path) -> None:
        """Extracts high severity findings with file references."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "SEVERITY: high\nFILE: `.github/workflows/ci.yml`\nFINDING: issue\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        assert "transcript.high.ci" in result

    def test_severity_without_file(self, transcripts_dir: Path) -> None:
        """Falls back to 'unspecified' when no FILE: line near severity."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "SEVERITY: critical\nThis is a general finding without a file reference.\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        assert "transcript.critical.unspecified" in result

    def test_file_hotspots(self, transcripts_dir: Path) -> None:
        """Extracts file hotspots from FILE: lines."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "FILE: `src/mde/hooks/guard.py`\nsome finding\n"
            "FILE: `src/mde/hooks/guard.py`\nanother finding\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        hotspots = [p for p in result if p.startswith("transcript.hotspot.")]
        assert len(hotspots) == 2
        assert all(p == "transcript.hotspot.guard" for p in hotspots)

    def test_error_patterns(self, transcripts_dir: Path) -> None:
        """Extracts error/fix patterns from transcript content."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "The bug was in the authentication flow that caused login failures.\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        error_patterns = [p for p in result if p.startswith("transcript.error.")]
        assert len(error_patterns) >= 1

    def test_skips_commit_messages(self, transcripts_dir: Path) -> None:
        """Does not extract patterns from embedded commit log lines."""
        (transcripts_dir / "2026-03-31-abc.md").write_text(
            "4bb92d5 fix: gitignore transient logs\n"
        )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        error_patterns = [p for p in result if p.startswith("transcript.error.")]
        assert len(error_patterns) == 0

    def test_limits_to_last_50(self, transcripts_dir: Path) -> None:
        """Only processes the most recent 50 transcript files."""
        for i in range(60):
            (transcripts_dir / f"2026-03-{i:02d}-abc.md").write_text(
                "SEVERITY: critical\nFILE: `test.py`\n"
            )
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        critical_patterns = [p for p in result if p.startswith("transcript.critical.")]
        assert len(critical_patterns) == 50

    def test_case_insensitive_severity(self, transcripts_dir: Path) -> None:
        """Handles mixed case in SEVERITY markers."""
        (transcripts_dir / "2026-03-31-abc.md").write_text("severity: Critical\nFILE: `app.py`\n")
        with patch("mde.dream.extract.get_paths") as mock_paths:
            mock_paths.return_value.dir_transcripts = transcripts_dir
            result = _scan_transcripts()
        assert "transcript.critical.app" in result

    def test_unreadable_file_skipped(self, transcripts_dir: Path) -> None:
        """Gracefully handles unreadable files."""
        bad_file = transcripts_dir / "2026-03-31-abc.md"
        bad_file.write_text("content")
        bad_file.chmod(0o000)
        try:
            with patch("mde.dream.extract.get_paths") as mock_paths:
                mock_paths.return_value.dir_transcripts = transcripts_dir
                result = _scan_transcripts()
            assert result == []
        finally:
            bad_file.chmod(0o644)


class TestSlugify:
    """Tests for the _slugify helper."""

    def test_basic(self) -> None:
        assert _slugify("Hello World") == "hello_world"

    def test_special_chars(self) -> None:
        assert _slugify("src/mde/hooks/guard.py") == "src_mde_hooks_guard_py"

    def test_truncation(self) -> None:
        long_text = "a" * 100
        assert len(_slugify(long_text)) <= 40

    def test_strips_underscores(self) -> None:
        assert _slugify("  --hello--  ") == "hello"

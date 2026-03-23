"""Tests for memory stack validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from mde.validate.memory import validate_memory


class TestMemoryValidation:
    """Test memory stack config validation."""

    def test_passes_when_all_files_exist(self) -> None:
        with patch("mde.validate.memory.MEMORY_COMPOSE", spec=Path) as mock_compose:
            mock_compose.is_file.return_value = True
            init_sql = mock_compose.parent.__truediv__.return_value
            init_sql.is_file.return_value = True
            result = validate_memory()
            assert len(result.findings) == 0

    def test_warns_when_compose_missing(self) -> None:
        with patch("mde.validate.memory.MEMORY_COMPOSE", spec=Path) as mock_compose:
            mock_compose.is_file.return_value = False
            mock_compose.__str__ = lambda _self: "/fake/memory/compose.yaml"  # type: ignore[assignment]
            result = validate_memory()
            missing = [f for f in result.findings if "memory-compose" in f.rule]
            assert len(missing) == 1

    def test_returns_early_when_compose_missing(self) -> None:
        """When compose is missing, don't check init.sql."""
        with patch("mde.validate.memory.MEMORY_COMPOSE", spec=Path) as mock_compose:
            mock_compose.is_file.return_value = False
            mock_compose.__str__ = lambda _self: "/fake/memory/compose.yaml"  # type: ignore[assignment]
            result = validate_memory()
            # Should only have the compose-missing finding, not init-sql
            assert len(result.findings) == 1

    def test_warns_when_init_sql_missing(self) -> None:
        with patch("mde.validate.memory.MEMORY_COMPOSE", spec=Path) as mock_compose:
            mock_compose.is_file.return_value = True
            init_sql = mock_compose.parent.__truediv__.return_value
            init_sql.is_file.return_value = False
            init_sql.__str__ = lambda _self: "/fake/memory/init.sql"  # type: ignore[assignment]
            result = validate_memory()
            init_findings = [f for f in result.findings if "init-sql" in f.rule]
            assert len(init_findings) == 1

    def test_files_checked_incremented(self) -> None:
        with patch("mde.validate.memory.MEMORY_COMPOSE", spec=Path) as mock_compose:
            mock_compose.is_file.return_value = True
            init_sql = mock_compose.parent.__truediv__.return_value
            init_sql.is_file.return_value = True
            result = validate_memory()
            assert result.files_checked == 2

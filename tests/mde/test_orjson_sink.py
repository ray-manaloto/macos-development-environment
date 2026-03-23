"""Tests for orjson-powered loguru file sink."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import orjson
import pytest
from loguru import logger

from mde import observability

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def _reset_loguru() -> Generator[None]:
    """Remove all loguru sinks and reset module state for test isolation."""
    logger.remove()
    old_init = observability._initialized
    observability._initialized = False
    try:
        yield
    finally:
        observability._initialized = old_init
        logger.remove()


class TestOrjsonFormat:
    """Test the orjson format function for loguru file sink."""

    def test_serialize_produces_valid_json(self) -> None:
        """Orjson serialize function outputs parseable JSON lines."""
        from mde.observability import _orjson_serialize

        record: dict[str, object] = {
            "message": "test message",
            "level": SimpleNamespace(name="INFO", no=20),
            "time": "2026-03-23T00:00:00Z",
            "extra": {"key": "value"},
        }

        result = _orjson_serialize(record)
        assert result.endswith("\n")
        parsed = json.loads(result)
        assert parsed["message"] == "test message"
        assert parsed["text"] == "test message"
        assert parsed["level"] == "INFO"
        assert parsed["time"] == "2026-03-23T00:00:00Z"
        assert parsed["extra"]["key"] == "value"

    def test_serialize_preserves_extra_fields(self) -> None:
        """Extra fields from loguru record appear in JSON output."""
        from mde.observability import _orjson_serialize

        record: dict[str, object] = {
            "message": "bound message",
            "level": SimpleNamespace(name="DEBUG", no=10),
            "time": "2026-03-23T01:00:00Z",
            "extra": {"hook": "session_start", "exit_code": 0},
        }

        parsed = json.loads(_orjson_serialize(record))
        assert parsed["extra"]["hook"] == "session_start"
        assert parsed["extra"]["exit_code"] == 0

    def test_format_escapes_braces_for_loguru(self) -> None:
        """Format callback doubles braces so loguru .format_map() treats them as literals."""
        from mde.observability import _orjson_format

        record: dict[str, object] = {
            "message": "test",
            "level": SimpleNamespace(name="INFO", no=20),
            "time": "2026-03-23T00:00:00Z",
            "extra": {},
        }

        result = _orjson_format(record)
        # Braces should be doubled
        assert "{{" in result
        assert "}}" in result

    def test_orjson_is_hard_dependency(self) -> None:
        """Verify orjson is the serializer, not stdlib json."""
        from mde.observability import _orjson_serialize

        assert orjson is not None
        assert callable(_orjson_serialize)

    @pytest.mark.usefixtures("_reset_loguru")
    def test_format_works_as_loguru_sink(self, tmp_path: Path) -> None:
        """Orjson format integrates correctly as a loguru file sink format callback."""
        log_file = tmp_path / "test.jsonl"
        logger.add(str(log_file), format=observability._orjson_format, enqueue=False)

        logger.info("hello orjson")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["message"] == "hello orjson"
        assert parsed["level"] == "INFO"

    @pytest.mark.usefixtures("_reset_loguru")
    def test_format_handles_bound_context(self, tmp_path: Path) -> None:
        """Bound context from logger.bind() appears in orjson output."""
        log_file = tmp_path / "test.jsonl"
        logger.add(str(log_file), format=observability._orjson_format, enqueue=False)

        logger.bind(component="test").info("with context")

        parsed = json.loads(log_file.read_text().strip())
        assert parsed["extra"]["component"] == "test"

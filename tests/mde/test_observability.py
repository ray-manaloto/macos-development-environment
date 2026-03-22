"""Tests for the central observability module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from mde import observability


class TestInitObservability:
    """Tests for init_observability()."""

    def test_creates_log_dir(self, tmp_path: Path) -> None:
        """Verify log directory is created when it does not exist."""
        log_file = str(tmp_path / "nested" / "dir" / "events.jsonl")
        with patch.object(observability, "_initialized", False):
            observability.init_observability(log_file=log_file)
            observability._initialized = False
        assert Path(log_file).parent.exists()

    def test_idempotent(self, tmp_path: Path) -> None:
        """Calling init_observability twice does not error."""
        log_file = str(tmp_path / "events.jsonl")
        with patch.object(observability, "_initialized", False):
            observability.init_observability(log_file=log_file)
            observability.init_observability(log_file=log_file)  # second call is a no-op
            observability._initialized = False


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_bound_logger(self) -> None:
        """Verify get_logger returns a structlog bound logger with expected interface."""
        logger = observability.get_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "bind")
        assert hasattr(logger, "warning")


class TestGetTracer:
    """Tests for get_tracer()."""

    def test_returns_tracer(self) -> None:
        """Verify get_tracer returns an OTEL Tracer."""
        from opentelemetry.trace import Tracer

        tracer = observability.get_tracer("test")
        assert isinstance(tracer, Tracer)


class TestStructuredLogOutput:
    """Tests for structured log output."""

    def test_structured_log_output(self, tmp_path: Path) -> None:
        """Verify log events are written as valid JSON to the log file."""
        log_file = tmp_path / "test-events.jsonl"
        with patch.object(observability, "_initialized", False):
            observability.init_observability(log_file=str(log_file))
            observability._initialized = False

        logger = observability.get_logger("test-output")
        logger.info("hello world", extra_key="extra_value")

        # Flush the file handle so data is readable
        handle = observability._log_file_handle
        if handle is not None:
            handle.flush()  # type: ignore[union-attr]

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        record = json.loads(lines[-1])
        assert record["event"] == "hello world"
        assert record["extra_key"] == "extra_value"
        assert "timestamp" in record
        assert record["level"] == "info"

"""Tests for the loguru-based observability module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from mde import observability

if TYPE_CHECKING:
    from collections.abc import Generator

    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter


@pytest.fixture
def _reset_loguru() -> Generator[None]:
    """Remove all loguru sinks and reset module state for test isolation.

    Saves and restores _initialized, _otel_logger_provider, and _otel_logger
    to prevent test pollution. Uses enqueue=False for deterministic delivery.
    """
    logger.remove()
    old_init = observability._initialized
    old_provider = observability._otel_logger_provider
    old_otel_logger = observability._otel_logger
    observability._initialized = False
    try:
        yield
    finally:
        observability._initialized = old_init
        observability._otel_logger_provider = old_provider
        observability._otel_logger = old_otel_logger
        logger.remove()


@pytest.fixture
def otel_exporter(_reset_loguru: None) -> Generator[InMemoryLogRecordExporter]:
    """Set up an in-memory OTEL exporter wired to _otel_sink for testing."""
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import (
        InMemoryLogRecordExporter,
        SimpleLogRecordProcessor,
    )

    exporter = InMemoryLogRecordExporter()
    provider = LoggerProvider()
    provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))
    with (
        patch.object(observability, "_otel_logger_provider", provider),
        patch.object(observability, "_otel_logger", provider.get_logger("mde")),
    ):
        logger.add(observability._otel_sink, level="DEBUG", enqueue=False)
        yield exporter


class TestLoguruJsonSerialization:
    """Tests for loguru serialize=True JSON output."""

    @pytest.mark.usefixtures("_reset_loguru")
    def test_serialize_produces_valid_json(self, tmp_path: Path) -> None:
        """Loguru serialize=True writes one JSON object per log line."""
        log_file = tmp_path / "test.jsonl"
        logger.add(str(log_file), serialize=True, enqueue=False)

        logger.info("hello world")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["text"].strip().endswith("hello world")
        assert record["record"]["level"]["name"] == "INFO"

    @pytest.mark.usefixtures("_reset_loguru")
    def test_serialize_includes_extra_fields(self, tmp_path: Path) -> None:
        """Extra kwargs bound to logger appear in record.extra."""
        log_file = tmp_path / "test.jsonl"
        logger.add(str(log_file), serialize=True, enqueue=False)

        logger.bind(hook="guard_install").info("check passed")

        record = json.loads(log_file.read_text().strip())
        assert record["record"]["extra"]["hook"] == "guard_install"


class TestOtelSink:
    """Tests for _otel_sink emitting OTEL LogRecords."""

    def test_otel_sink_emits_log_record(self, otel_exporter: InMemoryLogRecordExporter) -> None:
        """_otel_sink forwards loguru messages to OTEL as LogRecords."""
        logger.info("test otel message")

        records = otel_exporter.get_finished_logs()
        assert len(records) == 1
        assert records[0].log_record.body == "test otel message"

    def test_otel_sink_maps_levels_correctly(
        self, otel_exporter: InMemoryLogRecordExporter
    ) -> None:
        """Loguru levels map to correct OTEL severity numbers."""
        logger.debug("d")
        logger.info("i")
        logger.warning("w")
        logger.error("e")
        logger.critical("c")

        records = otel_exporter.get_finished_logs()
        severities = [r.log_record.severity_number.value for r in records]
        # OTEL severity: DEBUG=5, INFO=9, WARN=13, ERROR=17, FATAL=21
        assert severities == [5, 9, 13, 17, 21]

    def test_otel_sink_includes_extra_as_attributes(
        self, otel_exporter: InMemoryLogRecordExporter
    ) -> None:
        """Extra fields from loguru appear as OTEL LogRecord attributes."""
        logger.bind(hook="session_start", exit_code=0).info("done")

        records = otel_exporter.get_finished_logs()
        attrs = dict(records[0].log_record.attributes or {})
        assert attrs["hook"] == "session_start"
        assert attrs["exit_code"] == "0"

    @pytest.mark.usefixtures("_reset_loguru")
    def test_otel_sink_noop_when_logger_is_none(self) -> None:
        """_otel_sink silently returns when _otel_logger is None."""
        with patch.object(observability, "_otel_logger", None):
            logger.add(observability._otel_sink, level="DEBUG", enqueue=False)
            # Should not raise — the None guard returns early
            logger.info("should not raise")


class TestProbeCollector:
    """Tests for _probe_collector() OTEL endpoint health check."""

    def test_returns_false_when_no_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns False when OTEL_EXPORTER_OTLP_ENDPOINT is not set."""
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        assert observability._probe_collector() is False

    def test_returns_false_on_connection_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns False when the collector is unreachable."""
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            assert observability._probe_collector() is False

    def test_returns_true_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns True when the collector responds with a non-5xx status."""
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        mock_resp = MagicMock(status=200)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            assert observability._probe_collector() is True

    def test_returns_false_on_server_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns False when the collector responds with 5xx."""
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        mock_resp = MagicMock(status=500)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            assert observability._probe_collector() is False


class TestGrpcToHttp:
    """Tests for _grpc_to_http port conversion."""

    def test_converts_standard_grpc_port(self) -> None:
        """Replaces :4317 with :4318."""
        assert observability._grpc_to_http("http://localhost:4317") == "http://localhost:4318"

    def test_noop_for_http_port(self) -> None:
        """Already-HTTP endpoint is unchanged."""
        assert observability._grpc_to_http("http://localhost:4318") == "http://localhost:4318"

    def test_noop_for_custom_port(self) -> None:
        """Non-standard ports are left unchanged."""
        assert observability._grpc_to_http("http://collector:9999") == "http://collector:9999"


class TestInitObservability:
    """Tests for init_observability() with loguru."""

    @pytest.mark.usefixtures("_reset_loguru")
    def test_creates_log_dir(self, tmp_path: Path) -> None:
        """Log directory is created when it does not exist."""
        log_file = str(tmp_path / "nested" / "dir" / "events.jsonl")
        observability.init_observability(log_file=log_file)
        assert Path(log_file).parent.exists()

    @pytest.mark.usefixtures("_reset_loguru")
    def test_idempotent(self, tmp_path: Path) -> None:
        """Calling init_observability twice does not error."""
        log_file = str(tmp_path / "events.jsonl")
        observability.init_observability(log_file=log_file)
        observability.init_observability(log_file=log_file)  # second call is a no-op

    @pytest.mark.usefixtures("_reset_loguru")
    def test_init_with_collector_sets_up_otel(self, tmp_path: Path) -> None:
        """When collector is reachable, OTEL sink and atexit handler are configured."""
        log_file = str(tmp_path / "events.jsonl")
        with (
            patch.object(observability, "_probe_collector", return_value=True),
            patch("atexit.register") as mock_atexit,
        ):
            observability.init_observability(log_file=log_file)
            assert observability._otel_logger_provider is not None
            assert observability._otel_logger is not None
            assert mock_atexit.call_count >= 1


class TestGetTracer:
    """Tests for get_tracer (unchanged — still OTEL)."""

    def test_returns_tracer(self) -> None:
        """get_tracer returns an OTEL Tracer."""
        from opentelemetry.trace import Tracer

        tracer = observability.get_tracer("test")
        assert isinstance(tracer, Tracer)


class TestLogFacade:
    """Tests for src/mde/log.py facade."""

    def test_facade_is_loguru_logger(self) -> None:
        """From mde.log import logger returns the loguru logger singleton."""
        from loguru import logger as loguru_logger

        from mde.log import logger as facade_logger

        assert facade_logger is loguru_logger

    def test_facade_exports_get_tracer(self) -> None:
        """From mde.log import get_tracer works."""
        from opentelemetry.trace import Tracer

        from mde.log import get_tracer

        tracer = get_tracer("test")
        assert isinstance(tracer, Tracer)

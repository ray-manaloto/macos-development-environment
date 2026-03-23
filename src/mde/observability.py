"""Central observability module: loguru logging, OTEL tracing, LLM instrumentation.

Provides a multi-sink setup where each log call goes to a JSON file, an OTEL
log exporter, and stderr (WARNING+). Safe to call ``init_observability()``
multiple times (idempotent).

Loguru replaces structlog + logfire. openlit stays for Anthropic SDK auto-instrumentation.
orjson is declared for use in PR A2 (LGTM stack) where log volume justifies Rust-speed JSON.
"""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from loguru import logger
from opentelemetry._logs.severity import SeverityNumber as _SeverityNumber

if TYPE_CHECKING:
    from loguru import Record
    from opentelemetry._logs import Logger as _OtelLogger
    from opentelemetry.sdk._logs import LoggerProvider as _LoggerProvider
    from opentelemetry.trace import Tracer

_initialized = False

# Module-level OTEL logger — set during init, patchable in tests.
_otel_logger_provider: _LoggerProvider | None = None
_otel_logger: _OtelLogger | None = None

# Loguru level → OTEL SeverityNumber mapping.
# SUCCESS is loguru-specific (no OTEL equivalent) → maps to INFO.
# CRITICAL → FATAL because OTEL has no CRITICAL severity.
_LEVEL_MAP: dict[str, _SeverityNumber] = {
    "TRACE": _SeverityNumber.TRACE,
    "DEBUG": _SeverityNumber.DEBUG,
    "INFO": _SeverityNumber.INFO,
    "SUCCESS": _SeverityNumber.INFO,
    "WARNING": _SeverityNumber.WARN,
    "ERROR": _SeverityNumber.ERROR,
    "CRITICAL": _SeverityNumber.FATAL,
}


def _otel_sink(message: str) -> None:
    """Forward loguru log records to OTEL as LogRecords.

    Loguru sink functions receive a ``str`` subclass with a ``.record`` attribute.

    Field mapping:
        loguru record["message"]  → OTEL body
        record["level"]["name"]   → OTEL severity_number (via _LEVEL_MAP)
        record["extra"]           → OTEL attributes (stringified values)
        record["time"]            → OTEL timestamp (nanoseconds)
    """
    if _otel_logger is None:
        return

    from opentelemetry._logs import LogRecord

    record = message.record  # type: ignore[union-attr]
    severity = _LEVEL_MAP.get(record["level"].name, _SeverityNumber.INFO)

    try:
        otel_record = LogRecord(
            body=record["message"],
            severity_number=severity,
            attributes={k: str(v) for k, v in record["extra"].items()},
            timestamp=int(record["time"].timestamp() * 1_000_000_000),
        )
        _otel_logger.emit(otel_record)
    except Exception:  # noqa: BLE001, S110
        pass  # OTEL delivery is best-effort; don't propagate to loguru


def _probe_collector() -> bool:
    """Check if the OTEL Collector endpoint is reachable and speaks OTLP.

    Returns True if the collector responds, False otherwise.
    Called once during ``init_observability()`` — NOT at import time.

    We send an invalid OTLP request (empty body). A 4xx response proves the
    collector is reachable and speaks OTLP. Only 5xx or connection failure
    means the collector is unavailable.
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return False
    try:
        from urllib.request import Request, urlopen

        http_endpoint = _grpc_to_http(endpoint)
        req = Request(  # noqa: S310
            f"{http_endpoint}/v1/traces", data=b"", method="POST"
        )
        req.add_header("Content-Type", "application/x-protobuf")
        resp = urlopen(req, timeout=1)  # noqa: S310
        return resp.status < 500  # noqa: TRY300, PLR2004
    except Exception:  # noqa: BLE001
        return False


def _grpc_to_http(endpoint: str) -> str:
    """Convert a gRPC OTLP endpoint to HTTP by replacing the standard port.

    Assumes OTEL_EXPORTER_OTLP_ENDPOINT uses gRPC port (4317).
    We probe and export via HTTP/protobuf (4318) since urllib doesn't speak gRPC.
    If the endpoint already uses 4318 or a non-standard port, this is a no-op.
    """
    return endpoint.replace(":4317", ":4318")


def _orjson_serialize(record: Record) -> str:
    """Serialize a loguru record to a JSON line using orjson.

    Returns a single JSON line (with trailing newline) containing selected fields.
    This is the raw serialization; use ``_orjson_format`` as the loguru format callback.
    """
    level = record["level"]
    data = {
        "text": record["message"],
        "message": record["message"],
        "level": level.name,
        "time": str(record["time"]),
        "extra": record["extra"],
    }
    return orjson.dumps(data).decode("utf-8") + "\n"


def _orjson_format(record: Record) -> str:
    """Loguru ``format`` callback — orjson JSON with escaped braces.

    Loguru calls ``.format_map()`` on the returned string, so literal
    ``{`` / ``}`` in JSON must be doubled to avoid ``KeyError``.
    """
    raw = _orjson_serialize(record)
    return raw.replace("{", "{{").replace("}", "}}")


def init_observability(
    service_name: str = "mde",
    log_file: str = ".artifacts/mde-events.jsonl",
) -> None:
    """Configure loguru sinks, OTEL log bridge, and openlit LLM instrumentation.

    Args:
        service_name: OTEL service name for traces and logs.
        log_file: Path to the JSONL log file (directory created if missing).
    """
    global _initialized  # noqa: PLW0603
    if _initialized:
        return

    # Create log directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Remove loguru default stderr handler
    logger.remove()

    # Sink 1: JSON file (async, rotation, retention) — orjson for Rust-speed serialization
    logger.add(
        log_file,
        format=_orjson_format,
        enqueue=True,
        rotation="10 MB",
        retention=5,
        level="DEBUG",
    )

    # Sink 2: stderr WARNING+ — synchronous for immediate visibility
    logger.add(sys.stderr, level="WARNING", colorize=True, enqueue=False)

    # Probe OTEL Collector — set up OTEL sink only if reachable
    os.environ.setdefault("OTEL_PYTHON_LOG_LEVEL", "fatal")
    if _probe_collector():
        _setup_otel_sink(service_name)
    else:
        os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
        os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
        os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")

    # Suppress noisy OTEL SDK loggers
    import logging

    for noisy in (
        "opentelemetry.exporter",
        "opentelemetry.sdk.trace.export",
        "opentelemetry.sdk.metrics.export",
        "urllib3.connectionpool",
    ):
        logging.getLogger(noisy).setLevel(logging.CRITICAL)

    # Auto-instrument Anthropic SDK calls (only when OTEL Collector is available).
    if os.environ.get("OTEL_TRACES_EXPORTER") != "none":
        import io

        import openlit

        _stderr = sys.stderr
        _capture = io.StringIO()
        sys.stderr = _capture
        try:
            openlit.init()
        finally:
            sys.stderr = _stderr
        captured = _capture.getvalue().strip()
        if captured:
            logger.debug("openlit_init_stderr: {output}", output=captured)

    _initialized = True


def _setup_otel_sink(service_name: str) -> None:
    """Initialize OTEL LoggerProvider and add the _otel_sink to loguru."""
    global _otel_logger_provider, _otel_logger  # noqa: PLW0603

    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    resource = Resource.create({"service.name": service_name})
    _otel_logger_provider = LoggerProvider(resource=resource)

    http_endpoint = _grpc_to_http(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""))
    exporter = OTLPLogExporter(endpoint=f"{http_endpoint}/v1/logs")

    _otel_logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    _otel_logger = _otel_logger_provider.get_logger(service_name)

    # Sink 3: OTEL log records — enqueue=False because BatchLogRecordProcessor
    # already handles async batching. Avoids double-async pipeline.
    logger.add(_otel_sink, enqueue=False, level="INFO")

    # Flush OTEL logs on process exit (BatchLogRecordProcessor buffers records).
    def _shutdown_otel() -> None:
        if _otel_logger_provider is not None:
            _otel_logger_provider.shutdown()

    atexit.register(_shutdown_otel)


def get_tracer(name: str = "mde") -> Tracer:
    """Return an OpenTelemetry tracer.

    Args:
        name: Tracer instrumentation scope name.
    """
    from opentelemetry import trace

    return trace.get_tracer(name)

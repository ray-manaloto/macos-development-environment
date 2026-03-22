"""Central observability module: structured logging, OTEL tracing, LLM instrumentation.

Provides a dual-sink setup where each log call goes to BOTH a structured JSON file
AND an OTEL exporter. Safe to call ``init_observability()`` multiple times (idempotent).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

# Probe OTEL Collector BEFORE importing logfire/OTEL SDK.
# If unreachable or not speaking OTLP, disable exporters to prevent noisy stderr spam.
_otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
_collector_ok = False
if _otel_endpoint:
    try:
        from urllib.request import Request, urlopen

        # OTLP HTTP health check — POST empty protobuf to /v1/traces
        _http_endpoint = _otel_endpoint.replace(":4317", ":4318")  # HTTP port
        _req = Request(  # noqa: S310
            f"{_http_endpoint}/v1/traces", data=b"", method="POST"
        )
        _req.add_header("Content-Type", "application/x-protobuf")
        urlopen(_req, timeout=1)  # noqa: S310
        _collector_ok = True
    except Exception:  # noqa: BLE001
        _collector_ok = False
if not _collector_ok:
    os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
    os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
    os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
os.environ.setdefault("OTEL_PYTHON_LOG_LEVEL", "fatal")

import logfire  # noqa: E402 — must be after env var setup
import structlog  # noqa: E402

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer

_initialized = False
_log_file_handle: object = None  # held open for the lifetime of the process


def init_observability(
    service_name: str = "mde",
    log_file: str = ".artifacts/mde-events.jsonl",
) -> None:
    """Configure structlog, logfire OTEL bridge, and openlit LLM instrumentation.

    Args:
        service_name: OTEL service name for traces and logs.
        log_file: Path to the JSONL log file (directory created if missing).
    """
    global _initialized, _log_file_handle  # noqa: PLW0603
    if _initialized:
        return

    # Create log directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # OTEL bridge — sends to any OTEL backend, NOT Logfire platform
    logfire.configure(
        service_name=service_name,
        send_to_logfire=False,
        console=False,  # don't duplicate to console — structlog handles output
    )

    # Keep file handle alive for the process lifetime
    _log_file_handle = Path(log_file).open("a")  # noqa: SIM115

    # structlog processor chain — each call goes to BOTH sinks
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            logfire.StructlogProcessor(),  # sink 1: OTEL export
            structlog.processors.JSONRenderer(),  # sink 2: structured JSON
        ],
        logger_factory=structlog.PrintLoggerFactory(file=_log_file_handle),
    )

    # Auto-instrument Anthropic SDK calls (only when OTEL Collector is available)
    if os.environ.get("OTEL_TRACES_EXPORTER") != "none":
        import openlit

        openlit.init()

    _initialized = True


def get_logger(name: str = "mde") -> structlog.BoundLogger:
    """Return a configured structlog bound logger.

    Args:
        name: Logger name (used as the ``logger_name`` context variable).
    """
    return structlog.get_logger(name)


def get_tracer(name: str = "mde") -> Tracer:
    """Return an OpenTelemetry tracer.

    Args:
        name: Tracer instrumentation scope name.
    """
    from opentelemetry import trace

    return trace.get_tracer(name)

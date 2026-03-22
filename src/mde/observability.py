"""Central observability module: structured logging, OTEL tracing, LLM instrumentation.

Provides a dual-sink setup where each log call goes to BOTH a structured JSON file
AND an OTEL exporter. Safe to call ``init_observability()`` multiple times (idempotent).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer

_initialized = False
_log_file_handle: IO[str] | None = None


def _probe_collector() -> bool:
    """Check if the OTEL Collector endpoint is reachable and speaks OTLP.

    Returns True if the collector responds, False otherwise.
    Called once during ``init_observability()`` — NOT at import time.
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return False
    try:
        from urllib.request import Request, urlopen

        http_endpoint = endpoint.replace(":4317", ":4318")
        req = Request(  # noqa: S310
            f"{http_endpoint}/v1/traces", data=b"", method="POST"
        )
        req.add_header("Content-Type", "application/x-protobuf")
        urlopen(req, timeout=1)  # noqa: S310
    except Exception:  # noqa: BLE001
        return False
    else:
        return True


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

    # Probe OTEL Collector — disable exporters if unreachable to prevent stderr spam.
    # Must happen BEFORE logfire.configure() which sets up OTEL SDK exporters.
    os.environ.setdefault("OTEL_PYTHON_LOG_LEVEL", "fatal")
    if not _probe_collector():
        os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
        os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
        os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")

    # Suppress noisy OTEL exporter log messages
    import logging

    for noisy_logger in (
        "opentelemetry.exporter",
        "opentelemetry.sdk.trace.export",
        "opentelemetry.sdk.metrics.export",
        "urllib3.connectionpool",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.CRITICAL)

    # OTEL bridge — sends to any OTEL backend, NOT Logfire platform
    import logfire

    logfire.configure(
        service_name=service_name,
        send_to_logfire=False,
        console=False,
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

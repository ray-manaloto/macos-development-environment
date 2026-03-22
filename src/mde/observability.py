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
        resp = urlopen(req, timeout=1)  # noqa: S310
        # OTLP endpoints return 200 or 4xx — 5xx means wrong service
        return resp.status < 500  # noqa: TRY300, PLR2004
    except Exception:  # noqa: BLE001
        return False


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

    # Probe OTEL Collector HTTP endpoint — disable exporters if unreachable.
    # Claude Code's built-in telemetry uses gRPC on :4317 (settings.json).
    # Logfire uses HTTP on :4318 (Protobuf over HTTP, not gRPC).
    # We probe :4318 and disable exporters if no valid OTLP HTTP response.
    os.environ.setdefault("OTEL_PYTHON_LOG_LEVEL", "fatal")
    if not _probe_collector():
        os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
        os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
        os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
        # Clear the gRPC endpoint so logfire doesn't try HTTP on the gRPC port
        os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    # Suppress noisy OTEL exporter log messages
    import logging

    for noisy_logger in (
        "opentelemetry.exporter",
        "opentelemetry.sdk.trace.export",
        "opentelemetry.sdk.metrics.export",
        "urllib3.connectionpool",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.CRITICAL)

    # OTEL bridge — sends to any OTEL backend, NOT Logfire platform.
    # Logfire uses HTTP (not gRPC), so point it at the HTTP port (:4318).
    # Claude Code's built-in telemetry handles gRPC on :4317 separately.
    import logfire

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if otlp_endpoint and ":4317" in otlp_endpoint:
        http_endpoint = otlp_endpoint.replace(":4317", ":4318")
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{http_endpoint}/v1/traces"
        os.environ["OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"] = f"{http_endpoint}/v1/metrics"
        os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] = f"{http_endpoint}/v1/logs"

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

    # Auto-instrument Anthropic SDK calls (only when OTEL Collector is available).
    # Redirect stderr briefly to suppress "Overriding provider" messages from
    # openlit competing with logfire for OTEL provider registration.
    if os.environ.get("OTEL_TRACES_EXPORTER") != "none":
        import io
        import sys

        import openlit

        _stderr = sys.stderr
        sys.stderr = io.StringIO()  # suppress "Overriding provider" messages
        try:
            openlit.init()
        finally:
            sys.stderr = _stderr

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

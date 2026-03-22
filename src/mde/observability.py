"""Central observability module: structured logging, OTEL tracing, LLM instrumentation.

Provides a dual-sink setup where each log call goes to BOTH a structured JSON file
AND an OTEL exporter. Safe to call ``init_observability()`` multiple times (idempotent).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import logfire
import structlog

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
    logfire.configure(service_name=service_name, send_to_logfire=False)

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

    # Auto-instrument Anthropic SDK calls
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

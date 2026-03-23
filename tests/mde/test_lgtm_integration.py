"""Integration tests for LGTM observability stack.

These tests require the Docker stack to be running:
    mise run mde:observability:up

Skip automatically when stack is unavailable.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from urllib.parse import quote

import pytest

_logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestLGTMIntegration:
    """Integration tests — only run when Docker stack is up."""

    def test_trace_appears_in_tempo(self, lgtm_stack_running: None) -> None:
        """Send a test span and verify it appears in Tempo."""
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        # Unique ID for this test run
        test_id = f"test-{uuid.uuid4().hex[:8]}"

        provider = TracerProvider(resource=Resource.create({"service.name": "mde-test"}))
        exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("mde-integration-test")
        with tracer.start_as_current_span("integration-test") as span:
            span.set_attribute("test.id", test_id)

        provider.force_flush()
        provider.shutdown()

        # Poll Tempo for the trace (exponential backoff)
        from urllib.request import Request, urlopen

        delay = 0.5
        found = False
        for _ in range(8):  # max ~15s total
            time.sleep(delay)
            try:
                url = f"http://127.0.0.1:3200/api/search?tags=test.id%3D{test_id}"
                req = Request(url)  # noqa: S310
                resp = urlopen(req, timeout=5)  # noqa: S310
                data = json.loads(resp.read().decode())
                if data.get("traces"):
                    found = True
                    break
            except Exception:  # noqa: BLE001
                _logger.debug("Tempo poll failed", exc_info=True)
            delay = min(delay * 2, 15)

        assert found, f"Trace with test.id={test_id} not found in Tempo after polling"

    def test_log_appears_in_loki(self, lgtm_stack_running: None) -> None:
        """Send a test log via OTEL and verify it appears in Loki."""
        from opentelemetry._logs import LogRecord
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
        from opentelemetry.sdk.resources import Resource

        test_id = f"test-{uuid.uuid4().hex[:8]}"

        provider = LoggerProvider(resource=Resource.create({"service.name": "mde-test"}))
        exporter = OTLPLogExporter(endpoint="http://127.0.0.1:4318/v1/logs")
        provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))

        otel_logger = provider.get_logger("mde-integration-test")
        otel_logger.emit(LogRecord(body=f"integration-test-log-{test_id}"))

        provider.force_flush()
        provider.shutdown()

        # Poll Loki
        from urllib.request import urlopen

        delay = 0.5
        found = False
        query = quote(f'{{service_name="mde-test"}} |= "{test_id}"')
        for _ in range(8):
            time.sleep(delay)
            try:
                url = f"http://127.0.0.1:3100/loki/api/v1/query?query={query}"
                resp = urlopen(url, timeout=5)  # noqa: S310
                data = json.loads(resp.read().decode())
                streams = data.get("data", {}).get("result", [])
                if streams:
                    found = True
                    break
            except Exception:  # noqa: BLE001
                _logger.debug("Loki poll failed", exc_info=True)
            delay = min(delay * 2, 15)

        assert found, f"Log with test_id={test_id} not found in Loki after polling"

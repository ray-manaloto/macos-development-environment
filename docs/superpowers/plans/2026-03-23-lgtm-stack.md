# LGTM Docker Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the standalone `codex-otel-collector` with a Docker Compose LGTM stack (Collector + Tempo + Loki + Grafana) that stores and visualizes Claude Code and mde telemetry data.

**Architecture:** OTEL Collector receives OTLP on localhost:4317/4318, redacts sensitive attributes via transform processor, fans out to Tempo (traces) and Loki (logs) over the Docker internal network. Grafana auto-provisions both as datasources. All ports bound to 127.0.0.1, containers hardened with read-only filesystem and dropped capabilities.

**Tech Stack:** Docker Compose, OTEL Collector Contrib, Grafana, Tempo, Loki, Python (loguru, orjson, argparse), pytest

**Spec:** `docs/superpowers/specs/2026-03-22-lgtm-stack-design.md`

---

## File Structure

| Path | Action | Responsibility |
|------|--------|----------------|
| `docker/observability/docker-compose.yml` | Create | LGTM stack with profiles, resource limits, hardening |
| `docker/observability/collector-config.yaml` | Create | OTEL Collector: receive → transform → batch → fan-out |
| `docker/observability/grafana/provisioning/datasources/datasources.yaml` | Create | Auto-provision Tempo + Loki datasources |
| `src/mde/domain/observability_stack.py` | Create | Stack lifecycle: up/down/status logic |
| `src/mde/cli.py` | Modify | Add `observability` subcommand + dispatch entry |
| `src/mde/observability.py` | Modify | Wire orjson into file sink |
| `src/mde/telemetry_verify.py` | Modify | Add pipeline/identity checks |
| `.mise.toml` | Modify | Add `mde:observability:{up,down,status}` tasks |
| `tests/mde/test_observability_stack.py` | Create | Unit tests for stack management |
| `tests/mde/test_orjson_sink.py` | Create | Unit tests for orjson serialization |
| `tests/mde/test_lgtm_integration.py` | Create | Integration tests (Tempo/Loki queries) |
| `tests/conftest.py` | Create | `integration` marker + `lgtm_stack_running` fixture |
| `pyproject.toml` | Modify | Register `integration` pytest marker |
| `configs/grafana-stack/` | Delete | Superseded by `docker/observability/` |

---

### Task 1: Docker Compose Infrastructure

**Files:**
- Create: `docker/observability/docker-compose.yml`
- Create: `docker/observability/collector-config.yaml`
- Create: `docker/observability/grafana/provisioning/datasources/datasources.yaml`

- [ ] **Step 1: Create docker/observability/ directory structure**

```bash
mkdir -p docker/observability/grafana/provisioning/datasources
```

- [ ] **Step 2: Write collector-config.yaml**

OTEL Collector config with receive → transform (redact secrets) → batch → fan-out.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

processors:
  batch:
    send_batch_size: 64
    timeout: 2s
    send_batch_max_size: 128

  transform:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          # Redact attributes with secret-like names
          - delete_key(attributes, "api_key") where IsMatch(attributes["api_key"], ".*")
          - replace_pattern(attributes, ".*\\.api_key", "[REDACTED]")
          - replace_pattern(attributes, ".*\\.token", "[REDACTED]")
          - replace_pattern(attributes, ".*\\.secret", "[REDACTED]")
          - replace_pattern(attributes, ".*\\.password", "[REDACTED]")
          - replace_pattern(attributes, ".*\\.credential", "[REDACTED]")
          # Redact known API key prefixes in all attribute values
          - replace_all_matches(attributes, "sk-ant-.*", "[REDACTED]")
          - replace_all_matches(attributes, "ghp_.*", "[REDACTED]")
          - replace_all_matches(attributes, "gho_.*", "[REDACTED]")
          - replace_all_matches(attributes, "sk-.*", "[REDACTED]")
    log_statements:
      - context: log
        statements:
          - replace_all_matches(attributes, "sk-ant-.*", "[REDACTED]")
          - replace_all_matches(attributes, "ghp_.*", "[REDACTED]")
          - replace_all_matches(attributes, "sk-.*", "[REDACTED]")

exporters:
  otlphttp/tempo:
    endpoint: "http://tempo:4318"
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
  debug:
    verbosity: basic

extensions:
  health_check:
    endpoint: "0.0.0.0:13133"

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [transform, batch]
      exporters: [otlphttp/tempo, debug]
    logs:
      receivers: [otlp]
      processors: [transform, batch]
      exporters: [loki, debug]
```

Note: The exact transform processor OTTL syntax must be validated against the
`otel/opentelemetry-collector-contrib` image version. Look up the transform
processor docs for the pinned image version. The above is the intent — adjust
OTTL statements to match the actual API.

- [ ] **Step 3: Write docker-compose.yml**

Pin ALL image digests. To get current digests:
```bash
docker pull otel/opentelemetry-collector-contrib:0.107.0
docker inspect --format='{{index .RepoDigests 0}}' otel/opentelemetry-collector-contrib:0.107.0
# Repeat for grafana/grafana, grafana/tempo, grafana/loki
```

```yaml
name: mde-observability

services:
  collector:
    image: otel/opentelemetry-collector-contrib:0.107.0@sha256:<DIGEST>
    volumes:
      - ./collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro
    ports:
      - "127.0.0.1:4317:4317"
      - "127.0.0.1:4318:4318"
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:13133/health"]
      interval: 5s
      timeout: 2s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 256m
    cpus: 0.5
    depends_on:
      tempo:
        condition: service_healthy
      loki:
        condition: service_healthy

  tempo:
    image: grafana/tempo:2.5.0@sha256:<DIGEST>
    command: ["-config.file=/etc/tempo/config.yaml"]
    volumes:
      - tempo-data:/var/tempo
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3200/ready"]
      interval: 5s
      timeout: 2s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 512m
    cpus: 0.5

  loki:
    image: grafana/loki:2.9.8@sha256:<DIGEST>
    command: ["-config.file=/etc/loki/local-config.yaml"]
    volumes:
      - loki-data:/loki
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3100/ready"]
      interval: 5s
      timeout: 2s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 512m
    cpus: 0.5

  grafana:
    image: grafana/grafana:11.1.0@sha256:<DIGEST>
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-}
      - GF_AUTH_ANONYMOUS_ENABLED=false
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/api/health"]
      interval: 5s
      timeout: 2s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 256m
    cpus: 0.25
    depends_on:
      tempo:
        condition: service_healthy
      loki:
        condition: service_healthy

volumes:
  tempo-data:
  loki-data:
  grafana-data:
```

Replace each `<DIGEST>` with the actual sha256 digest from the docker inspect step.

- [ ] **Step 4: Write Grafana datasource provisioning**

```yaml
# docker/observability/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

- [ ] **Step 5: Validate compose config**

```bash
docker compose -f docker/observability/docker-compose.yml config --quiet
```
Expected: exit 0, no errors.

- [ ] **Step 6: Commit**

```bash
git add docker/observability/
git commit -m "feat: add LGTM Docker Compose stack with hardened containers"
```

---

### Task 2: Stack Management Module

**Files:**
- Create: `src/mde/domain/observability_stack.py`
- Modify: `src/mde/cli.py:35-141` (parser), `src/mde/cli.py:448-467` (dispatch table)
- Create: `tests/mde/test_observability_stack.py`

- [ ] **Step 1: Write failing tests for observability_stack module**

Create `tests/mde/test_observability_stack.py`:

```python
"""Tests for observability stack management."""

from __future__ import annotations

from unittest.mock import patch

from mde.domain.observability_stack import (
    COMPOSE_FILE,
    stack_down,
    stack_status,
    stack_up,
    stop_orphan_collectors,
)


class TestStopOrphanCollectors:
    """Test legacy codex-otel-collector detection and removal."""

    def test_stops_codex_collector(self) -> None:
        mock_ps = "codex-otel-collector\totel/opentelemetry-collector-contrib:0.107.0\tUp 2 hours"
        with (
            patch("subprocess.run") as mock_run,
        ):
            # First call: docker ps
            mock_run.return_value.stdout = mock_ps
            mock_run.return_value.returncode = 0
            stop_orphan_collectors()
            # Should have called docker stop
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("stop" in c and "codex-otel-collector" in c for c in calls)

    def test_noop_when_no_orphans(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            stop_orphan_collectors()
            # Only the ps call, no stop
            assert mock_run.call_count == 1


class TestStackUp:
    """Test stack_up validates GRAFANA_PASSWORD and starts compose."""

    def test_fails_without_grafana_password(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = stack_up()
            assert result != 0

    def test_succeeds_with_grafana_password(self) -> None:
        with (
            patch.dict("os.environ", {"GRAFANA_PASSWORD": "test123"}),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result = stack_up()
            assert result == 0


class TestComposeFile:
    """Test compose file path is correct."""

    def test_compose_file_path(self) -> None:
        assert COMPOSE_FILE.name == "docker-compose.yml"
        assert "docker/observability" in str(COMPOSE_FILE)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_observability_stack.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'mde.domain.observability_stack'`

- [ ] **Step 3: Implement observability_stack.py**

Create `src/mde/domain/observability_stack.py`:

```python
"""Observability stack lifecycle management.

Manages the Docker Compose LGTM stack (OTEL Collector + Tempo + Loki + Grafana).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

COMPOSE_FILE = Path(__file__).resolve().parents[3] / "docker" / "observability" / "docker-compose.yml"


def stop_orphan_collectors() -> None:
    """Detect and stop legacy codex-otel-collector containers."""
    import subprocess

    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return

    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 1 and "codex-otel-collector" in parts[0]:
            print(f"  Stopping orphan collector: {parts[0]}", file=sys.stderr)
            subprocess.run(
                ["docker", "stop", parts[0]],
                capture_output=True,
                timeout=30,
            )


def stack_up() -> int:
    """Start the LGTM observability stack.

    Validates GRAFANA_PASSWORD is set, stops orphan collectors, then starts compose.
    """
    import subprocess

    password = os.environ.get("GRAFANA_PASSWORD", "")
    if not password:
        print(
            "ERROR: GRAFANA_PASSWORD not set. "
            "Add it to macOS Keychain: security add-generic-password -s GRAFANA_PASSWORD -a mde -w '<password>'",
            file=sys.stderr,
        )
        return 1

    if not COMPOSE_FILE.is_file():
        print(f"ERROR: Compose file not found: {COMPOSE_FILE}", file=sys.stderr)
        return 1

    stop_orphan_collectors()

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "--wait"],
        timeout=120,
    )
    return result.returncode


def stack_down() -> int:
    """Stop the LGTM observability stack."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
        timeout=60,
    )
    return result.returncode


def stack_status() -> int:
    """Show LGTM stack container status."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "table"],
        timeout=10,
    )
    return result.returncode


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'observability' subcommand and its children."""
    obs_p = sub.add_parser("observability", help="LGTM observability stack management")
    obs_sub = obs_p.add_subparsers(dest="observability_action")
    obs_sub.add_parser("up", help="Start the observability stack")
    obs_sub.add_parser("down", help="Stop the observability stack")
    obs_sub.add_parser("status", help="Show stack container status")


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct observability subcommand handler."""
    action = getattr(args, "observability_action", None)
    if action == "up":
        return stack_up()
    if action == "down":
        return stack_down()
    if action == "status":
        return stack_status()
    print("Usage: mde-py observability {up,down,status}", file=sys.stderr)
    return 1
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/mde/test_observability_stack.py -v
```
Expected: all PASS

- [ ] **Step 5: Wire into cli.py**

In `src/mde/cli.py`, add observability subparsers in `_build_parser()` after the
statusline block (around line 139):

```python
    # observability
    from mde.domain.observability_stack import add_subparsers as _add_obs_subparsers
    _add_obs_subparsers(sub)
```

Add the dispatch handler after `_cmd_statusline`:

```python
def _cmd_observability(args: argparse.Namespace) -> int:
    with _traced_command("observability") as ctx:
        from mde.domain.observability_stack import dispatch as obs_dispatch

        result = obs_dispatch(args)
        ctx["result"] = result
        return result
```

Add to `_DISPATCH_TABLE`:

```python
    "observability": _cmd_observability,
```

- [ ] **Step 6: Run quality gate**

```bash
uv run mde-py quality
```
Expected: 6/6 passed

- [ ] **Step 7: Commit**

```bash
git add src/mde/domain/observability_stack.py src/mde/cli.py tests/mde/test_observability_stack.py
git commit -m "feat: add observability stack management (up/down/status)"
```

---

### Task 3: Mise Tasks

**Files:**
- Modify: `.mise.toml`

- [ ] **Step 1: Add observability tasks to .mise.toml**

Add after the existing `mde:quality` task block:

```toml
[tasks."mde:observability:up"]
description = "Start LGTM observability stack (Collector + Tempo + Loki + Grafana)"
run = "uv run mde-py observability up"

[tasks."mde:observability:down"]
description = "Stop LGTM observability stack"
run = "uv run mde-py observability down"

[tasks."mde:observability:status"]
description = "Show LGTM observability stack status"
run = "uv run mde-py observability status"
```

- [ ] **Step 2: Verify mise tasks register**

```bash
mise tasks | grep observability
```
Expected: three tasks listed

- [ ] **Step 3: Commit**

```bash
git add .mise.toml
git commit -m "feat: add mise tasks for observability stack management"
```

---

### Task 4: orjson File Sink

**Files:**
- Create: `tests/mde/test_orjson_sink.py`
- Modify: `src/mde/observability.py:135-143`

- [ ] **Step 1: Write failing tests**

Create `tests/mde/test_orjson_sink.py`:

```python
"""Tests for orjson-powered loguru file sink."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import orjson


class TestOrjsonFormat:
    """Test the orjson format function for loguru file sink."""

    def test_format_produces_valid_json(self, tmp_path: Path) -> None:
        """orjson format function outputs parseable JSON lines."""
        from mde.observability import _orjson_format

        # Simulate a loguru record dict
        record = {
            "text": "test message",
            "record": {
                "message": "test message",
                "level": {"name": "INFO", "no": 20},
                "time": "2026-03-23T00:00:00Z",
                "extra": {"key": "value"},
            },
        }

        class FakeMessage(str):
            record = record["record"]

        result = _orjson_format(FakeMessage(record["text"]))
        # Should be valid JSON ending with newline
        assert result.endswith("\n")
        parsed = json.loads(result)
        assert parsed["message"] == "test message"

    def test_orjson_used_not_stdlib(self) -> None:
        """Verify orjson is the serializer, not stdlib json."""
        from mde.observability import _orjson_format

        # orjson is a hard dependency — import should not be conditional
        assert orjson is not None
        # The function should exist (not guarded by try/except)
        assert callable(_orjson_format)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_orjson_sink.py -v
```
Expected: FAIL — `ImportError: cannot import name '_orjson_format'`

- [ ] **Step 3: Implement orjson format function in observability.py**

At the top of `src/mde/observability.py`, add after existing imports:

```python
import orjson
```

Add the format function before `init_observability()`:

```python
def _orjson_format(message: str) -> str:
    """Format a loguru record as JSON using orjson.

    Loguru passes a ``str`` subclass with a ``.record`` attribute to format functions.
    We serialize the record dict with orjson (Rust-speed) instead of stdlib json.
    """
    record = message.record  # type: ignore[union-attr]
    data = {
        "text": record["message"],
        "message": record["message"],
        "level": record["level"].name,
        "time": str(record["time"]),
        "extra": record["extra"],
    }
    return orjson.dumps(data).decode("utf-8") + "\n"
```

Then modify the file sink in `init_observability()` — replace `serialize=True`
with the `format` parameter:

Change (line ~136-143):
```python
    logger.add(
        log_file,
        serialize=True,
        enqueue=True,
        rotation="10 MB",
        retention=5,
        level="DEBUG",
    )
```

To:
```python
    logger.add(
        log_file,
        format=_orjson_format,
        enqueue=True,
        rotation="10 MB",
        retention=5,
        level="DEBUG",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/mde/test_orjson_sink.py -v
```
Expected: all PASS

- [ ] **Step 5: Run full quality gate (orjson change affects existing tests)**

```bash
uv run mde-py quality
```
Expected: 6/6 passed. If existing observability tests fail, adjust them to
account for the new format function.

- [ ] **Step 6: Commit**

```bash
git add src/mde/observability.py tests/mde/test_orjson_sink.py
git commit -m "feat: wire orjson into loguru file sink for faster JSON serialization"
```

---

### Task 5: Telemetry Verify Updates

**Files:**
- Modify: `src/mde/telemetry_verify.py`
- Modify: `tests/mde/test_telemetry_verify.py`

- [ ] **Step 1: Write failing tests for new verify checks**

Add to `tests/mde/test_telemetry_verify.py`:

```python
class TestCheckCollectorPipelines:
    """Test _check_collector_pipelines pure function."""

    def test_passes_with_non_debug_exporters(self, tmp_path: Path) -> None:
        config = tmp_path / "collector-config.yaml"
        config.write_text(
            "exporters:\n  otlphttp/tempo:\n    endpoint: http://tempo:4318\n"
            "service:\n  pipelines:\n    traces:\n      exporters: [otlphttp/tempo]\n"
        )
        results = _check_collector_pipelines(config)
        assert all(s == "OK" for _, s, _ in results)

    def test_warns_debug_only_exporters(self, tmp_path: Path) -> None:
        config = tmp_path / "collector-config.yaml"
        config.write_text(
            "exporters:\n  debug:\n    verbosity: basic\n"
            "service:\n  pipelines:\n    traces:\n      exporters: [debug]\n"
        )
        results = _check_collector_pipelines(config)
        statuses = [s for _, s, _ in results]
        assert "WARNING" in statuses

    def test_returns_error_for_missing_file(self, tmp_path: Path) -> None:
        results = _check_collector_pipelines(tmp_path / "nonexistent.yaml")
        statuses = [s for _, s, _ in results]
        assert "FAIL" in statuses
```

Import `_check_collector_pipelines` from `mde.telemetry_verify` at the top of the test file.

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_telemetry_verify.py::TestCheckCollectorPipelines -v
```
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement _check_collector_pipelines**

Add to `src/mde/telemetry_verify.py`:

```python
def _check_collector_pipelines(config_path: Path) -> list[tuple[str, str, str]]:
    """Check that the OTEL Collector config has non-debug exporters.

    Args:
        config_path: Path to the collector-config.yaml file.

    Returns:
        List of (check_name, status, detail) tuples.
    """
    import yaml

    results: list[tuple[str, str, str]] = []

    if not config_path.is_file():
        results.append(("collector-config", "FAIL", f"config not found: {config_path}"))
        return results

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        results.append(("collector-config", "FAIL", f"failed to parse: {exc}"))
        return results

    pipelines = data.get("service", {}).get("pipelines", {})
    for pipeline_name, pipeline in pipelines.items():
        exporters = pipeline.get("exporters", [])
        non_debug = [e for e in exporters if not e.startswith("debug")]
        if non_debug:
            results.append((
                f"pipeline:{pipeline_name}",
                "OK",
                f"non-debug exporters: {non_debug}",
            ))
        else:
            results.append((
                f"pipeline:{pipeline_name}",
                "WARNING",
                "only debug exporter configured — data is not stored",
            ))

    if not pipelines:
        results.append(("collector-config", "WARNING", "no pipelines defined"))

    return results
```

Also wire `_check_collector_pipelines` into `verify_telemetry()` by adding a new
section to the `sections` list:

```python
    ("Collector Pipelines", _check_collector_pipelines(
        Path(__file__).resolve().parents[2] / "docker" / "observability" / "collector-config.yaml"
    )),
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/mde/test_telemetry_verify.py -v
```
Expected: all PASS

- [ ] **Step 5: Run quality gate**

```bash
uv run mde-py quality
```
Expected: 6/6 passed

- [ ] **Step 6: Commit**

```bash
git add src/mde/telemetry_verify.py tests/mde/test_telemetry_verify.py
git commit -m "feat: add collector pipeline validation to telemetry verify"
```

---

### Task 6: Integration Tests + pytest Marker

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/mde/test_lgtm_integration.py`
- Modify: `pyproject.toml` (add marker)

- [ ] **Step 1: Verify integration marker exists in pyproject.toml**

The `integration` marker is already registered in `pyproject.toml:156-158`:
```toml
markers = [
    "integration: tests requiring external tools (mise, chezmoi, docker, gh)",
]
```
No changes needed — the existing marker covers Docker-dependent tests.

- [ ] **Step 2: Create conftest.py with lgtm_stack_running fixture**

Create `tests/conftest.py`:

```python
"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def lgtm_stack_running() -> None:
    """Skip test if LGTM observability stack is not running.

    Probes the OTEL Collector health endpoint on localhost:13133.
    """
    try:
        from urllib.request import urlopen

        resp = urlopen("http://127.0.0.1:13133/health", timeout=2)  # noqa: S310
        if resp.status >= 500:  # noqa: PLR2004
            pytest.skip("LGTM stack: collector unhealthy")
    except Exception:  # noqa: BLE001
        pytest.skip("LGTM stack not running (collector health endpoint unreachable)")
```

- [ ] **Step 3: Write integration tests**

Create `tests/mde/test_lgtm_integration.py`:

```python
"""Integration tests for LGTM observability stack.

These tests require the Docker stack to be running:
    mise run mde:observability:up

Skip automatically when stack is unavailable.
"""

from __future__ import annotations

import json
import time
import uuid

import pytest


@pytest.mark.integration
class TestLGTMIntegration:
    """Integration tests — only run when Docker stack is up."""

    def test_trace_appears_in_tempo(self, lgtm_stack_running: None) -> None:
        """Send a test span and verify it appears in Tempo."""
        from opentelemetry import trace
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
                pass
            delay = min(delay * 2, 4)

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
        from urllib.parse import quote

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
                pass
            delay = min(delay * 2, 4)

        assert found, f"Log with test_id={test_id} not found in Loki after polling"
```

- [ ] **Step 4: Run integration tests (skip expected if stack not running)**

```bash
uv run pytest tests/mde/test_lgtm_integration.py -v
```
Expected: SKIPPED (unless Docker stack is up, then PASS)

- [ ] **Step 5: Run full quality gate**

```bash
uv run mde-py quality
```
Expected: 6/6 passed (integration tests skipped in default run)

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/mde/test_lgtm_integration.py pyproject.toml
git commit -m "feat: add LGTM integration tests with Tempo/Loki query polling"
```

---

### Task 7: Remove Legacy Compose + Final Verification

**Files:**
- Delete: `configs/grafana-stack/` (if exists)
- Verify: full stack end-to-end

- [ ] **Step 1: Check if legacy compose exists and remove**

```bash
ls configs/grafana-stack/ 2>/dev/null
```

If it exists:
```bash
git rm -r configs/grafana-stack/
```

- [ ] **Step 2: Start the stack**

```bash
mise run mde:observability:up
```
Expected: all 4 containers start and become healthy.

- [ ] **Step 3: Run telemetry verify**

```bash
uv run mde-py telemetry verify
```
Expected: all checks pass, including new pipeline checks.

- [ ] **Step 4: Run integration tests with stack up**

```bash
uv run pytest tests/mde/test_lgtm_integration.py -v
```
Expected: both tests PASS (traces in Tempo, logs in Loki).

- [ ] **Step 5: Run full quality gate**

```bash
uv run mde-py quality
```
Expected: 6/6 passed, 278+ tests.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: remove legacy grafana-stack, all verification passes"
```

---

## Execution Order

Tasks 1-3 can be parallelized (Docker infra, Python module, mise tasks have
separate file ownership). Task 4 (orjson) and Task 5 (telemetry verify) can
also run in parallel. Task 6 (integration tests) depends on Tasks 1-2. Task 7
depends on all previous tasks.

```
Task 1 (Docker) ──────┐
Task 2 (Stack module) ─┼── Task 6 (Integration tests) ── Task 7 (Final)
Task 3 (Mise tasks) ───┘
Task 4 (orjson) ────────────────────── (independent, no downstream deps)
Task 5 (Telemetry verify) ──────────── Task 7 (Final)
```

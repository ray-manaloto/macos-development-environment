"""Tests for telemetry source configuration and data arrival checks."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from mde.telemetry_verify import (
    _check_data_arrival_loki,
    _check_data_arrival_tempo,
    _check_source_configs,
)


def _make_path_factory(file_map: dict[str, str | bool] | None = None) -> MagicMock:
    """Create a Path mock factory that routes is_file/read_text by substring match.

    Args:
        file_map: Dict mapping substring patterns to either:
            - str: file content (is_file=True, read_text returns content)
            - True: file exists but no content needed (is_file=True)
            - False or missing: file does not exist (is_file=False)
    """
    if file_map is None:
        file_map = {}

    def make_path(arg: object) -> MagicMock:
        p = MagicMock()
        s = str(arg)
        matched = False
        for pattern, value in file_map.items():
            if pattern in s:
                if isinstance(value, str):
                    p.is_file.return_value = True
                    p.read_text.return_value = value
                else:
                    p.is_file.return_value = bool(value)
                matched = True
                break
        if not matched:
            p.is_file.return_value = False
        p.__truediv__ = lambda _self, other, _s=s: make_path(f"{_s}/{other}")
        p.resolve.return_value = p
        p.parent = p
        return p

    return make_path


class TestCheckSourceConfigs:
    """Test source configuration verification for all telemetry sources."""

    @patch("mde.telemetry_verify.Path")
    def test_all_configs_present(self, mock_path_cls: MagicMock) -> None:
        """All source configs found and valid."""
        codex_toml = (
            "[otel]\n"
            "[otel.exporter.otlp-http]\n"
            'endpoint = "http://127.0.0.1:4318/v1/logs"\n'
            'protocol = "binary"\n'
        )
        claude_json = json.dumps(
            {
                "env": {
                    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
                    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
                }
            }
        )
        make_path = _make_path_factory(
            {
                "config.toml": codex_toml,
                "observability.py": True,
                "settings.json": claude_json,
            }
        )
        mock_path_cls.home.return_value = make_path("/home")
        mock_path_cls.side_effect = make_path

        results = _check_source_configs()
        statuses = {name: status for name, status, _ in results}

        assert statuses["claude-code"] == "OK"
        assert statuses["codex"] == "OK"
        assert statuses["gemini"] == "WARNING"  # Gemini doesn't support OTLP
        assert statuses["mde"] == "OK"

    @patch("mde.telemetry_verify.Path")
    def test_codex_config_missing(self, mock_path_cls: MagicMock) -> None:
        """Codex config file not found."""
        make_path = _make_path_factory()
        mock_path_cls.home.return_value = make_path("/home")
        mock_path_cls.side_effect = make_path

        results = _check_source_configs()
        codex_results = [(n, s, d) for n, s, d in results if n == "codex"]
        assert len(codex_results) == 1
        assert codex_results[0][1] == "WARNING"
        assert "not found" in codex_results[0][2]

    @patch("mde.telemetry_verify.Path")
    def test_codex_missing_otel_section(self, mock_path_cls: MagicMock) -> None:
        """Codex config exists but has no [otel] section."""
        make_path = _make_path_factory(
            {
                "config.toml": "[general]\nmodel = 'gpt-4'\n",
                "observability.py": True,
            }
        )
        mock_path_cls.home.return_value = make_path("/home")
        mock_path_cls.side_effect = make_path

        results = _check_source_configs()
        codex_results = [(n, s, d) for n, s, d in results if n == "codex"]
        assert codex_results[0][1] == "WARNING"
        assert "otel" in codex_results[0][2].lower()

    @patch("mde.telemetry_verify.Path")
    def test_mde_observability_missing(self, mock_path_cls: MagicMock) -> None:
        """Observability.py not found emits WARNING for mde source."""
        make_path = _make_path_factory()  # all files missing
        mock_path_cls.home.return_value = make_path("/home")
        mock_path_cls.side_effect = make_path

        results = _check_source_configs()
        mde_results = [(n, s, d) for n, s, d in results if n == "mde"]
        assert mde_results[0][1] == "WARNING"

    @patch("mde.telemetry_verify.Path")
    def test_codex_wrong_endpoint(self, mock_path_cls: MagicMock) -> None:
        """Codex config has [otel] but endpoint points to wrong host."""
        codex_toml = (
            '[otel]\n[otel.exporter.otlp-http]\nendpoint = "http://remote-host:4318/v1/logs"\n'
        )
        make_path = _make_path_factory(
            {
                "config.toml": codex_toml,
                "observability.py": True,
            }
        )
        mock_path_cls.home.return_value = make_path("/home")
        mock_path_cls.side_effect = make_path

        results = _check_source_configs()
        codex_results = [(n, s, d) for n, s, d in results if n == "codex"]
        assert codex_results[0][1] == "WARNING"
        assert "non-localhost" in codex_results[0][2].lower()


class TestCheckDataArrivalLoki:
    """Test Loki data arrival checks."""

    @patch("mde.telemetry_verify.urlopen")
    def test_all_services_found(self, mock_urlopen: MagicMock) -> None:
        """All expected service names present in Loki labels."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {
                "status": "success",
                "data": ["claude-code", "codex-app-server", "codex_exec", "gemini-cli", "mde"],
            }
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_loki()
        statuses = {name: status for name, status, _ in results}
        assert all(s == "OK" for s in statuses.values()), f"Expected all OK, got {statuses}"

    @patch("mde.telemetry_verify.urlopen")
    def test_some_services_missing(self, mock_urlopen: MagicMock) -> None:
        """Some expected services not found in Loki."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {
                "status": "success",
                "data": ["claude-code", "mde"],
            }
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_loki()
        statuses = {name: status for name, status, _ in results}
        assert statuses["loki:claude-code"] == "OK"
        assert statuses["loki:mde"] == "OK"
        assert statuses["loki:codex-app-server"] == "WARNING"
        assert statuses["loki:gemini-cli"] == "WARNING"

    @patch("mde.telemetry_verify.urlopen", side_effect=ConnectionRefusedError("refused"))
    def test_loki_unreachable(self, mock_urlopen: MagicMock) -> None:
        """Loki endpoint is unreachable -- WARNING, not FAIL."""
        _ = mock_urlopen
        results = _check_data_arrival_loki()
        assert len(results) == 1
        assert results[0][1] == "WARNING"
        assert "unreachable" in results[0][2].lower() or "refused" in results[0][2].lower()

    @patch("mde.telemetry_verify.urlopen")
    def test_empty_loki_response(self, mock_urlopen: MagicMock) -> None:
        """Loki returns empty data array."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {
                "status": "success",
                "data": [],
            }
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_loki()
        statuses = {name: status for name, status, _ in results}
        assert all(s == "WARNING" for s in statuses.values())


class TestCheckDataArrivalTempo:
    """Test Tempo data arrival checks."""

    @patch("mde.telemetry_verify.urlopen")
    def test_traces_found(self, mock_urlopen: MagicMock) -> None:
        """Tempo returns recent traces."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {
                "traces": [
                    {"rootServiceName": "claude-code", "traceID": "abc123"},
                    {"rootServiceName": "codex-app-server", "traceID": "def456"},
                ],
            }
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_tempo()
        statuses = {name: status for name, status, _ in results}
        assert statuses["tempo:traces"] == "OK"
        details = {name: detail for name, _, detail in results}
        assert "2 traces" in details["tempo:traces"]

    @patch("mde.telemetry_verify.urlopen")
    def test_no_traces(self, mock_urlopen: MagicMock) -> None:
        """Tempo returns empty traces."""
        resp = MagicMock()
        resp.read.return_value = json.dumps({"traces": []}).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_tempo()
        assert results[0][1] == "WARNING"
        assert "no recent traces" in results[0][2].lower()

    @patch("mde.telemetry_verify.urlopen", side_effect=ConnectionRefusedError("refused"))
    def test_tempo_unreachable(self, mock_urlopen: MagicMock) -> None:
        """Tempo endpoint is unreachable -- WARNING, not FAIL."""
        _ = mock_urlopen
        results = _check_data_arrival_tempo()
        assert len(results) == 1
        assert results[0][1] == "WARNING"

    @patch("mde.telemetry_verify.urlopen")
    def test_tempo_null_traces(self, mock_urlopen: MagicMock) -> None:
        """Tempo returns null traces field."""
        resp = MagicMock()
        resp.read.return_value = json.dumps({"traces": None}).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_tempo()
        assert results[0][1] == "WARNING"

    @patch("mde.telemetry_verify.urlopen")
    def test_tempo_service_names_listed(self, mock_urlopen: MagicMock) -> None:
        """Tempo result includes service names from traces."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {
                "traces": [
                    {"rootServiceName": "mde", "traceID": "aaa"},
                    {"rootServiceName": "claude-code", "traceID": "bbb"},
                    {"rootServiceName": "mde", "traceID": "ccc"},
                ],
            }
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        results = _check_data_arrival_tempo()
        details = {name: detail for name, _, detail in results}
        assert "mde" in details.get("tempo:services", "")
        assert "claude-code" in details.get("tempo:services", "")

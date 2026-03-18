"""Tests for agentkit_cli.monitor_daemon (D4)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.monitor_config import MonitorConfig
from agentkit_cli.monitor_daemon import _log, run_daemon


# ---------------------------------------------------------------------------
# _log helper tests
# ---------------------------------------------------------------------------

class TestLog:
    def test_log_writes_json_line(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        _log({"ts": "2025-01-01", "event": "test", "score": 85.0})
        content = log_file.read_text()
        data = json.loads(content.strip())
        assert data["event"] == "test"
        assert data["score"] == 85.0

    def test_log_appends_multiple_lines(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        _log({"event": "a"})
        _log({"event": "b"})
        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        assert len(lines) == 2

    def test_log_creates_dir(self, tmp_path, monkeypatch):
        log_file = tmp_path / "subdir" / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        _log({"event": "test"})
        assert log_file.exists()


# ---------------------------------------------------------------------------
# run_daemon unit tests (with mocked engine)
# ---------------------------------------------------------------------------

class TestRunDaemon:
    def test_daemon_logs_startup(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        toml_path = tmp_path / ".agentkit.toml"

        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_all_due", return_value=[]):
            run_daemon(poll_interval=0, toml_path=toml_path, _test_max_cycles=1)

        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        events = [json.loads(l).get("event") for l in lines]
        assert "startup" in events

    def test_daemon_logs_exit(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        toml_path = tmp_path / ".agentkit.toml"

        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_all_due", return_value=[]):
            run_daemon(poll_interval=0, toml_path=toml_path, _test_max_cycles=1)

        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        events = [json.loads(l).get("event") for l in lines]
        assert "exit" in events

    def test_daemon_logs_run_results(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        toml_path = tmp_path / ".agentkit.toml"
        cfg = MonitorConfig(toml_path=toml_path)
        cfg.add_target("github:owner/repo")

        from agentkit_cli.monitor_engine import MonitorResult
        from datetime import timezone
        mock_result = MonitorResult(
            target="github:owner/repo",
            score=85.0,
            prev_score=None,
            delta=0.0,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_all_due", return_value=[mock_result]):
            run_daemon(poll_interval=0, toml_path=toml_path, _test_max_cycles=1)

        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        entries = [json.loads(l) for l in lines]
        run_entries = [e for e in entries if e.get("target") == "github:owner/repo"]
        assert len(run_entries) >= 1
        assert run_entries[0]["score"] == 85.0

    def test_daemon_handles_engine_error(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        monkeypatch.setattr("agentkit_cli.monitor_daemon.LOG_FILE", log_file)
        toml_path = tmp_path / ".agentkit.toml"

        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_all_due", side_effect=RuntimeError("boom")):
            # Should not raise
            run_daemon(poll_interval=0, toml_path=toml_path, _test_max_cycles=1)

        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        entries = [json.loads(l) for l in lines]
        error_entries = [e for e in entries if e.get("event") == "error"]
        assert len(error_entries) >= 1
        assert "boom" in error_entries[0]["message"]


# ---------------------------------------------------------------------------
# Integration: subprocess launch + SIGTERM
# ---------------------------------------------------------------------------

class TestDaemonProcess:
    def test_daemon_starts_and_sigterms(self, tmp_path):
        """Launch daemon as subprocess, verify it starts, then SIGTERM it."""
        log_file = tmp_path / "monitor.log"
        toml_path = tmp_path / ".agentkit.toml"
        # Create empty config
        MonitorConfig(toml_path=toml_path)

        env = os.environ.copy()
        env["AGENTKIT_MONITOR_TOML"] = str(toml_path)
        env["AGENTKIT_MONITOR_LOG"] = str(log_file)

        proc = subprocess.Popen(
            [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent}')
from unittest.mock import patch
from pathlib import Path
from agentkit_cli.monitor_daemon import run_daemon
import agentkit_cli.monitor_daemon as mod
mod.LOG_FILE = Path('{log_file}')
with patch('agentkit_cli.monitor_engine.MonitorEngine.run_all_due', return_value=[]):
    run_daemon(poll_interval=1, toml_path=Path('{toml_path}'), _test_max_cycles=3)
"""],
            env=env,
        )
        # Give it a moment to start
        time.sleep(0.5)
        assert proc.poll() is None, "Daemon exited prematurely"

        # Send SIGTERM
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Daemon did not exit after SIGTERM within 5s")

    def test_daemon_writes_structured_log(self, tmp_path):
        """Daemon should write JSON lines to the log file."""
        log_file = tmp_path / "monitor.log"
        toml_path = tmp_path / ".agentkit.toml"
        MonitorConfig(toml_path=toml_path)

        proc = subprocess.Popen(
            [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent}')
from unittest.mock import patch
from pathlib import Path
from agentkit_cli.monitor_daemon import run_daemon
import agentkit_cli.monitor_daemon as mod
mod.LOG_FILE = Path('{log_file}')
with patch('agentkit_cli.monitor_engine.MonitorEngine.run_all_due', return_value=[]):
    run_daemon(poll_interval=0, toml_path=Path('{toml_path}'), _test_max_cycles=1)
"""],
        )
        proc.wait(timeout=10)

        assert log_file.exists()
        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        assert len(lines) >= 2  # startup + exit
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "ts" in data

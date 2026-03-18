"""Tests for agentkit_cli.commands.monitor (D3)."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.commands.monitor import monitor_app, PID_FILE, LOG_FILE, MONITOR_DIR
from agentkit_cli.monitor_config import MonitorConfig


runner = CliRunner()


def _invoke(args, **kwargs):
    return runner.invoke(monitor_app, args, catch_exceptions=False, **kwargs)


def _config_option(tmp_path: Path):
    return ["--config", str(tmp_path / ".agentkit.toml")]


# ---------------------------------------------------------------------------
# add command tests
# ---------------------------------------------------------------------------

class TestAddCommand:
    def test_add_basic(self, tmp_path):
        result = _invoke(["add", "github:owner/repo"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "Added monitor target" in result.output
        assert "github:owner/repo" in result.output

    def test_add_with_schedule(self, tmp_path):
        result = _invoke(["add", "github:owner/repo", "--schedule", "weekly"] + _config_option(tmp_path))
        assert result.exit_code == 0
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        mt = cfg.get_target("github:owner/repo")
        assert mt.schedule == "weekly"

    def test_add_invalid_schedule(self, tmp_path):
        result = runner.invoke(monitor_app, ["add", "github:owner/repo", "--schedule", "monthly"] + _config_option(tmp_path))
        assert result.exit_code != 0

    def test_add_with_slack(self, tmp_path):
        result = _invoke(["add", "github:owner/repo", "--notify-slack", "https://slack.test"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "Slack" in result.output

    def test_add_with_min_score(self, tmp_path):
        result = _invoke(["add", "github:owner/repo", "--min-score", "75"] + _config_option(tmp_path))
        assert result.exit_code == 0
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        mt = cfg.get_target("github:owner/repo")
        assert mt.min_score == 75.0

    def test_add_persists_to_config(self, tmp_path):
        _invoke(["add", "github:owner/repo"] + _config_option(tmp_path))
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        assert cfg.get_target("github:owner/repo") is not None


# ---------------------------------------------------------------------------
# remove command tests
# ---------------------------------------------------------------------------

class TestRemoveCommand:
    def test_remove_existing(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo")
        result = _invoke(["remove", "github:owner/repo", "--yes"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_remove_nonexistent(self, tmp_path):
        result = runner.invoke(monitor_app, ["remove", "github:missing/repo", "--yes"] + _config_option(tmp_path))
        assert result.exit_code != 0
        assert "Not found" in result.output


# ---------------------------------------------------------------------------
# list command tests
# ---------------------------------------------------------------------------

class TestListCommand:
    def test_list_empty(self, tmp_path):
        result = _invoke(["list"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "No monitored targets" in result.output

    def test_list_with_targets(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo1")
        cfg.add_target("github:owner/repo2")
        result = _invoke(["list", "--json"] + _config_option(tmp_path))
        assert result.exit_code == 0
        data = json.loads(result.output)
        names = [d["target"] for d in data]
        assert "github:owner/repo1" in names
        assert "github:owner/repo2" in names

    def test_list_json_output(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo")
        result = _invoke(["list", "--json"] + _config_option(tmp_path))
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["target"] == "github:owner/repo"

    def test_list_shows_schedule(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo", schedule="weekly")
        result = _invoke(["list"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "weekly" in result.output


# ---------------------------------------------------------------------------
# run command tests
# ---------------------------------------------------------------------------

class TestRunCommand:
    def test_run_no_due_targets(self, tmp_path):
        now = datetime.now(timezone.utc).isoformat()
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo")
        cfg.update_last_run("github:owner/repo", 85.0, ts=now)
        result = _invoke(["run"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "No targets due" in result.output

    def test_run_specific_target(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo")

        from agentkit_cli.monitor_engine import MonitorResult
        mock_result = MonitorResult(
            target="github:owner/repo",
            score=85.0,
            prev_score=None,
            delta=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_target", return_value=mock_result):
            result = _invoke(["run", "--target", "github:owner/repo"] + _config_option(tmp_path))
        assert result.exit_code == 0

    def test_run_missing_target_exits_nonzero(self, tmp_path):
        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_target", return_value=None):
            result = runner.invoke(
                monitor_app,
                ["run", "--target", "github:missing/repo"] + _config_option(tmp_path),
            )
        assert result.exit_code != 0

    def test_run_json_output(self, tmp_path):
        cfg = MonitorConfig(toml_path=tmp_path / ".agentkit.toml")
        cfg.add_target("github:owner/repo")

        from agentkit_cli.monitor_engine import MonitorResult
        mock_result = MonitorResult(
            target="github:owner/repo",
            score=85.0,
            prev_score=None,
            delta=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with patch("agentkit_cli.monitor_engine.MonitorEngine.run_target", return_value=mock_result):
            result = _invoke(["run", "--target", "github:owner/repo", "--json"] + _config_option(tmp_path))
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# start / stop / status tests
# ---------------------------------------------------------------------------

class TestDaemonLifecycle:
    def test_start_creates_pid_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agentkit_cli.commands.monitor.PID_FILE", tmp_path / "monitor.pid")
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", tmp_path / "monitor.log")
        monkeypatch.setattr("agentkit_cli.commands.monitor.MONITOR_DIR", tmp_path)
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        with patch("subprocess.Popen", return_value=mock_proc):
            result = runner.invoke(monitor_app, ["start"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert (tmp_path / "monitor.pid").exists()

    def test_stop_removes_pid_file(self, tmp_path, monkeypatch):
        pid_file = tmp_path / "monitor.pid"
        pid_file.write_text("99999")
        monkeypatch.setattr("agentkit_cli.commands.monitor.PID_FILE", pid_file)
        monkeypatch.setattr("agentkit_cli.commands.monitor.MONITOR_DIR", tmp_path)
        with patch("os.kill") as mock_kill:
            result = runner.invoke(monitor_app, ["stop"])
        assert result.exit_code == 0
        assert "stopped" in result.output.lower() or "Daemon stopped" in result.output

    def test_stop_no_pid_file(self, tmp_path, monkeypatch):
        pid_file = tmp_path / "monitor.pid"
        monkeypatch.setattr("agentkit_cli.commands.monitor.PID_FILE", pid_file)
        result = runner.invoke(monitor_app, ["stop"])
        assert result.exit_code == 0
        assert "not running" in result.output.lower() or "No daemon" in result.output

    def test_status_stopped(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agentkit_cli.commands.monitor.PID_FILE", tmp_path / "monitor.pid")
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", tmp_path / "monitor.log")
        result = _invoke(["status"] + _config_option(tmp_path))
        assert result.exit_code == 0
        assert "stopped" in result.output.lower()

    def test_status_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agentkit_cli.commands.monitor.PID_FILE", tmp_path / "monitor.pid")
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", tmp_path / "monitor.log")
        result = _invoke(["status", "--json"] + _config_option(tmp_path))
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "daemon_running" in data
        assert data["daemon_running"] is False


# ---------------------------------------------------------------------------
# logs command tests
# ---------------------------------------------------------------------------

class TestLogsCommand:
    def test_logs_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", tmp_path / "monitor.log")
        result = runner.invoke(monitor_app, ["logs"])
        assert result.exit_code == 0
        assert "No log file" in result.output

    def test_logs_with_entries(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        entry = json.dumps({
            "ts": "2025-01-01T12:00:00+00:00",
            "target": "github:owner/repo",
            "score": 85.0,
            "delta": 5.0,
            "notify_fired": False,
        })
        log_file.write_text(entry + "\n")
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", log_file)
        result = runner.invoke(monitor_app, ["logs"])
        assert result.exit_code == 0
        assert "github:owner/repo" in result.output

    def test_logs_json_output(self, tmp_path, monkeypatch):
        log_file = tmp_path / "monitor.log"
        entry = {"ts": "2025-01-01T12:00:00+00:00", "target": "x", "score": 90.0, "delta": 0.0, "notify_fired": False}
        log_file.write_text(json.dumps(entry) + "\n")
        monkeypatch.setattr("agentkit_cli.commands.monitor.LOG_FILE", log_file)
        result = runner.invoke(monitor_app, ["logs", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1

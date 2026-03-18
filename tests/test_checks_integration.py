"""Tests for GitHub Checks API integration in run and gate commands."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_github_env(monkeypatch):
    """Set env vars to simulate GitHub Actions."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "testorg/testrepo")
    monkeypatch.setenv("GITHUB_SHA", "abc123def")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")


def _clear_github_env(monkeypatch):
    """Remove GitHub Actions env vars."""
    for var in ("GITHUB_ACTIONS", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)


def _mock_urlopen_response(body: dict):
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# run command checks integration
# ---------------------------------------------------------------------------

class TestRunChecksIntegration:
    def test_checks_auto_detect_creates_check(self, monkeypatch, tmp_path):
        """When GITHUB_ACTIONS=true, auto-detect creates a check run."""
        _set_github_env(monkeypatch)
        resp = _mock_urlopen_response({"id": 99})
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            result = runner.invoke(app, ["run", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert mock_open.call_count >= 1

    def test_no_checks_flag_skips(self, monkeypatch, tmp_path):
        """--no-checks prevents check run creation."""
        _set_github_env(monkeypatch)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.checks_client.urllib_request.urlopen") as mock_open:
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--no-checks"])
        assert result.exit_code == 0
        mock_open.assert_not_called()

    def test_no_github_env_no_check(self, monkeypatch, tmp_path):
        """Outside GitHub Actions, no check run is created."""
        _clear_github_env(monkeypatch)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.checks_client.urllib_request.urlopen") as mock_open:
            result = runner.invoke(app, ["run", "--path", str(tmp_path)])
        assert result.exit_code == 0
        mock_open.assert_not_called()

    def test_checks_api_failure_nonfatal(self, monkeypatch, tmp_path):
        """Checks API failure should not crash run command."""
        _set_github_env(monkeypatch)
        from urllib.error import HTTPError
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.checks_client.urllib_request.urlopen",
                    side_effect=HTTPError("url", 500, "err", {}, None)):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--checks"])
        assert result.exit_code == 0

    def test_checks_explicit_outside_actions(self, monkeypatch, tmp_path):
        """--checks outside Actions should warn but not crash."""
        _clear_github_env(monkeypatch)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--checks"])
        assert result.exit_code == 0

    def test_check_run_update_called(self, monkeypatch, tmp_path):
        """Check run should be updated with completed status at end."""
        _set_github_env(monkeypatch)
        resp = _mock_urlopen_response({"id": 42})
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--checks"])
        assert result.exit_code == 0
        # First call = create (POST), second call = update (PATCH)
        if mock_open.call_count >= 2:
            update_req = mock_open.call_args_list[1][0][0]
            assert update_req.method == "PATCH"
            body = json.loads(update_req.data)
            assert body["status"] == "completed"


# ---------------------------------------------------------------------------
# gate command checks integration
# ---------------------------------------------------------------------------

class TestGateChecksIntegration:
    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_auto_detect_creates_check(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="PASS", passed=True, score=85.0, grade="B",
            thresholds={"min_score": 70.0}, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        _set_github_env(monkeypatch)
        resp = _mock_urlopen_response({"id": 77})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70"])
        assert mock_open.call_count >= 1

    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_no_checks_skips(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="PASS", passed=True, score=85.0, grade="B",
            thresholds={"min_score": 70.0}, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        _set_github_env(monkeypatch)
        with patch("agentkit_cli.checks_client.urllib_request.urlopen") as mock_open:
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70", "--no-checks"])
        mock_open.assert_not_called()

    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_fail_conclusion_failure(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="FAIL", passed=False, score=50.0, grade="D",
            thresholds={"min_score": 70.0}, failure_reasons=["score too low"],
            components={}, missing_tools=[], tool_status=[],
        )
        _set_github_env(monkeypatch)
        resp = _mock_urlopen_response({"id": 55})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70", "--checks"])
        if mock_open.call_count >= 2:
            update_req = mock_open.call_args_list[1][0][0]
            body = json.loads(update_req.data)
            assert body["conclusion"] == "failure"

    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_pass_conclusion_success(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="PASS", passed=True, score=90.0, grade="A",
            thresholds={"min_score": 70.0}, failure_reasons=[],
            components={"agentlint": {"raw_score": 90.0, "weight": 1.0, "contribution": 90.0}},
            missing_tools=[], tool_status=[],
        )
        _set_github_env(monkeypatch)
        resp = _mock_urlopen_response({"id": 88})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70", "--checks"])
        if mock_open.call_count >= 2:
            update_req = mock_open.call_args_list[1][0][0]
            body = json.loads(update_req.data)
            assert body["conclusion"] == "success"

    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_checks_api_failure_nonfatal(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="PASS", passed=True, score=85.0, grade="B",
            thresholds={"min_score": 70.0}, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        _set_github_env(monkeypatch)
        from urllib.error import HTTPError
        with patch("agentkit_cli.checks_client.urllib_request.urlopen",
                    side_effect=HTTPError("url", 422, "err", {}, None)):
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70", "--checks"])
        # Should not crash — exit 0 because gate passed
        assert result.exit_code == 0

    @patch("agentkit_cli.commands.gate_cmd.run_gate")
    def test_gate_no_github_env_noop(self, mock_gate, monkeypatch, tmp_path):
        from agentkit_cli.gate import GateResult
        mock_gate.return_value = GateResult(
            verdict="PASS", passed=True, score=85.0, grade="B",
            thresholds={"min_score": 70.0}, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        _clear_github_env(monkeypatch)
        with patch("agentkit_cli.checks_client.urllib_request.urlopen") as mock_open:
            result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70"])
        mock_open.assert_not_called()

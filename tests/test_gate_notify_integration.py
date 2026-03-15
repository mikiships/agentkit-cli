"""Integration tests: --notify-slack/discord/webhook flags on gate and run commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.commands.gate_cmd import gate_command
from agentkit_cli.gate import GateResult
from agentkit_cli.main import app

runner = CliRunner()


def _make_gate_result(passed: bool = False, score: float = 55.0) -> GateResult:
    return GateResult(
        verdict="PASS" if passed else "FAIL",
        score=score,
        grade="A" if passed else "C",
        passed=passed,
        failure_reasons=[] if passed else ["score below threshold"],
        thresholds={"min_score": 70},
        components={},
        missing_tools=[],
        tool_status=[],
        baseline_delta=None,
    )


class TestGateNotifySlack:
    def test_notify_slack_fires_on_fail(self, tmp_path):
        gate_result = _make_gate_result(passed=False, score=55.0)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                result = runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--min-score", "70",
                    "--notify-slack", "https://hooks.slack.com/test",
                    "--notify-on", "fail",
                ])
        assert any(c.service == "slack" for c in captured)

    def test_notify_not_fired_when_no_url(self, tmp_path):
        gate_result = _make_gate_result(passed=False)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "70"])
        assert captured == []

    def test_notify_discord_fires_on_fail(self, tmp_path):
        gate_result = _make_gate_result(passed=False)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--notify-discord", "https://discord.com/api/webhooks/test",
                    "--notify-on", "fail",
                ])
        assert any(c.service == "discord" for c in captured)

    def test_notify_webhook_fires_on_fail(self, tmp_path):
        gate_result = _make_gate_result(passed=False)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--notify-webhook", "https://example.com/hook",
                    "--notify-on", "fail",
                ])
        assert any(c.service == "webhook" for c in captured)

    def test_notify_on_always_passes_correct_config(self, tmp_path):
        gate_result = _make_gate_result(passed=True, score=90.0)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--notify-slack", "https://hooks.slack.com/test",
                    "--notify-on", "always",
                ])
        assert len(captured) == 1
        assert captured[0].notify_on == "always"

    def test_notify_env_var_slack(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_NOTIFY_SLACK", "https://hooks.slack.com/env")
        gate_result = _make_gate_result(passed=False)
        captured = []

        def _capture(configs, **kwargs):
            captured.extend(configs)

        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=_capture):
                runner.invoke(app, ["gate", "--path", str(tmp_path), "--notify-on", "fail"])
        assert any(c.service == "slack" for c in captured)

    def test_notify_failure_does_not_affect_exit_code(self, tmp_path):
        """Notification errors must not change gate exit code."""
        gate_result = _make_gate_result(passed=False)
        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=RuntimeError("boom")):
                result = runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--notify-slack", "https://hooks.slack.com/test",
                    "--notify-on", "fail",
                ])
        # Gate should still return 1 (failed gate), not 2 (error)
        assert result.exit_code == 1

    def test_notify_pass_does_not_affect_exit_code(self, tmp_path):
        """Notification errors on passing gate don't change exit code."""
        gate_result = _make_gate_result(passed=True, score=90.0)
        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=gate_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications", side_effect=RuntimeError("boom")):
                result = runner.invoke(app, [
                    "gate", "--path", str(tmp_path),
                    "--notify-slack", "https://hooks.slack.com/test",
                    "--notify-on", "always",
                ])
        assert result.exit_code == 0

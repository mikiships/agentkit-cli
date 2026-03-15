"""Tests for agentkit notify test and notify config subcommands."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


class TestNotifyTest:
    def test_no_args_exits_nonzero(self):
        result = runner.invoke(app, ["notify", "test"])
        assert result.exit_code != 0

    def test_slack_success(self):
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", return_value=(True, "HTTP 200")):
            result = runner.invoke(app, ["notify", "test", "--slack", "https://hooks.slack.com/test"])
        assert result.exit_code == 0
        assert "delivered" in result.output.lower() or "✓" in result.output

    def test_slack_failure(self):
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", return_value=(False, "connection refused")):
            result = runner.invoke(app, ["notify", "test", "--slack", "https://hooks.slack.com/bad"])
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "✗" in result.output

    def test_discord_success(self):
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", return_value=(True, "HTTP 204")):
            result = runner.invoke(app, ["notify", "test", "--discord", "https://discord.com/api/webhooks/x"])
        assert result.exit_code == 0

    def test_webhook_success(self):
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", return_value=(True, "HTTP 200")):
            result = runner.invoke(app, ["notify", "test", "--webhook", "https://example.com/hook"])
        assert result.exit_code == 0

    def test_multiple_targets(self):
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", return_value=(True, "HTTP 200")):
            result = runner.invoke(app, [
                "notify", "test",
                "--slack", "https://hooks.slack.com/a",
                "--discord", "https://discord.com/api/webhooks/b",
            ])
        assert result.exit_code == 0

    def test_partial_failure_exits_nonzero(self):
        responses = [(True, "HTTP 200"), (False, "error")]
        with patch("agentkit_cli.commands.notify_cmd._send_with_retry", side_effect=responses):
            result = runner.invoke(app, [
                "notify", "test",
                "--slack", "https://hooks.slack.com/a",
                "--discord", "https://discord.com/api/webhooks/b",
            ])
        assert result.exit_code != 0


class TestNotifyConfig:
    def test_config_no_env(self, monkeypatch):
        monkeypatch.delenv("AGENTKIT_NOTIFY_SLACK", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_DISCORD", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_WEBHOOK", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_ON", raising=False)
        result = runner.invoke(app, ["notify", "config"])
        assert result.exit_code == 0
        assert "not set" in result.output

    def test_config_with_slack_env(self, monkeypatch):
        monkeypatch.setenv("AGENTKIT_NOTIFY_SLACK", "https://hooks.slack.com/env")
        monkeypatch.delenv("AGENTKIT_NOTIFY_DISCORD", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_WEBHOOK", raising=False)
        result = runner.invoke(app, ["notify", "config"])
        assert result.exit_code == 0
        assert "AGENTKIT_NOTIFY_SLACK" in result.output

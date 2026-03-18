"""D2 tests: agentkit webhook CLI commands."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# webhook --help
# ---------------------------------------------------------------------------

def test_webhook_help_shows_subcommands():
    result = runner.invoke(app, ["webhook", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "config" in result.output
    assert "test" in result.output


def test_webhook_serve_help():
    result = runner.invoke(app, ["webhook", "serve", "--help"])
    assert result.exit_code == 0
    assert "--port" in result.output


def test_webhook_config_help():
    result = runner.invoke(app, ["webhook", "config", "--help"])
    assert result.exit_code == 0
    assert "--show" in result.output
    assert "--set-secret" in result.output


def test_webhook_test_help():
    result = runner.invoke(app, ["webhook", "test", "--help"])
    assert result.exit_code == 0
    assert "--event" in result.output


# ---------------------------------------------------------------------------
# webhook config --show
# ---------------------------------------------------------------------------

def test_webhook_config_show(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["webhook", "config", "--show"])
    assert result.exit_code == 0
    assert "Webhook Configuration" in result.output
    assert "port" in result.output


def test_webhook_config_set_secret(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["webhook", "config", "--set-secret", "s3cret"])
        assert result.exit_code == 0
        assert "webhook.secret" in result.output

        # Verify persisted
        toml = Path(".agentkit.toml")
        assert toml.exists()
        content = toml.read_text()
        assert "s3cret" in content


def test_webhook_config_set_port(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["webhook", "config", "--set-port", "9090"])
        assert result.exit_code == 0
        assert "webhook.port" in result.output

        toml = Path(".agentkit.toml")
        content = toml.read_text()
        assert "9090" in content


def test_webhook_config_set_channel(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["webhook", "config", "--set-channel", "https://hooks.slack.com/test"])
        assert result.exit_code == 0
        assert "notify_channels" in result.output


# ---------------------------------------------------------------------------
# webhook test
# ---------------------------------------------------------------------------

def test_webhook_test_push():
    from agentkit_cli.webhook.event_processor import EventProcessor
    mock_result = {
        "event_type": "push",
        "repo": "local/test",
        "score": 72.0,
        "prev_score": None,
        "recorded": True,
        "notified": False,
    }
    with patch.object(EventProcessor, "process", return_value=mock_result):
        result = runner.invoke(app, ["webhook", "test", "--event", "push", "--repo", "."])
    assert result.exit_code == 0
    assert "72" in result.output


def test_webhook_test_pull_request():
    from agentkit_cli.webhook.event_processor import EventProcessor
    mock_result = {
        "event_type": "pull_request",
        "repo": "a/b",
        "score": 88.0,
        "prev_score": 80.0,
        "recorded": True,
        "notified": False,
        "comment_body": "## agentkit Quality Report\n...",
    }
    with patch.object(EventProcessor, "process", return_value=mock_result):
        result = runner.invoke(app, ["webhook", "test", "--event", "pull_request", "--repo", "a/b"])
    assert result.exit_code == 0
    assert "88" in result.output


def test_webhook_test_invalid_event():
    result = runner.invoke(app, ["webhook", "test", "--event", "invalid"])
    assert result.exit_code != 0 or "Error" in result.output or "must be" in result.output


# ---------------------------------------------------------------------------
# Synthetic event builder
# ---------------------------------------------------------------------------

def test_build_synthetic_event_push():
    from agentkit_cli.commands.webhook import _build_synthetic_event
    evt = _build_synthetic_event("push", "owner/repo")
    assert evt["event_type"] == "push"
    assert evt["repository"]["full_name"] == "owner/repo"
    assert "ref" in evt


def test_build_synthetic_event_pr():
    from agentkit_cli.commands.webhook import _build_synthetic_event
    evt = _build_synthetic_event("pull_request", "owner/repo")
    assert evt["event_type"] == "pull_request"
    assert "pull_request" in evt
    assert evt["pull_request"]["number"] == 1


def test_build_synthetic_event_local_path(tmp_path):
    from agentkit_cli.commands.webhook import _build_synthetic_event
    evt = _build_synthetic_event("push", str(tmp_path))
    assert "local/" in evt["repository"]["full_name"]

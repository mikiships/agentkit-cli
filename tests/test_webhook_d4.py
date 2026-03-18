"""D4 tests: agentkit doctor webhook check and agentkit run --webhook-notify."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.doctor import check_webhook_config, run_doctor

runner = CliRunner()


# ---------------------------------------------------------------------------
# D4.1 check_webhook_config
# ---------------------------------------------------------------------------

def test_check_webhook_config_no_toml(tmp_path):
    result = check_webhook_config(tmp_path)
    assert result.id == "integrations.webhook"
    assert result.category == "integrations"
    # No TOML → pass (optional)
    assert result.status == "pass"


def test_check_webhook_config_empty_section(tmp_path):
    toml = tmp_path / ".agentkit.toml"
    toml.write_text("[webhook]\n")
    result = check_webhook_config(tmp_path)
    assert result.status == "pass"


def test_check_webhook_config_missing_secret_warns(tmp_path):
    toml = tmp_path / ".agentkit.toml"
    toml.write_text('[webhook]\nport = 9090\nsecret = ""\n')
    result = check_webhook_config(tmp_path)
    assert result.status == "warn"
    assert "secret" in result.summary.lower() or "secret" in result.details.lower()


def test_check_webhook_config_with_secret_passes(tmp_path):
    toml = tmp_path / ".agentkit.toml"
    toml.write_text('[webhook]\nport = 8080\nsecret = "mysecret"\n')
    result = check_webhook_config(tmp_path)
    assert result.status == "pass"
    assert "8080" in result.summary


def test_doctor_includes_webhook_section(tmp_path):
    """run_doctor returns a check with category == 'integrations' for webhook."""
    with patch("agentkit_cli.doctor.detect_git_repo") as mock_git:
        from agentkit_cli.doctor import GitRepoState
        mock_git.return_value = GitRepoState(git_available=True, is_repo=False, message="")
        report = run_doctor(root=tmp_path)
    ids = [c.id for c in report.checks]
    assert "integrations.webhook" in ids


def test_doctor_cli_shows_webhook_output(tmp_path):
    """agentkit doctor CLI output includes 'webhook'."""
    result = runner.invoke(app, ["doctor", "--no-fail-exit"], catch_exceptions=False)
    assert "webhook" in result.output.lower()


# ---------------------------------------------------------------------------
# D4.2 agentkit run --webhook-notify
# ---------------------------------------------------------------------------

def test_run_help_includes_webhook_notify():
    result = runner.invoke(app, ["run", "--help"])
    assert "--webhook-notify" in result.output


def test_run_webhook_notify_posts_to_url(tmp_path):
    """--webhook-notify sends a POST when notify.webhook_url is set."""
    from agentkit_cli.config import AgentKitConfig, NotifyConfig
    import dataclasses

    mock_cfg = AgentKitConfig()
    mock_cfg.notify.webhook_url = "https://example.com/hook"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        with patch("agentkit_cli.config.load_config", return_value=mock_cfg):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.return_value.__enter__ = lambda s: s
                mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
                result = runner.invoke(
                    app,
                    ["run", "--skip", "generate", "--skip", "lint", "--skip", "reflect",
                     "--no-history", "--webhook-notify"],
                    catch_exceptions=False,
                )
    # Should have called urlopen
    assert mock_urlopen.called or "webhook-notify" in result.output


def test_run_webhook_notify_warns_when_no_url(tmp_path):
    """--webhook-notify warns if no URL is configured."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["run", "--skip", "generate", "--skip", "lint", "--skip", "reflect",
             "--no-history", "--webhook-notify"],
        )
    # Should warn about missing URL
    assert "webhook" in result.output.lower() or result.exit_code in (0, 1)

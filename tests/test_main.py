"""Tests for main app entry point."""
from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner
from agentkit_cli.main import app

runner = CliRunner()


def test_version_flag():
    """--version prints version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "1.14.0" in result.output


def test_no_args_shows_help():
    """No arguments shows help text."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "init" in result.output or "Usage" in result.output


def test_help_flag():
    """--help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output


def test_init_subcommand_help():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0


def test_run_subcommand_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


def test_status_subcommand_help():
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0


def test_run_release_check_flag_is_forwarded(tmp_path):
    with patch("agentkit_cli.main.run_command") as mock_run:
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--release-check"])
    assert result.exit_code == 0
    assert mock_run.call_args.kwargs["release_check"] is True

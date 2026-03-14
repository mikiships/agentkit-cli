"""Tests for auto-record behavior in agentkit run."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_run_no_history_flag_skips_recording(tmp_path):
    """--no-history prevents record_run from being called."""
    with (
        patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False),
        patch("agentkit_cli.commands.run_cmd.record_run") as mock_record,
    ):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--no-history"])
    assert result.exit_code == 0
    mock_record.assert_not_called()


def test_run_records_history_on_skipped_tools(tmp_path):
    """When all tools are not installed (skipped), no history is recorded (no pass/fail)."""
    with (
        patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False),
        patch("agentkit_cli.commands.run_cmd.record_run") as mock_record,
    ):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 0
    # Skipped steps don't get recorded
    mock_record.assert_not_called()


def test_run_records_history_on_pass(tmp_path):
    """Passing tool steps trigger record_run calls."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with (
        patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True),
        patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result),
        patch("agentkit_cli.commands.run_cmd.record_run") as mock_record,
    ):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 0
    # Should have recorded per-tool + overall
    assert mock_record.call_count >= 1
    # Check overall was recorded
    calls_args = [c.args for c in mock_record.call_args_list]
    tools_recorded = [args[1] for args in calls_args]
    assert "overall" in tools_recorded


def test_run_records_fail_score_on_tool_failure(tmp_path):
    """Failing tool steps record score=0."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error"

    with (
        patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True),
        patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result),
        patch("agentkit_cli.commands.run_cmd.record_run") as mock_record,
    ):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 1
    # Should have called record_run with score=0.0 for tool failures
    calls_args = [c.args for c in mock_record.call_args_list]
    scores = [args[2] for args in calls_args if args[1] != "overall"]
    assert all(s == 0.0 for s in scores)


def test_run_history_failure_does_not_abort_run(tmp_path):
    """If history recording raises an exception, the run still completes."""
    with (
        patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False),
        patch("agentkit_cli.commands.run_cmd.record_run", side_effect=RuntimeError("DB broken")),
    ):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    # run should still complete
    assert result.exit_code == 0

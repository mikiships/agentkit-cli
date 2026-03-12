"""Tests for agentkit run command."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from agentkit_cli.main import app

runner = CliRunner()


def _mock_not_installed(tool: str) -> bool:
    return False


def _mock_installed(tool: str) -> bool:
    return True


def test_run_skips_missing_tools_gracefully(tmp_path):
    """run completes without error when tools are not installed."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    # Should not crash; skipped steps show in output
    assert result.exit_code == 0
    assert "skipped" in result.output


def test_run_all_steps_skipped(tmp_path):
    """All steps can be skipped."""
    result = runner.invoke(app, [
        "run", "--path", str(tmp_path),
        "--skip", "generate",
        "--skip", "lint",
        "--skip", "benchmark",
        "--skip", "reflect",
    ])
    assert result.exit_code == 0
    assert "skipped" in result.output


def test_run_benchmark_skipped_by_default(tmp_path):
    """Benchmark step is skipped by default."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "benchmark" in result.output
    assert result.exit_code == 0


def test_run_json_output_valid(tmp_path):
    """--json flag produces valid JSON."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0
    output = result.output
    # Find the JSON block
    json_start = output.find("{")
    assert json_start != -1, "No JSON found in output"
    json_str = output[json_start:]
    # Find balanced braces
    data = json.loads(json_str[:json_str.rfind("}") + 1])
    assert "steps" in data
    assert "timestamp" in data
    assert "passed" in data
    assert "failed" in data
    assert "skipped" in data


def test_run_json_output_has_steps(tmp_path):
    """JSON output contains steps array."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    output = result.output
    json_start = output.find("{")
    json_str = output[json_start:output.rfind("}") + 1]
    data = json.loads(json_str)
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0


def test_run_saves_last_run_json(tmp_path):
    """run saves .agentkit-last-run.json after running."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 0
    last_run = tmp_path / ".agentkit-last-run.json"
    assert last_run.exists(), ".agentkit-last-run.json should be created"
    data = json.loads(last_run.read_text())
    assert "timestamp" in data
    assert "steps" in data


def test_run_skip_generate(tmp_path):
    """Skipping generate works."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--skip", "generate"])
    assert result.exit_code == 0


def test_run_skip_lint(tmp_path):
    """Skipping lint works."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--skip", "lint"])
    assert result.exit_code == 0


def test_run_shows_pipeline_table(tmp_path):
    """run shows a pipeline results table."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "Pipeline Results" in result.output or "Step" in result.output


def test_run_with_notes(tmp_path):
    """--notes flag is accepted."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--notes", "test run notes"])
    assert result.exit_code == 0


def test_run_failing_step_exits_nonzero(tmp_path):
    """A failing tool step causes non-zero exit."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "error output"
    mock_result.stderr = ""

    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    # Should exit with code 1
    assert result.exit_code == 1


def test_run_passing_steps_exit_zero(tmp_path):
    """All-pass run exits with 0."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok"
    mock_result.stderr = ""

    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 0

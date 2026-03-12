"""Tests for agentkit run --ci mode."""
from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from agentkit_cli.main import app

runner = CliRunner()


def _make_fail_result():
    m = MagicMock()
    m.returncode = 1
    m.stdout = "lint error"
    m.stderr = ""
    return m


def _make_pass_result():
    m = MagicMock()
    m.returncode = 0
    m.stdout = "ok"
    m.stderr = ""
    return m


# --- Exit code tests ---

def test_run_ci_exits_1_on_tool_failure(tmp_path):
    """agentkit run --ci exits 1 when a step fails."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=_make_fail_result()):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    assert result.exit_code == 1


def test_run_ci_exits_0_all_pass(tmp_path):
    """agentkit run --ci exits 0 when all tools not installed (all skipped)."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    assert result.exit_code == 0


def test_run_ci_exits_0_all_skipped_explicit(tmp_path):
    """agentkit run --ci exits 0 when all steps skipped."""
    result = runner.invoke(app, [
        "run", "--path", str(tmp_path), "--ci",
        "--skip", "generate", "--skip", "lint",
        "--skip", "benchmark", "--skip", "reflect",
    ])
    assert result.exit_code == 0


def test_run_non_ci_exits_1_on_tool_failure(tmp_path):
    """agentkit run (no --ci) also exits 1 when step fails (existing behavior)."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=_make_fail_result()):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert result.exit_code == 1


# --- Plain output tests ---

def test_run_ci_output_contains_step_names(tmp_path):
    """agentkit run --ci output lists step names."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    assert "generate" in result.output or "lint" in result.output


def test_run_ci_output_no_rich_markup(tmp_path):
    """agentkit run --ci output should not contain Rich markup tags like [bold]."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    # Rich markup like [bold], [green], [dim] should not appear literally
    assert "[bold]" not in result.output
    assert "[green]" not in result.output
    assert "[dim]" not in result.output


def test_run_ci_output_steps_passed_line(tmp_path):
    """agentkit run --ci output includes 'steps passed' summary."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    assert "steps passed" in result.output


def test_run_ci_failure_message_in_output(tmp_path):
    """agentkit run --ci shows failure count in output."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=_make_fail_result()):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci"])
    assert "failure" in result.output.lower() or "fail" in result.output.lower()


# --- JSON output tests ---

def _extract_json(output: str) -> dict:
    """Extract JSON from mixed output."""
    depth = 0
    start = None
    for i, ch in enumerate(output):
        if ch == "{":
            if start is None:
                start = i
            depth += 1
        elif ch == "}" and start is not None:
            depth -= 1
            if depth == 0:
                return json.loads(output[start : i + 1])
    raise ValueError("No JSON found in output")


def test_run_ci_json_flag_valid_json(tmp_path):
    """agentkit run --ci --json outputs valid JSON."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    assert result.exit_code == 0
    data = _extract_json(result.output)
    assert isinstance(data, dict)


def test_run_ci_json_has_success_key(tmp_path):
    """agentkit run --ci --json output has 'success' key."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    assert "success" in data
    assert data["success"] is True


def test_run_ci_json_success_false_on_failure(tmp_path):
    """agentkit run --ci --json success=false when steps fail."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=_make_fail_result()):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    assert result.exit_code == 1
    data = _extract_json(result.output)
    assert data["success"] is False


def test_run_ci_json_has_steps_key(tmp_path):
    """agentkit run --ci --json output has 'steps' list."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0


def test_run_ci_json_steps_have_name_field(tmp_path):
    """Steps in JSON output have 'name' field."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    for step in data["steps"]:
        assert "name" in step


def test_run_ci_json_steps_have_status_field(tmp_path):
    """Steps in JSON output have 'status' field."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    for step in data["steps"]:
        assert "status" in step


def test_run_ci_json_steps_have_duration_ms_field(tmp_path):
    """Steps in JSON output have 'duration_ms' field."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    for step in data["steps"]:
        assert "duration_ms" in step
        assert isinstance(step["duration_ms"], int)


def test_run_ci_json_steps_have_output_file_field(tmp_path):
    """Steps in JSON output have 'output_file' field."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--ci", "--json"])
    data = _extract_json(result.output)
    for step in data["steps"]:
        assert "output_file" in step


def test_run_json_without_ci_flag_still_works(tmp_path):
    """agentkit run --json (without --ci) still produces valid JSON."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = _extract_json(result.output)
    assert "steps" in data
    assert "success" in data


def test_run_ci_help():
    """agentkit run --help shows --ci flag."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--ci" in result.output

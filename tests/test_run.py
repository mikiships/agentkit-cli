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


# --- D3: Summary table tests ---

def test_run_summary_shows_pass_count(tmp_path):
    """Summary line shows X/Y steps passed."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "steps passed" in result.output


def test_run_summary_table_has_columns(tmp_path):
    """Summary table has Step/Status/Duration/Notes columns."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "Step" in result.output
    assert "Status" in result.output
    assert "Duration" in result.output
    assert "Notes" in result.output


def test_run_summary_skipped_symbol(tmp_path):
    """Skipped steps show ⊘ SKIPPED symbol."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "SKIPPED" in result.output


def test_run_summary_pass_symbol(tmp_path):
    """Passed steps show ✓ PASS symbol."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok"
    mock_result.stderr = ""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "PASS" in result.output


def test_run_summary_fail_symbol(tmp_path):
    """Failed steps show ✗ FAIL symbol."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "error"
    mock_result.stderr = ""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "FAIL" in result.output


def _extract_json(output: str) -> dict:
    """Extract outermost JSON object from mixed output."""
    start = output.find("{")
    assert start != -1, "No JSON found"
    depth = 0
    for i, ch in enumerate(output[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(output[start:i + 1])
    raise ValueError("Unterminated JSON")


def test_run_json_has_summary_key(tmp_path):
    """JSON output includes 'summary' key with structured data."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    data = _extract_json(result.output)
    assert "summary" in data
    assert "passed" in data["summary"]
    assert "failed" in data["summary"]
    assert "skipped" in data["summary"]
    assert "total" in data["summary"]
    assert "result" in data["summary"]


def test_run_json_summary_result_pass(tmp_path):
    """JSON summary result=pass when no failures."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    data = _extract_json(result.output)
    assert data["summary"]["result"] == "pass"


def test_run_json_summary_result_fail(tmp_path):
    """JSON summary result=fail when a step fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "error"
    mock_result.stderr = ""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", return_value=mock_result):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    data = _extract_json(result.output)
    assert data["summary"]["result"] == "fail"


def test_run_json_summary_steps_list(tmp_path):
    """JSON summary.steps is a list with step/status/duration/notes."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json"])
    data = _extract_json(result.output)
    steps = data["summary"]["steps"]
    assert isinstance(steps, list)
    assert len(steps) > 0
    first = steps[0]
    assert "step" in first
    assert "status" in first
    assert "duration" in first


def test_run_summary_table_title(tmp_path):
    """Summary table has 'Pipeline Summary' title."""
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["run", "--path", str(tmp_path)])
    assert "Pipeline Summary" in result.output


def test_lint_diff_step_uses_check_command(tmp_path):
    """lint-diff step must call agentlint check, not pass path as command."""
    calls = []
    def mock_run(tool, args, cwd=None):
        calls.append((tool, args))
        result = MagicMock()
        result.returncode = 0
        result.stdout = "clean"
        result.stderr = ""
        return result

    (tmp_path / "CLAUDE.md").write_text("# Test")
    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", side_effect=mock_run):
        runner.invoke(app, ["run", "--path", str(tmp_path), "--skip", "benchmark"])

    lint_diff_calls = [(t, a) for t, a in calls if a and a[0] == "check"]
    assert len(lint_diff_calls) >= 1, f"Expected agentlint check call, got: {calls}"
    assert lint_diff_calls[0][0] == "agentlint"
    assert lint_diff_calls[0][1][0] == "check"


def test_reflect_step_uses_from_notes_flag(tmp_path):
    """reflect step must use --from-notes, not --notes."""
    calls = []
    def mock_run(tool, args, cwd=None):
        calls.append((tool, args))
        result = MagicMock()
        result.returncode = 0
        result.stdout = "ok"
        result.stderr = ""
        return result

    with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.run_cmd.run_tool", side_effect=mock_run):
        runner.invoke(app, ["run", "--path", str(tmp_path), "--skip", "benchmark"])

    reflect_calls = [(t, a) for t, a in calls if t == "agentreflect"]
    assert len(reflect_calls) >= 1, f"Expected agentreflect call, got: {calls}"
    args = reflect_calls[0][1]
    assert "--from-notes" in args, f"Expected --from-notes in args, got: {args}"
    assert "--notes" not in args or "--from-notes" in args, "Should use --from-notes, not --notes"

"""Tests for agentkit gate."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.gate import evaluate_gate_rules, run_gate
from agentkit_cli.main import app

runner = CliRunner()


CURRENT_RESULTS = {
    "agentlint": {"score": 82},
    "agentmd": {"score": 78},
    "coderace": {"results": [{"agent": "codex", "score": 90}, {"agent": "claude", "score": 70}]},
    "agentreflect": {"suggestions_md": "### Tighten context"},
}

CURRENT_STATUSES = [
    {"tool": "agentlint", "installed": True, "status": "success"},
    {"tool": "agentmd", "installed": True, "status": "success"},
    {"tool": "coderace", "installed": True, "status": "success"},
    {"tool": "agentreflect", "installed": True, "status": "success"},
]


def test_evaluate_gate_rules_fails_below_min_score():
    passed, reasons, baseline_delta = evaluate_gate_rules(72.0, min_score=80.0)

    assert passed is False
    assert baseline_delta is None
    assert reasons == ["score 72.0 is below min-score 80.0"]


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_run_gate_passes_when_score_meets_threshold(mock_run_all, mock_tool_status, tmp_path: Path):
    result = run_gate(path=tmp_path, min_score=80.0)

    assert result.passed is True
    assert result.verdict == "PASS"
    assert result.score == 80.0
    assert result.failure_reasons == []


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_pass_exit_code_in_terminal_mode(mock_run_all, mock_tool_status, tmp_path: Path):
    result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "79"])

    assert result.exit_code == 0, result.output
    assert "Verdict:" in result.output
    assert "PASS" in result.output
    assert "80.0/100" in result.output


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_fail_exit_code_in_terminal_mode(mock_run_all, mock_tool_status, tmp_path: Path):
    result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "81"])

    assert result.exit_code == 1, result.output
    assert "FAIL" in result.output
    assert "below min-score 81.0" in result.output


def test_gate_help_registered():
    result = runner.invoke(app, ["gate", "--help"])

    assert result.exit_code == 0
    assert "--min-score" in result.output

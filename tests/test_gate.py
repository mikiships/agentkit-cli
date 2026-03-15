"""Tests for agentkit gate."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.gate import GateError, evaluate_gate_rules, run_gate
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


# ── D2: Baseline regression gating ────────────────────────────────────────────

def test_evaluate_gate_rules_fails_when_drop_exceeds_max_drop():
    passed, reasons, baseline_delta = evaluate_gate_rules(70.0, baseline_score=80.0, max_drop=5.0)

    assert passed is False
    assert baseline_delta == -10.0
    assert any("dropped" in r for r in reasons)


def test_evaluate_gate_rules_passes_when_drop_within_max_drop():
    passed, reasons, baseline_delta = evaluate_gate_rules(77.0, baseline_score=80.0, max_drop=5.0)

    assert passed is True
    assert baseline_delta == -3.0
    assert reasons == []


def test_evaluate_gate_rules_both_min_score_and_max_drop_enforced():
    passed, reasons, baseline_delta = evaluate_gate_rules(
        60.0, min_score=70.0, baseline_score=80.0, max_drop=5.0
    )

    assert passed is False
    assert len(reasons) == 2
    assert any("min-score" in r for r in reasons)
    assert any("dropped" in r for r in reasons)


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_run_gate_fails_with_invalid_baseline_file(mock_run_all, mock_tool_status, tmp_path: Path):
    bad_path = tmp_path / "nonexistent.json"

    try:
        run_gate(path=tmp_path, baseline_report=bad_path, max_drop=5.0)
        raise AssertionError("Expected GateError")
    except GateError as exc:
        assert "not found" in str(exc).lower() or "baseline" in str(exc).lower()


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_run_gate_fails_with_invalid_json_baseline(mock_run_all, mock_tool_status, tmp_path: Path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json", encoding="utf-8")

    try:
        run_gate(path=tmp_path, baseline_report=bad_file, max_drop=5.0)
        raise AssertionError("Expected GateError")
    except GateError as exc:
        assert "json" in str(exc).lower() or "invalid" in str(exc).lower()


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_baseline_regression_fail(mock_run_all, mock_tool_status, tmp_path: Path):
    # Current score is 80.0; baseline 90.0 → drop of 10 exceeds max-drop 5
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps({"score": 90.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["gate", "--path", str(tmp_path), "--baseline-report", str(baseline_file), "--max-drop", "5"],
    )

    assert result.exit_code == 1, result.output
    assert "FAIL" in result.output


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_baseline_regression_pass(mock_run_all, mock_tool_status, tmp_path: Path):
    # Current score is 80.0; baseline 83.0 → drop of 3 within max-drop 5
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps({"score": 83.0}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["gate", "--path", str(tmp_path), "--baseline-report", str(baseline_file), "--max-drop", "5"],
    )

    assert result.exit_code == 0, result.output
    assert "PASS" in result.output


# ── D3: Machine-readable outputs ───────────────────────────────────────────────

@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_json_output_is_valid_json(mock_run_all, mock_tool_status, tmp_path: Path):
    result = runner.invoke(app, ["gate", "--path", str(tmp_path), "--min-score", "79", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "verdict" in data
    assert "score" in data
    assert "grade" in data
    assert "thresholds" in data
    assert "failure_reasons" in data
    assert "passed" in data


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_output_writes_file(mock_run_all, mock_tool_status, tmp_path: Path):
    out_file = tmp_path / "result.json"
    result = runner.invoke(
        app, ["gate", "--path", str(tmp_path), "--min-score", "79", "--output", str(out_file)]
    )

    assert result.exit_code == 0, result.output
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["verdict"] == "PASS"


@patch("agentkit_cli.gate._tool_status", return_value=CURRENT_STATUSES)
@patch("agentkit_cli.gate.run_all", return_value=CURRENT_RESULTS)
def test_gate_cli_job_summary_prints_to_stdout_without_env(mock_run_all, mock_tool_status, tmp_path: Path):
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_STEP_SUMMARY"}
    result = runner.invoke(
        app,
        ["gate", "--path", str(tmp_path), "--min-score", "79", "--job-summary"],
        env=env,
    )

    assert result.exit_code == 0, result.output
    assert "## agentkit gate" in result.output
    assert "Verdict" in result.output

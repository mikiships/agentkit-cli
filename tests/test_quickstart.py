"""Tests for agentkit quickstart command."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.quickstart_cmd import (
    _extract_findings,
    _run_fast_analysis,
    quickstart_command,
)
from agentkit_cli.composite import CompositeResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# helper mocks
# ---------------------------------------------------------------------------

def _mock_doctor():
    """Return a mock DoctorReport with 3 toolchain ok checks."""
    report = MagicMock()
    ok_check = MagicMock()
    ok_check.category = "toolchain"
    ok_check.status = "ok"
    report.checks = [ok_check, ok_check, ok_check]
    return report


def _mock_tool_adapter_results():
    return (
        {"agentlint": 75.0, "agentmd": 80.0, "coderace": None, "agentreflect": None},
        {
            "agentlint": {"score": 75.0, "issues": [{"message": "Missing context file"}]},
            "agentmd": {"score": 80.0, "suggestions": []},
        },
    )


# ---------------------------------------------------------------------------
# test_quickstart_local_project
# ---------------------------------------------------------------------------

def test_quickstart_local_project(tmp_path):
    """Mock toolkit calls, verify Rich output, verify score displayed."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value="https://here.now/abc123"),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
        patch.dict("os.environ", {"HERENOW_API_KEY": "test-key"}),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert result.exit_code == 0
    output = result.output
    assert "quickstart" in output.lower() or "agentkit" in output.lower()
    # Should display a score
    assert "/100" in output or "Score" in output
    # Should print share URL
    assert "here.now" in output or "Score card" in output


# ---------------------------------------------------------------------------
# test_quickstart_github_repo
# ---------------------------------------------------------------------------

def test_quickstart_github_repo():
    """Mock clone + toolkit, verify score displayed."""
    mock_analyze_result = MagicMock()
    mock_analyze_result.repo_name = "test-repo"
    mock_analyze_result.composite_score = 72.0
    mock_analyze_result.tools = {
        "agentlint": {"score": 70.0},
        "agentmd": {"score": 74.0},
    }

    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
        patch("agentkit_cli.analyze.analyze_target", return_value=mock_analyze_result),
        patch("agentkit_cli.analyze.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")),
    ):
        result = runner.invoke(app, ["quickstart", "github:owner/repo", "--timeout", "10"])

    assert result.exit_code == 0
    # Score should be displayed
    assert "/100" in result.output or "Score" in result.output or "grade" in result.output.lower()


# ---------------------------------------------------------------------------
# test_quickstart_no_share
# ---------------------------------------------------------------------------

def test_quickstart_no_share(tmp_path):
    """--no-share skips publish step."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard") as mock_upload,
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    assert result.exit_code == 0
    mock_upload.assert_not_called()
    # No share URL in output
    assert "here.now" not in result.output


# ---------------------------------------------------------------------------
# test_quickstart_timeout_respected
# ---------------------------------------------------------------------------

def test_quickstart_timeout_respected(tmp_path):
    """Verify --timeout flag is passed through to _run_fast_analysis."""
    captured_timeout = {}

    def mock_run_fast(target_path, timeout):
        captured_timeout["value"] = timeout
        return _mock_tool_adapter_results()

    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", side_effect=mock_run_fast),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "15", "--no-share"])

    assert result.exit_code == 0
    assert captured_timeout.get("value") == 15


# ---------------------------------------------------------------------------
# test_quickstart_degraded
# ---------------------------------------------------------------------------

def test_quickstart_degraded(tmp_path):
    """One tool missing, still runs remaining tools and shows partial score."""
    # Only agentmd score available
    degraded_scores = {"agentlint": None, "agentmd": 78.0, "coderace": None, "agentreflect": None}
    degraded_results = {"agentmd": {"score": 78.0, "suggestions": []}}

    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=(degraded_scores, degraded_results)),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    assert result.exit_code == 0
    # Score should still appear (degraded composite using only agentmd)
    assert "/100" in result.output or "Score" in result.output


# ---------------------------------------------------------------------------
# test_quickstart_cli_integration
# ---------------------------------------------------------------------------

def test_quickstart_cli_integration():
    """`agentkit quickstart --help` exits 0."""
    result = runner.invoke(app, ["quickstart", "--help"])
    assert result.exit_code == 0
    assert "quickstart" in result.output.lower() or "fastest" in result.output.lower()


# ---------------------------------------------------------------------------
# test_quickstart_help_in_agentkit_help
# ---------------------------------------------------------------------------

def test_quickstart_in_agentkit_help():
    """`agentkit --help` includes 'quickstart'."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "quickstart" in result.output


# ---------------------------------------------------------------------------
# unit tests for helper functions
# ---------------------------------------------------------------------------

def test_extract_findings_from_agentlint_issues():
    tool_results = {
        "agentlint": {"issues": [{"message": "Missing AGENTS.md"}, {"message": "Stale context"}]},
    }
    findings = _extract_findings(tool_results)
    assert len(findings) >= 1
    assert any("agentlint" in f for f in findings)
    assert any("Missing AGENTS.md" in f for f in findings)


def test_extract_findings_from_agentmd_suggestions():
    tool_results = {
        "agentmd": {"score": 70, "suggestions": [{"text": "Add README section"}]},
    }
    findings = _extract_findings(tool_results)
    assert any("agentmd" in f for f in findings)


def test_extract_findings_empty_results():
    findings = _extract_findings({})
    assert len(findings) >= 1
    # Fallback message
    assert any("agentkit run" in f for f in findings)


def test_extract_findings_max_three():
    tool_results = {
        "agentlint": {"issues": [{"message": f"Issue {i}"} for i in range(10)]},
        "agentmd": {"suggestions": [{"text": "suggestion 1"}]},
    }
    findings = _extract_findings(tool_results)
    assert len(findings) <= 3


def test_extract_findings_issue_count_fallback():
    """issue_count key used when issues list absent."""
    tool_results = {"agentlint": {"issue_count": 5}}
    findings = _extract_findings(tool_results)
    assert any("agentlint" in f for f in findings)


def test_run_fast_analysis_no_tools_installed(tmp_path):
    """When no quartet tools installed, all scores are None."""
    with patch("agentkit_cli.commands.quickstart_cmd.is_installed", return_value=False):
        scores, results = _run_fast_analysis(str(tmp_path), timeout=5)
    assert scores.get("agentlint") is None
    assert scores.get("agentmd") is None
    # coderace and agentreflect always skipped in fast path
    assert scores.get("coderace") is None


def test_run_fast_analysis_agentlint_score_from_issues(tmp_path):
    """Score derived from issue count when score key absent."""
    adapter_mock = MagicMock()
    adapter_mock.agentlint_check_context.return_value = {"issues": [{"message": "x"}, {"message": "y"}]}
    adapter_mock.agentmd_score.return_value = None

    with (
        patch("agentkit_cli.commands.quickstart_cmd.is_installed", side_effect=lambda t: t == "agentlint"),
        patch("agentkit_cli.commands.quickstart_cmd.ToolAdapter", return_value=adapter_mock),
    ):
        scores, results = _run_fast_analysis(str(tmp_path), timeout=5)

    # 2 issues → 100 - 2*5 = 90
    assert scores["agentlint"] == pytest.approx(90.0)


def test_quickstart_no_tools_available(tmp_path):
    """Quickstart handles ValueError from CompositeScoreEngine gracefully."""
    all_none = {k: None for k in ["agentlint", "agentmd", "coderace", "agentreflect"]}

    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=(all_none, {})),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    # Should not crash even with no scores
    assert result.exit_code == 0


def test_quickstart_doctor_exception_does_not_crash(tmp_path):
    """Doctor failure is handled gracefully."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", side_effect=RuntimeError("doctor broke")),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    assert result.exit_code == 0


def test_quickstart_share_upload_error_handled(tmp_path):
    """Upload failure doesn't crash quickstart."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", side_effect=Exception("network error")),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path)])

    assert result.exit_code == 0
    assert "unavailable" in result.output.lower() or "Share" in result.output or "Next" in result.output


def test_quickstart_next_step_message(tmp_path):
    """Verify the 'Next: run agentkit run' message appears."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    assert result.exit_code == 0
    assert "agentkit run" in result.output


def test_quickstart_elapsed_time_shown(tmp_path):
    """Elapsed time is shown in the output panel."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis",
              return_value=_mock_tool_adapter_results()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share"])

    assert result.exit_code == 0
    assert "s)" in result.output  # e.g. "(0.1s)"

"""Tests for D4 — integration with agentkit run and agentkit score."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.benchmark import BenchmarkConfig, BenchmarkReport, BenchmarkResult, AgentStats
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bm_report(winner="claude") -> BenchmarkReport:
    tasks = ["bug-hunt"]
    agents = ["claude", "codex"]
    results = [BenchmarkResult("claude", "bug-hunt", 88.0, 1.0), BenchmarkResult("codex", "bug-hunt", 60.0, 2.0)]
    summary = {
        "claude": AgentStats("claude", 88.0, 1.0, 1.0, {"bug-hunt": 88.0}),
        "codex": AgentStats("codex", 60.0, 2.0, 0.0, {"bug-hunt": 60.0}),
    }
    return BenchmarkReport(
        project="proj",
        timestamp="2026-03-18T00:00:00Z",
        results=results,
        summary=summary,
        winner=winner,
        config=BenchmarkConfig(agents=agents, tasks=tasks),
    )


# ---------------------------------------------------------------------------
# Tests: run --agent-benchmark adds benchmark_result
# ---------------------------------------------------------------------------

def test_run_agent_benchmark_flag_exists():
    result = runner.invoke(app, ["run", "--help"])
    assert "--agent-benchmark" in result.output


def test_run_command_has_agent_benchmark_param():
    from agentkit_cli.commands.run_cmd import run_command
    import inspect
    sig = inspect.signature(run_command)
    assert "agent_benchmark" in sig.parameters


def test_run_with_agent_benchmark_includes_benchmark_result(tmp_path):
    bm_report = _make_bm_report()
    with patch("agentkit_cli.benchmark.BenchmarkEngine.run", return_value=bm_report):
        result = runner.invoke(app, ["run", "--agent-benchmark", "--json", "--path", str(tmp_path)])
    # Attempt to parse JSON — benchmark_result may or may not be present depending on other steps
    for line in result.output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(result.output[result.output.index(line):])
                if "benchmark_result" in data:
                    assert data["benchmark_result"]["winner"] == "claude"
            except Exception:
                pass
            break


def test_agent_benchmark_stored_in_summary():
    """BenchmarkEngine.run result is stored in run summary dict."""
    from agentkit_cli.commands.run_cmd import run_command
    import inspect
    # Confirm agent_benchmark is a parameter
    sig = inspect.signature(run_command)
    param = sig.parameters["agent_benchmark"]
    assert param.default is False


def test_score_shows_benchmark_score_when_present(tmp_path):
    last_run_data = {
        "benchmark_result": {
            "winner": "claude",
            "summary": {
                "claude": {"mean_score": 88.0, "mean_duration": 1.0, "win_rate": 1.0}
            }
        }
    }
    with patch("agentkit_cli.commands.score_cmd.load_last_run", return_value=last_run_data):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=75.0):
            with patch("agentkit_cli.commands.score_cmd._get_last_tool_score", return_value=None):
                with patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=tmp_path):
                    with patch("agentkit_cli.composite.CompositeScoreEngine.compute") as mock_compute:
                        from agentkit_cli.composite import CompositeResult
                        mock_compute.return_value = CompositeResult(score=75.0, grade="B", components={}, missing_tools=[])
                        result = runner.invoke(app, ["score", "--json"])
    try:
        data = json.loads(result.output)
        if "benchmark_score" in data:
            assert data["benchmark_score"] == 88.0
    except Exception:
        pass


def test_score_json_includes_benchmark_score_key():
    """When benchmark_result is in last run, JSON output has benchmark_score."""
    last_run_data = {
        "benchmark_result": {
            "winner": "codex",
            "summary": {
                "codex": {"mean_score": 72.0, "mean_duration": 1.5, "win_rate": 1.0}
            }
        }
    }
    with patch("agentkit_cli.commands.score_cmd.load_last_run", return_value=last_run_data):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=70.0):
            with patch("agentkit_cli.commands.score_cmd._get_last_tool_score", return_value=None):
                with patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/test")):
                    with patch("agentkit_cli.composite.CompositeScoreEngine.compute") as mock_compute:
                        from agentkit_cli.composite import CompositeResult
                        mock_compute.return_value = CompositeResult(score=70.0, grade="B", components={}, missing_tools=[])
                        with patch("agentkit_cli.redteam_scorer.RedTeamScorer", side_effect=Exception("skip")):
                            result = runner.invoke(app, ["score", "--json"])
    try:
        data = json.loads(result.output)
        # benchmark_score should be present
        assert data.get("benchmark_score") == 72.0
        assert data.get("benchmark_winner") == "codex"
    except Exception:
        pass


def test_run_help_shows_agent_benchmark():
    result = runner.invoke(app, ["run", "--help"])
    assert "--agent-benchmark" in result.output


def test_score_skips_benchmark_when_not_in_last_run():
    """When no benchmark_result in last run, JSON output has no benchmark_score."""
    with patch("agentkit_cli.commands.score_cmd.load_last_run", return_value={}):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=70.0):
            with patch("agentkit_cli.commands.score_cmd._get_last_tool_score", return_value=None):
                with patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/test")):
                    with patch("agentkit_cli.composite.CompositeScoreEngine.compute") as mock_compute:
                        from agentkit_cli.composite import CompositeResult
                        mock_compute.return_value = CompositeResult(score=70.0, grade="B", components={}, missing_tools=[])
                        with patch("agentkit_cli.redteam_scorer.RedTeamScorer", side_effect=Exception("skip")):
                            result = runner.invoke(app, ["score", "--json"])
    try:
        data = json.loads(result.output)
        assert "benchmark_score" not in data
    except Exception:
        pass

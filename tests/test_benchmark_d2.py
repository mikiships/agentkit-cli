"""Tests for agentkit benchmark CLI command (D2)."""
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

def _make_report(agents=None, tasks=None, winner="claude") -> BenchmarkReport:
    agents = agents or ["claude", "codex"]
    tasks = tasks or ["bug-hunt"]
    results = []
    for agent in agents:
        for task in tasks:
            score = 85.0 if agent == "claude" else 60.0
            results.append(BenchmarkResult(agent=agent, task=task, score=score, duration_s=1.5))
    summary = {
        a: AgentStats(
            agent=a,
            mean_score=85.0 if a == "claude" else 60.0,
            mean_duration=1.5,
            win_rate=1.0 if a == winner else 0.0,
            task_scores={t: 85.0 if a == winner else 60.0 for t in tasks},
        )
        for a in agents
    }
    return BenchmarkReport(
        project="test-proj",
        timestamp="2026-03-18T00:00:00Z",
        results=results,
        summary=summary,
        winner=winner,
        config=BenchmarkConfig(agents=agents, tasks=tasks),
    )


def _patch_engine(report=None):
    """Context manager patching BenchmarkEngine.run."""
    r = report or _make_report()

    class FakeEngine:
        def __init__(self, runner=None):
            pass

        def run(self, project_path, config=None, progress_callback=None):
            if progress_callback:
                for res in r.results:
                    progress_callback(res.agent, res.task, res.round_num, res)
            return r

    return patch("agentkit_cli.commands.benchmark_cmd.BenchmarkEngine", FakeEngine)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_benchmark_command_exists():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert result.exit_code == 0
    assert "benchmark" in result.output.lower()


def test_benchmark_help_shows_agents_option():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert "--agents" in result.output


def test_benchmark_help_shows_tasks_option():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert "--tasks" in result.output


def test_benchmark_help_shows_rounds_option():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert "--rounds" in result.output


def test_benchmark_help_shows_json_option():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert "--json" in result.output


def test_benchmark_help_shows_share_option():
    result = runner.invoke(app, ["benchmark", "--help"])
    assert "--share" in result.output


def test_benchmark_json_output():
    with _patch_engine():
        result = runner.invoke(app, ["benchmark", ".", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "project" in data
    assert "winner" in data
    assert "results" in data


def test_benchmark_shows_winner():
    with _patch_engine():
        result = runner.invoke(app, ["benchmark", "."])
    assert result.exit_code == 0
    assert "claude" in result.output.lower()


def test_benchmark_quiet_suppresses_output():
    with _patch_engine():
        result = runner.invoke(app, ["benchmark", ".", "--quiet"])
    assert result.exit_code == 0
    # quiet should produce minimal output (no "Running benchmark on:")
    assert "Running benchmark on:" not in result.output


def test_benchmark_custom_agents():
    report = _make_report(agents=["claude"])
    with _patch_engine(report=report):
        result = runner.invoke(app, ["benchmark", ".", "--agents", "claude"])
    assert result.exit_code == 0


def test_benchmark_custom_tasks():
    report = _make_report(tasks=["bug-hunt"])
    with _patch_engine(report=report):
        result = runner.invoke(app, ["benchmark", ".", "--tasks", "bug-hunt"])
    assert result.exit_code == 0


def test_benchmark_output_file(tmp_path):
    out = tmp_path / "report.html"
    with _patch_engine():
        with patch("agentkit_cli.benchmark_report.BenchmarkReportRenderer") as MockR:
            MockR.return_value.render.return_value = "<html>test</html>"
            result = runner.invoke(app, ["benchmark", ".", "--output", str(out)])
    assert result.exit_code == 0


def test_benchmark_json_contains_summary():
    with _patch_engine():
        result = runner.invoke(app, ["benchmark", ".", "--json"])
    data = json.loads(result.output)
    assert "summary" in data
    assert "claude" in data["summary"]

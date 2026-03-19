"""Tests for BenchmarkReportRenderer (D3)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from agentkit_cli.benchmark import BenchmarkConfig, BenchmarkReport, BenchmarkResult, AgentStats
from agentkit_cli.benchmark_report import BenchmarkReportRenderer, publish_benchmark


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(winner="claude") -> BenchmarkReport:
    tasks = ["bug-hunt", "refactor"]
    agents = ["claude", "codex"]
    results = [
        BenchmarkResult("claude", "bug-hunt", 90.0, 1.0),
        BenchmarkResult("claude", "refactor", 85.0, 1.2),
        BenchmarkResult("codex", "bug-hunt", 60.0, 2.0),
        BenchmarkResult("codex", "refactor", 55.0, 2.1),
    ]
    summary = {
        "claude": AgentStats("claude", 87.5, 1.1, 1.0, {"bug-hunt": 90.0, "refactor": 85.0}),
        "codex": AgentStats("codex", 57.5, 2.05, 0.0, {"bug-hunt": 60.0, "refactor": 55.0}),
    }
    return BenchmarkReport(
        project="myproject",
        timestamp="2026-03-18T00:00:00Z",
        results=results,
        summary=summary,
        winner=winner,
        config=BenchmarkConfig(agents=agents, tasks=tasks),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_renderer_returns_string():
    report = _make_report()
    html = BenchmarkReportRenderer().render(report)
    assert isinstance(html, str)
    assert len(html) > 100


def test_renderer_contains_project_name():
    report = _make_report()
    html = BenchmarkReportRenderer().render(report)
    assert "myproject" in html


def test_renderer_contains_winner():
    report = _make_report(winner="claude")
    html = BenchmarkReportRenderer().render(report)
    assert "claude" in html
    assert "👑" in html


def test_renderer_dark_theme():
    html = BenchmarkReportRenderer().render(_make_report())
    # Dark background
    assert "#0d1117" in html


def test_renderer_contains_task_names():
    html = BenchmarkReportRenderer().render(_make_report())
    assert "bug-hunt" in html
    assert "refactor" in html


def test_renderer_contains_agent_names():
    html = BenchmarkReportRenderer().render(_make_report())
    assert "claude" in html
    assert "codex" in html


def test_renderer_green_score():
    html = BenchmarkReportRenderer().render(_make_report())
    assert "score-green" in html


def test_renderer_red_score():
    # force a low score
    report = _make_report()
    report.results.append(BenchmarkResult("codex", "bug-hunt", 30.0, 1.0))
    # Rebuild summary with low score
    report.summary["codex"] = AgentStats("codex", 30.0, 1.5, 0.0, {"bug-hunt": 30.0})
    html = BenchmarkReportRenderer().render(report)
    assert "score-red" in html


def test_renderer_contains_win_rate():
    html = BenchmarkReportRenderer().render(_make_report())
    assert "Win Rate" in html or "win_rate" in html.lower() or "100%" in html


def test_renderer_valid_html():
    html = BenchmarkReportRenderer().render(_make_report())
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_publish_benchmark_returns_url():
    report = _make_report()
    with patch("agentkit_cli.benchmark_report._json_post") as mock_post, \
         patch("agentkit_cli.benchmark_report._put_file"), \
         patch("agentkit_cli.benchmark_report._finalize") as mock_fin:
        mock_post.return_value = {
            "siteId": "abc123",
            "files": [{"uploadUrl": "https://upload.example.com/abc"}],
        }
        mock_fin.return_value = {"url": "https://here.now/abc123"}
        url = publish_benchmark(report)
    assert url == "https://here.now/abc123"


def test_publish_benchmark_returns_none_on_error():
    report = _make_report()
    with patch("agentkit_cli.benchmark_report._json_post", side_effect=Exception("fail")):
        url = publish_benchmark(report)
    assert url is None

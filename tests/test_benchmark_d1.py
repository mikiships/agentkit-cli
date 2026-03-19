"""Tests for BenchmarkEngine (D1)."""
from __future__ import annotations

import pytest

from agentkit_cli.benchmark import (
    BenchmarkConfig,
    BenchmarkEngine,
    BenchmarkReport,
    BenchmarkResult,
    AgentStats,
    DEFAULT_AGENTS,
    DEFAULT_TASKS,
    DEFAULT_TIMEOUT,
    DEFAULT_ROUNDS,
    _compute_summary,
    _pick_winner,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_runner(score_map=None, error=None):
    """Return a runner that returns preset scores."""
    if score_map is None:
        score_map = {}

    def runner(agent, task, project_path, timeout):
        if error:
            return 0.0, error
        key = (agent, task)
        return score_map.get(key, 75.0), None

    return runner


def _simple_result(agent="claude", task="bug-hunt", score=80.0, error=None) -> BenchmarkResult:
    return BenchmarkResult(agent=agent, task=task, score=score, duration_s=1.0, error=error)


# ---------------------------------------------------------------------------
# BenchmarkConfig
# ---------------------------------------------------------------------------

def test_benchmark_config_defaults():
    cfg = BenchmarkConfig()
    assert cfg.agents == list(DEFAULT_AGENTS)
    assert cfg.tasks == list(DEFAULT_TASKS)
    assert cfg.timeout == DEFAULT_TIMEOUT
    assert cfg.rounds == DEFAULT_ROUNDS


def test_benchmark_config_custom():
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], timeout=60, rounds=3)
    assert cfg.agents == ["claude"]
    assert cfg.tasks == ["bug-hunt"]
    assert cfg.timeout == 60
    assert cfg.rounds == 3


# ---------------------------------------------------------------------------
# BenchmarkResult
# ---------------------------------------------------------------------------

def test_benchmark_result_to_dict():
    r = BenchmarkResult(agent="claude", task="bug-hunt", score=85.5, duration_s=2.3, error=None, round_num=1)
    d = r.to_dict()
    assert d["agent"] == "claude"
    assert d["task"] == "bug-hunt"
    assert d["score"] == 85.5
    assert d["duration_s"] == 2.3
    assert d["error"] is None
    assert d["round_num"] == 1


def test_benchmark_result_with_error():
    r = BenchmarkResult(agent="gemini", task="refactor", score=0.0, duration_s=0.5, error="timeout")
    d = r.to_dict()
    assert d["error"] == "timeout"
    assert d["score"] == 0.0


# ---------------------------------------------------------------------------
# BenchmarkEngine run
# ---------------------------------------------------------------------------

def test_engine_returns_benchmark_report():
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    assert isinstance(report, BenchmarkReport)


def test_engine_result_count():
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude", "codex"], tasks=["bug-hunt", "refactor"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    assert len(report.results) == 4  # 2 agents × 2 tasks


def test_engine_rounds_multiply_results():
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=3)
    report = engine.run("/tmp/proj", config=cfg)
    assert len(report.results) == 3


def test_engine_winner_set():
    scores = {("claude", "bug-hunt"): 90.0, ("codex", "bug-hunt"): 60.0}
    engine = BenchmarkEngine(runner=_mock_runner(score_map=scores))
    cfg = BenchmarkConfig(agents=["claude", "codex"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    assert report.winner == "claude"


def test_engine_project_name_from_path():
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/myrepo", config=cfg)
    assert report.project == "myrepo"


def test_engine_timestamp_set():
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    assert report.timestamp  # non-empty


def test_engine_progress_callback():
    calls = []

    def cb(agent, task, round_num, result):
        calls.append((agent, task, round_num))

    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    engine.run("/tmp/proj", config=cfg, progress_callback=cb)
    assert calls == [("claude", "bug-hunt", 1)]


def test_engine_error_runner():
    engine = BenchmarkEngine(runner=_mock_runner(error="coderace not installed"))
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    assert report.results[0].error == "coderace not installed"
    assert report.results[0].score == 0.0


# ---------------------------------------------------------------------------
# _compute_summary
# ---------------------------------------------------------------------------

def test_compute_summary_mean_score():
    results = [
        _simple_result("claude", "bug-hunt", 80.0),
        _simple_result("claude", "refactor", 60.0),
        _simple_result("codex", "bug-hunt", 70.0),
        _simple_result("codex", "refactor", 50.0),
    ]
    summary = _compute_summary(results, ["bug-hunt", "refactor"])
    assert summary["claude"].mean_score == 70.0
    assert summary["codex"].mean_score == 60.0


def test_compute_summary_win_rate():
    results = [
        _simple_result("claude", "bug-hunt", 90.0),
        _simple_result("claude", "refactor", 90.0),
        _simple_result("codex", "bug-hunt", 50.0),
        _simple_result("codex", "refactor", 50.0),
    ]
    summary = _compute_summary(results, ["bug-hunt", "refactor"])
    assert summary["claude"].win_rate == 1.0
    assert summary["codex"].win_rate == 0.0


def test_compute_summary_excludes_errors():
    results = [
        BenchmarkResult("claude", "bug-hunt", 0.0, 1.0, error="fail"),
        _simple_result("codex", "bug-hunt", 70.0),
    ]
    summary = _compute_summary(results, ["bug-hunt"])
    # claude had error, codex wins; claude mean_score excludes error
    assert summary["claude"].mean_score == 0.0
    assert summary["codex"].win_rate == 1.0


def test_pick_winner_highest_score():
    summary = {
        "claude": AgentStats("claude", 85.0, 2.0, 0.6),
        "codex": AgentStats("codex", 70.0, 1.5, 0.4),
    }
    assert _pick_winner(summary) == "claude"


def test_report_to_dict_json_serializable():
    import json
    engine = BenchmarkEngine(runner=_mock_runner())
    cfg = BenchmarkConfig(agents=["claude"], tasks=["bug-hunt"], rounds=1)
    report = engine.run("/tmp/proj", config=cfg)
    d = report.to_dict()
    # Should not raise
    json.dumps(d)
    assert "project" in d
    assert "results" in d
    assert "summary" in d
    assert "winner" in d


def test_default_tasks_contains_context_use():
    assert "context-use" in DEFAULT_TASKS


def test_default_tasks_count():
    assert len(DEFAULT_TASKS) == 5

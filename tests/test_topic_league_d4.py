"""D4 tests for topic-league integration (run --topic-league flag, JSON parsability, token guard)."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.commands.topic_league_cmd import topic_league_command
from agentkit_cli.engines.topic_league import TopicLeagueResult, LeagueResult, ScoreDistribution
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(rank, name, score, grade="B", stars=10):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=stars)


def _mock_result(topic, scores):
    entries = [_entry(i + 1, f"{topic}/repo{i}", s) for i, s in enumerate(scores)]
    return TopicRankResult(topic=topic, entries=entries, generated_at="", total_analyzed=len(entries))


def _make_factory(results_map):
    def factory(topic, limit):
        mock = MagicMock()
        mock.run.return_value = results_map[topic]
        return mock
    return factory


# ---------------------------------------------------------------------------
# JSON parsability
# ---------------------------------------------------------------------------

def test_json_output_parseable(capsys):
    results_map = {
        "python": _mock_result("python", [80.0, 70.0]),
        "rust": _mock_result("rust", [60.0, 55.0]),
    }
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=2,
        json_output=True,
        quiet=False,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "standings" in data
    assert isinstance(data["standings"], list)
    assert len(data["standings"]) == 2


def test_json_fields_complete(capsys):
    results_map = {
        "python": _mock_result("python", [80.0]),
        "rust": _mock_result("rust", [60.0]),
    }
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=1,
        json_output=True,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "topics" in data
    assert "timestamp" in data
    assert "topic_results" in data


def test_json_standings_rank_ordering(capsys):
    results_map = {
        "python": _mock_result("python", [90.0]),
        "rust": _mock_result("rust", [50.0]),
        "go": _mock_result("go", [70.0]),
    }
    topic_league_command(
        topics=["python", "rust", "go"],
        repos_per_topic=1,
        json_output=True,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    ranks = [s["rank"] for s in data["standings"]]
    assert ranks == sorted(ranks)
    assert data["standings"][0]["topic"] == "python"


# ---------------------------------------------------------------------------
# Token guard — missing GITHUB_TOKEN should warn, not crash
# ---------------------------------------------------------------------------

def test_missing_token_warns_not_crashes(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    results_map = {
        "python": _mock_result("python", [70.0]),
        "rust": _mock_result("rust", [60.0]),
    }
    # Should not raise; should print warning
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=1,
        json_output=False,
        quiet=False,
        token=None,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    assert "Warning" in captured.out or "GITHUB_TOKEN" in captured.out


def test_missing_token_json_mode_no_crash(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    results_map = {
        "python": _mock_result("python", [70.0]),
        "rust": _mock_result("rust", [60.0]),
    }
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=1,
        json_output=True,
        token=None,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "standings" in data


# ---------------------------------------------------------------------------
# run --topic-league flag wiring
# ---------------------------------------------------------------------------

def test_run_topic_league_flag_wires():
    """Verify the --topic-league flag exists on the run command."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app
    runner = CliRunner()
    r = runner.invoke(app, ["run", "--help"])
    assert "--topic-league" in r.output


# ---------------------------------------------------------------------------
# Parallel mode produces same count
# ---------------------------------------------------------------------------

def test_parallel_same_count_as_sequential():
    results_map = {
        "a": _mock_result("a", [80.0]),
        "b": _mock_result("b", [70.0]),
        "c": _mock_result("c", [60.0]),
    }
    from agentkit_cli.engines.topic_league import TopicLeagueEngine
    engine_seq = TopicLeagueEngine(
        topics=["a", "b", "c"],
        repos_per_topic=1,
        parallel=False,
        _engine_factory=_make_factory(results_map),
    )
    engine_par = TopicLeagueEngine(
        topics=["a", "b", "c"],
        repos_per_topic=1,
        parallel=True,
        _engine_factory=_make_factory(results_map),
    )
    r_seq = engine_seq.run()
    r_par = engine_par.run()
    assert len(r_seq.standings) == len(r_par.standings) == 3


def test_integration_score_distribution_present(capsys):
    results_map = {
        "python": _mock_result("python", [80.0, 70.0, 60.0]),
        "rust": _mock_result("rust", [50.0]),
    }
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=3,
        json_output=True,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    s = next(s for s in data["standings"] if s["topic"] == "python")
    dist = s["score_distribution"]
    assert dist["min"] == 60.0
    assert dist["max"] == 80.0
    assert dist["mean"] == pytest.approx(70.0, abs=0.01)


def test_integration_repo_count(capsys):
    results_map = {
        "python": _mock_result("python", [80.0, 70.0, 60.0]),
        "rust": _mock_result("rust", [50.0]),
    }
    topic_league_command(
        topics=["python", "rust"],
        repos_per_topic=3,
        json_output=True,
        _engine_factory=_make_factory(results_map),
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    s = next(s for s in data["standings"] if s["topic"] == "python")
    assert s["repo_count"] == 3

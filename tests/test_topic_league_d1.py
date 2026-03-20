"""D1 tests for TopicLeagueEngine."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentkit_cli.engines.topic_league import (
    TopicLeagueEngine,
    TopicLeagueResult,
    LeagueResult,
    ScoreDistribution,
    _compute_distribution,
    _build_standings,
)
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(rank, name, score, grade="B", stars=10, desc=""):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=stars, description=desc)


def _mock_result(topic, entries):
    return TopicRankResult(
        topic=topic,
        entries=entries,
        generated_at="2026-01-01 00:00 UTC",
        total_analyzed=len(entries),
    )


def _make_factory(results_map):
    def factory(topic, limit):
        mock = MagicMock()
        mock.run.return_value = results_map[topic]
        return mock
    return factory


# ---------------------------------------------------------------------------
# Unit: ScoreDistribution
# ---------------------------------------------------------------------------

def test_compute_distribution_empty():
    dist = _compute_distribution([])
    assert dist.min_score == 0.0
    assert dist.mean_score == 0.0
    assert dist.max_score == 0.0


def test_compute_distribution_single():
    dist = _compute_distribution([_entry(1, "a/b", 75.0)])
    assert dist.min_score == 75.0
    assert dist.mean_score == 75.0
    assert dist.max_score == 75.0


def test_compute_distribution_multiple():
    entries = [_entry(1, "a/b", 80.0), _entry(2, "c/d", 60.0), _entry(3, "e/f", 70.0)]
    dist = _compute_distribution(entries)
    assert dist.min_score == 60.0
    assert dist.mean_score == pytest.approx(70.0, abs=0.01)
    assert dist.max_score == 80.0


def test_score_distribution_to_dict():
    dist = ScoreDistribution(min_score=50.0, mean_score=65.0, max_score=80.0)
    d = dist.to_dict()
    assert d["min"] == 50.0
    assert d["mean"] == 65.0
    assert d["max"] == 80.0


# ---------------------------------------------------------------------------
# Unit: _build_standings
# ---------------------------------------------------------------------------

def test_build_standings_order():
    results = {
        "python": _mock_result("python", [_entry(1, "a/a", 80.0), _entry(2, "b/b", 70.0)]),
        "rust": _mock_result("rust", [_entry(1, "c/c", 50.0)]),
        "go": _mock_result("go", [_entry(1, "d/d", 90.0)]),
    }
    standings = _build_standings(results)
    assert standings[0].topic == "go"
    assert standings[1].topic == "python"
    assert standings[2].topic == "rust"


def test_build_standings_ranks():
    results = {
        "a": _mock_result("a", [_entry(1, "x/x", 70.0)]),
        "b": _mock_result("b", [_entry(1, "y/y", 60.0)]),
    }
    standings = _build_standings(results)
    assert standings[0].rank == 1
    assert standings[1].rank == 2


def test_build_standings_top_repo():
    results = {
        "topic": _mock_result("topic", [
            _entry(1, "best/repo", 90.0),
            _entry(2, "other/repo", 60.0),
        ]),
        "topic2": _mock_result("topic2", [_entry(1, "x/x", 50.0)]),
    }
    standings = _build_standings(results)
    # topic should be #1
    s = next(s for s in standings if s.topic == "topic")
    assert s.top_repo == "best/repo"


# ---------------------------------------------------------------------------
# TopicLeagueEngine init validation
# ---------------------------------------------------------------------------

def test_engine_requires_min_topics():
    with pytest.raises(ValueError, match="at least 2"):
        TopicLeagueEngine(topics=["python"])


def test_engine_rejects_too_many_topics():
    with pytest.raises(ValueError, match="at most 10"):
        TopicLeagueEngine(topics=[f"t{i}" for i in range(11)])


def test_engine_accepts_exactly_2():
    engine = TopicLeagueEngine(topics=["python", "rust"])
    assert len(engine.topics) == 2


def test_engine_accepts_exactly_10():
    engine = TopicLeagueEngine(topics=[f"t{i}" for i in range(10)])
    assert len(engine.topics) == 10


def test_engine_clamps_repos_per_topic():
    engine = TopicLeagueEngine(topics=["a", "b"], repos_per_topic=99)
    assert engine.repos_per_topic == 10


# ---------------------------------------------------------------------------
# TopicLeagueEngine.run (mocked)
# ---------------------------------------------------------------------------

def _make_engine(topics, results_map, parallel=False):
    return TopicLeagueEngine(
        topics=topics,
        repos_per_topic=3,
        parallel=parallel,
        _engine_factory=_make_factory(results_map),
    )


def test_engine_run_basic():
    results_map = {
        "python": _mock_result("python", [_entry(1, "a/a", 80.0, "A")]),
        "rust": _mock_result("rust", [_entry(1, "b/b", 65.0, "B")]),
    }
    engine = _make_engine(["python", "rust"], results_map)
    result = engine.run()
    assert isinstance(result, TopicLeagueResult)
    assert len(result.standings) == 2
    assert result.standings[0].topic == "python"


def test_engine_run_parallel():
    results_map = {
        "a": _mock_result("a", [_entry(1, "x/x", 70.0, "B")]),
        "b": _mock_result("b", [_entry(1, "y/y", 60.0, "C")]),
        "c": _mock_result("c", [_entry(1, "z/z", 80.0, "A")]),
    }
    engine = _make_engine(["a", "b", "c"], results_map, parallel=True)
    result = engine.run()
    assert len(result.standings) == 3
    assert result.standings[0].topic == "c"


def test_engine_run_progress_cb():
    calls = []
    results_map = {
        "x": _mock_result("x", [_entry(1, "a/a", 70.0)]),
        "y": _mock_result("y", [_entry(1, "b/b", 60.0)]),
    }
    engine = _make_engine(["x", "y"], results_map)
    engine.run(progress_cb=lambda topic, idx, total, name: calls.append(topic))
    # progress_cb passed to inner engine; mock captures the call chain


def test_league_result_to_dict():
    results_map = {
        "python": _mock_result("python", [_entry(1, "a/a", 80.0, "A")]),
        "rust": _mock_result("rust", [_entry(1, "b/b", 65.0, "B")]),
    }
    engine = _make_engine(["python", "rust"], results_map)
    result = engine.run()
    d = result.to_dict()
    assert "standings" in d
    assert "topic_results" in d
    assert "timestamp" in d
    assert len(d["standings"]) == 2


def test_league_result_standing_to_dict():
    results_map = {
        "alpha": _mock_result("alpha", [_entry(1, "x/x", 90.0, "A")]),
        "beta": _mock_result("beta", [_entry(1, "y/y", 50.0, "C")]),
    }
    engine = _make_engine(["alpha", "beta"], results_map)
    result = engine.run()
    s = result.standings[0]
    d = s.to_dict()
    assert d["topic"] == "alpha"
    assert d["rank"] == 1
    assert "score_distribution" in d
    assert d["score_distribution"]["min"] == 90.0

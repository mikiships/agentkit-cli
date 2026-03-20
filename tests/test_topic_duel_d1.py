"""D1 tests for TopicDuelEngine."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentkit_cli.engines.topic_duel import (
    TopicDuelEngine,
    TopicDuelResult,
    TopicDuelDimension,
    _avg_score,
    _top_score,
    _grade_a_count,
    _compute_dimensions,
    _overall_winner,
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


def _make_engine_factory(results_map):
    """Return a factory that yields mock TopicRankEngines from a {topic: TopicRankResult} dict."""
    def factory(topic, limit):
        mock_engine = MagicMock()
        mock_engine.run.return_value = results_map[topic]
        return mock_engine
    return factory


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

def test_avg_score_empty():
    assert _avg_score([]) == 0.0


def test_avg_score_basic():
    entries = [_entry(1, "a/a", 80.0), _entry(2, "b/b", 60.0)]
    assert _avg_score(entries) == 70.0


def test_top_score_empty():
    assert _top_score([]) == 0.0


def test_top_score_basic():
    entries = [_entry(1, "a/a", 80.0), _entry(2, "b/b", 60.0)]
    assert _top_score(entries) == 80.0


def test_grade_a_count():
    entries = [
        _entry(1, "a/a", 90.0, grade="A"),
        _entry(2, "b/b", 65.0, grade="B"),
        _entry(3, "c/c", 85.0, grade="A"),
    ]
    assert _grade_a_count(entries) == 2


def test_compute_dimensions_topic1_wins_avg():
    e1 = [_entry(1, "x/x", 85.0, "A"), _entry(2, "y/y", 75.0, "B")]
    e2 = [_entry(1, "a/a", 50.0, "C"), _entry(2, "b/b", 45.0, "D")]
    dims = _compute_dimensions("t1", "t2", e1, e2)
    avg_dim = next(d for d in dims if d.name == "avg_score")
    assert avg_dim.winner == "topic1"


def test_compute_dimensions_tie():
    e1 = [_entry(1, "x/x", 70.0, "B")]
    e2 = [_entry(1, "a/a", 70.0, "B")]
    dims = _compute_dimensions("t1", "t2", e1, e2)
    avg_dim = next(d for d in dims if d.name == "avg_score")
    assert avg_dim.winner == "tie"


def test_overall_winner_clear():
    assert _overall_winner(80.0, 60.0, []) == "topic1"
    assert _overall_winner(55.0, 75.0, []) == "topic2"


def test_overall_winner_tie():
    assert _overall_winner(70.0, 70.0, []) == "tie"


# ---------------------------------------------------------------------------
# Engine integration (mocked)
# ---------------------------------------------------------------------------

def test_engine_returns_topic_duel_result():
    r1 = _mock_result("fastapi", [_entry(1, "t/a", 80.0, "A"), _entry(2, "t/b", 70.0, "B")])
    r2 = _mock_result("django", [_entry(1, "d/a", 60.0, "C"), _entry(2, "d/b", 50.0, "C")])
    factory = _make_engine_factory({"fastapi": r1, "django": r2})

    engine = TopicDuelEngine("fastapi", "django", repos_per_topic=2, _engine_factory=factory)
    result = engine.run()

    assert isinstance(result, TopicDuelResult)
    assert result.topic1 == "fastapi"
    assert result.topic2 == "django"
    assert result.overall_winner == "topic1"


def test_engine_winner_declared_when_topic2_better():
    r1 = _mock_result("a", [_entry(1, "t/a", 40.0, "D")])
    r2 = _mock_result("b", [_entry(1, "b/a", 90.0, "A")])
    factory = _make_engine_factory({"a": r1, "b": r2})

    engine = TopicDuelEngine("a", "b", repos_per_topic=1, _engine_factory=factory)
    result = engine.run()

    assert result.overall_winner == "topic2"


def test_engine_avg_scores_populated():
    r1 = _mock_result("p", [_entry(1, "x/a", 80.0, "A"), _entry(2, "x/b", 60.0, "B")])
    r2 = _mock_result("q", [_entry(1, "y/a", 70.0, "B")])
    factory = _make_engine_factory({"p": r1, "q": r2})

    engine = TopicDuelEngine("p", "q", _engine_factory=factory)
    result = engine.run()

    assert result.topic1_avg_score == 70.0
    assert result.topic2_avg_score == 70.0


def test_engine_dimensions_populated():
    r1 = _mock_result("x", [_entry(1, "a/a", 80.0, "A")])
    r2 = _mock_result("y", [_entry(1, "b/b", 60.0, "B")])
    factory = _make_engine_factory({"x": r1, "y": r2})

    engine = TopicDuelEngine("x", "y", _engine_factory=factory)
    result = engine.run()

    assert len(result.dimensions) >= 1
    names = [d.name for d in result.dimensions]
    assert "avg_score" in names


def test_engine_to_dict():
    r1 = _mock_result("a", [_entry(1, "a/a", 75.0, "B")])
    r2 = _mock_result("b", [_entry(1, "b/b", 65.0, "B")])
    factory = _make_engine_factory({"a": r1, "b": r2})

    result = TopicDuelEngine("a", "b", _engine_factory=factory).run()
    d = result.to_dict()
    assert d["topic1"] == "a"
    assert d["topic2"] == "b"
    assert "dimensions" in d
    assert isinstance(d["dimensions"], list)


def test_engine_empty_topics():
    r1 = _mock_result("empty1", [])
    r2 = _mock_result("empty2", [])
    factory = _make_engine_factory({"empty1": r1, "empty2": r2})

    engine = TopicDuelEngine("empty1", "empty2", _engine_factory=factory)
    result = engine.run()

    assert result.overall_winner == "tie"
    assert result.topic1_avg_score == 0.0
    assert result.topic2_avg_score == 0.0

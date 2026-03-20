"""Tests for D1: RepoDuelEngine core."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentkit_cli.repo_duel import (
    RepoDuelEngine,
    RepoDuelResult,
    DimensionResult,
    _make_dimension,
    _tool_score,
)
from agentkit_cli.analyze import AnalyzeResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_analyze_result(target, score=70.0, grade="B", tools=None):
    return AnalyzeResult(
        target=target,
        repo_name=target.split("/")[-1],
        composite_score=score,
        grade=grade,
        tools=tools or {
            "agentmd": {"score": score, "status": "pass", "finding": "ok"},
            "coderace": {"score": score - 5, "status": "pass", "finding": "ok"},
            "agentlint": {"score": score + 5, "status": "pass", "finding": "ok"},
            "agentreflect": {"score": score, "status": "pass", "finding": "ok"},
        },
    )


def _analyze_factory(results_map):
    def factory(target, timeout):
        return results_map[target]
    return factory


# ---------------------------------------------------------------------------
# _make_dimension
# ---------------------------------------------------------------------------

def test_make_dimension_repo1_wins():
    d = _make_dimension("composite_score", 80.0, 60.0)
    assert d.winner == "repo1"
    assert d.delta == 20.0


def test_make_dimension_repo2_wins():
    d = _make_dimension("composite_score", 60.0, 80.0)
    assert d.winner == "repo2"


def test_make_dimension_draw():
    d = _make_dimension("composite_score", 70.0, 70.0)
    assert d.winner == "draw"


def test_make_dimension_lower_wins():
    d = _make_dimension("errors", 2.0, 5.0, higher_wins=False)
    assert d.winner == "repo1"


# ---------------------------------------------------------------------------
# _tool_score
# ---------------------------------------------------------------------------

def test_tool_score_returns_value():
    r = _make_analyze_result("repo", score=75.0)
    assert _tool_score(r, "agentmd") == 75.0


def test_tool_score_missing_returns_zero():
    from agentkit_cli.analyze import AnalyzeResult
    r = AnalyzeResult(target="repo", repo_name="repo", composite_score=70.0, grade="B", tools={})
    assert _tool_score(r, "agentmd") == 0.0


def test_tool_score_none_returns_zero():
    from agentkit_cli.analyze import AnalyzeResult
    r = AnalyzeResult(target="repo", repo_name="repo", composite_score=70.0, grade="B", tools={"agentmd": {"score": None}})
    assert _tool_score(r, "agentmd") == 0.0


# ---------------------------------------------------------------------------
# RepoDuelEngine
# ---------------------------------------------------------------------------

def test_engine_repo1_wins():
    r1 = _make_analyze_result("github:a/repo1", score=90.0, grade="A")
    r2 = _make_analyze_result("github:b/repo2", score=50.0, grade="C")
    factory = _analyze_factory({"github:a/repo1": r1, "github:b/repo2": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("github:a/repo1", "github:b/repo2")
    assert isinstance(result, RepoDuelResult)
    assert result.winner == "repo1"


def test_engine_repo2_wins():
    r1 = _make_analyze_result("github:a/repo1", score=40.0, grade="D")
    r2 = _make_analyze_result("github:b/repo2", score=95.0, grade="A")
    factory = _analyze_factory({"github:a/repo1": r1, "github:b/repo2": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("github:a/repo1", "github:b/repo2")
    assert result.winner == "repo2"


def test_engine_draw():
    r1 = _make_analyze_result("r1", score=70.0, tools={"agentmd": {"score": 70.0}, "coderace": {"score": 70.0}, "agentlint": {"score": 70.0}, "agentreflect": {"score": 70.0}})
    r2 = _make_analyze_result("r2", score=70.0, tools={"agentmd": {"score": 70.0}, "coderace": {"score": 70.0}, "agentlint": {"score": 70.0}, "agentreflect": {"score": 70.0}})
    factory = _analyze_factory({"r1": r1, "r2": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("r1", "r2")
    assert result.winner == "draw"


def test_engine_has_4_dimensions_by_default():
    r1 = _make_analyze_result("a", score=80.0)
    r2 = _make_analyze_result("b", score=60.0)
    factory = _analyze_factory({"a": r1, "b": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("a", "b")
    assert len(result.dimension_results) == 4


def test_engine_deep_adds_redteam_dimension():
    r1 = _make_analyze_result("a", score=80.0)
    r2 = _make_analyze_result("b", score=60.0)
    factory = _analyze_factory({"a": r1, "b": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("a", "b", deep=True)
    assert len(result.dimension_results) == 5
    names = [d.name for d in result.dimension_results]
    assert "redteam_resistance" in names


def test_result_stores_repos():
    r1 = _make_analyze_result("repo1", score=80.0)
    r2 = _make_analyze_result("repo2", score=60.0)
    factory = _analyze_factory({"repo1": r1, "repo2": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("repo1", "repo2")
    assert result.repo1 == "repo1"
    assert result.repo2 == "repo2"


def test_result_stores_scores_and_grades():
    r1 = _make_analyze_result("r1", score=90.0, grade="A")
    r2 = _make_analyze_result("r2", score=55.0, grade="C")
    factory = _analyze_factory({"r1": r1, "r2": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("r1", "r2")
    assert result.repo1_score == 90.0
    assert result.repo2_score == 55.0
    assert result.repo1_grade == "A"
    assert result.repo2_grade == "C"


def test_result_to_dict():
    r1 = _make_analyze_result("a", score=80.0)
    r2 = _make_analyze_result("b", score=60.0)
    factory = _analyze_factory({"a": r1, "b": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("a", "b")
    d = result.to_dict()
    assert "repo1" in d
    assert "repo2" in d
    assert "dimension_results" in d
    assert "winner" in d
    assert "run_date" in d


def test_dimension_result_to_dict():
    d = DimensionResult(name="composite_score", repo1_value=80.0, repo2_value=60.0, winner="repo1", delta=20.0)
    dd = d.to_dict()
    assert dd["name"] == "composite_score"
    assert dd["winner"] == "repo1"
    assert dd["delta"] == 20.0


def test_result_run_date_set():
    r1 = _make_analyze_result("a", score=80.0)
    r2 = _make_analyze_result("b", score=60.0)
    factory = _analyze_factory({"a": r1, "b": r2})
    engine = RepoDuelEngine(_analyze_factory=factory)
    result = engine.run_duel("a", "b")
    assert result.run_date != ""

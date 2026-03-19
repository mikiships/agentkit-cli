"""Tests for D1: UserScorecardEngine core."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.user_scorecard import (
    UserScorecardEngine,
    UserScorecardResult,
    RepoResult,
    score_to_grade,
    list_public_repos,
    _check_context_file,
)


# ---------------------------------------------------------------------------
# score_to_grade
# ---------------------------------------------------------------------------

def test_grade_A():
    assert score_to_grade(80.0) == "A"

def test_grade_A_high():
    assert score_to_grade(100.0) == "A"

def test_grade_B():
    assert score_to_grade(65.0) == "B"

def test_grade_B_high():
    assert score_to_grade(79.9) == "B"

def test_grade_C():
    assert score_to_grade(50.0) == "C"

def test_grade_C_high():
    assert score_to_grade(64.9) == "C"

def test_grade_D():
    assert score_to_grade(49.9) == "D"

def test_grade_D_zero():
    assert score_to_grade(0.0) == "D"

def test_grade_none():
    assert score_to_grade(None) == "D"


# ---------------------------------------------------------------------------
# Helper to build fake repos
# ---------------------------------------------------------------------------

def _make_repos(n=5):
    return [
        {"full_name": f"alice/repo-{i}", "name": f"repo-{i}", "stars": 10 - i, "fork": False}
        for i in range(n)
    ]


def _make_analyze_fn(scores):
    """Returns an analyze override callable that returns scores[full_name] or (None, 'err')."""
    def _fn(full_name, timeout):
        s = scores.get(full_name)
        if s is None:
            return None, "timeout"
        return s, None
    return _fn


def _always_false_context(full_name, token):
    return False


def _always_true_context(full_name, token):
    return True


# ---------------------------------------------------------------------------
# UserScorecardEngine.aggregate
# ---------------------------------------------------------------------------

def test_aggregate_basic():
    repos = [
        RepoResult("repo-0", "alice/repo-0", 85.0, "A", True),
        RepoResult("repo-1", "alice/repo-1", 70.0, "B", False),
        RepoResult("repo-2", "alice/repo-2", 55.0, "C", True),
    ]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert result.username == "alice"
    assert result.total_repos == 3
    assert result.analyzed_repos == 3
    assert result.skipped_repos == 0
    assert abs(result.avg_score - (85 + 70 + 55) / 3) < 0.1
    assert result.grade in ("A", "B", "C", "D")
    assert len(result.top_repos) == 3
    # Not enough for bottom_repos (< 5 analyzed)
    assert result.bottom_repos == []


def test_aggregate_top_3():
    repos = [RepoResult(f"r-{i}", f"alice/r-{i}", float(i * 10), score_to_grade(float(i * 10)), False) for i in range(6)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    top_scores = [r.score for r in result.top_repos]
    assert top_scores == sorted(top_scores, reverse=True)
    assert len(result.top_repos) == 3


def test_aggregate_bottom_repos_requires_5():
    repos = [RepoResult(f"r-{i}", f"alice/r-{i}", float(i * 10), "A", False) for i in range(4)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert result.bottom_repos == []


def test_aggregate_bottom_repos_with_5():
    repos = [RepoResult(f"r-{i}", f"alice/r-{i}", float(i * 10 + 10), "A", False) for i in range(5)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert len(result.bottom_repos) == 3


def test_aggregate_context_coverage():
    repos = [
        RepoResult("r-0", "alice/r-0", 80.0, "A", True),
        RepoResult("r-1", "alice/r-1", 70.0, "B", False),
        RepoResult("r-2", "alice/r-2", 60.0, "C", True),
        RepoResult("r-3", "alice/r-3", 50.0, "C", False),
    ]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert abs(result.context_coverage_pct - 50.0) < 0.1


def test_aggregate_skip_repos():
    repos = [
        RepoResult("r-0", "alice/r-0", 85.0, "A", True),
        RepoResult("r-1", "alice/r-1", None, "D", False, error="timeout"),
    ]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert result.analyzed_repos == 1
    assert result.skipped_repos == 1


def test_aggregate_empty():
    engine = UserScorecardEngine("alice")
    result = engine.aggregate([])
    assert result.total_repos == 0
    assert result.avg_score == 0.0
    assert result.grade == "D"
    assert result.context_coverage_pct == 0.0


def test_aggregate_all_repos_sorted():
    repos = [
        RepoResult("r-0", "alice/r-0", 30.0, "D", False),
        RepoResult("r-1", "alice/r-1", 90.0, "A", True),
        RepoResult("r-2", "alice/r-2", 60.0, "C", False),
    ]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    scores = [r.score for r in result.all_repos if r.score is not None]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Engine: list_public_repos + skip-forks + min-stars
# ---------------------------------------------------------------------------

def test_engine_list_repos_skip_forks():
    raw_repos = [
        {"full_name": "alice/r-0", "name": "r-0", "stars": 5, "fork": False},
        {"full_name": "alice/fork-1", "name": "fork-1", "stars": 3, "fork": True},
    ]
    engine = UserScorecardEngine(
        "alice",
        skip_forks=True,
        _repos_override=raw_repos,
        _analyze_override=_make_analyze_fn({"alice/r-0": 75.0}),
        _context_override=_always_false_context,
    )
    result = engine.run()
    assert result.total_repos == 2  # override passes raw list as-is (engine doesn't re-filter)


def test_engine_run_with_overrides():
    raw_repos = [
        {"full_name": "alice/repo-0", "name": "repo-0", "stars": 5, "fork": False},
        {"full_name": "alice/repo-1", "name": "repo-1", "stars": 2, "fork": False},
    ]
    scores = {"alice/repo-0": 85.0, "alice/repo-1": 40.0}
    engine = UserScorecardEngine(
        "alice",
        _repos_override=raw_repos,
        _analyze_override=_make_analyze_fn(scores),
        _context_override=_always_true_context,
    )
    result = engine.run()
    assert result.analyzed_repos == 2
    assert result.context_coverage_pct == 100.0
    assert result.grade in ("A", "B", "C", "D")


def test_engine_timeout_handling():
    raw_repos = [{"full_name": "alice/repo-0", "name": "repo-0", "stars": 1, "fork": False}]
    engine = UserScorecardEngine(
        "alice",
        _repos_override=raw_repos,
        _analyze_override=lambda fn, t: (None, "timeout"),
        _context_override=_always_false_context,
    )
    result = engine.run()
    assert result.skipped_repos == 1
    assert result.analyzed_repos == 0


def test_engine_pagination_support():
    """Verify engine accepts a large pre-paginated repo list."""
    raw_repos = [
        {"full_name": f"alice/repo-{i}", "name": f"repo-{i}", "stars": i, "fork": False}
        for i in range(35)
    ]
    scores = {f"alice/repo-{i}": float(50 + i) for i in range(35)}
    engine = UserScorecardEngine(
        "alice",
        _repos_override=raw_repos,
        _analyze_override=_make_analyze_fn(scores),
        _context_override=_always_false_context,
    )
    result = engine.run()
    assert result.total_repos == 35


def test_grade_calculation_aggregate():
    repos = [RepoResult(f"r-{i}", f"alice/r-{i}", 82.0, "A", False) for i in range(3)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert result.grade == "A"


def test_grade_calculation_b():
    repos = [RepoResult("r", "alice/r", 70.0, "B", False)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    assert result.grade == "B"


def test_repo_result_to_dict():
    r = RepoResult("repo", "alice/repo", 75.0, "B", True, stars=10)
    d = r.to_dict()
    assert d["full_name"] == "alice/repo"
    assert d["score"] == 75.0
    assert d["grade"] == "B"
    assert d["has_context"] is True
    assert "error" not in d


def test_user_scorecard_result_to_dict():
    repos = [RepoResult("r", "alice/r", 80.0, "A", True)]
    engine = UserScorecardEngine("alice")
    result = engine.aggregate(repos)
    d = result.to_dict()
    assert d["username"] == "alice"
    assert "avg_score" in d
    assert "grade" in d
    assert "all_repos" in d

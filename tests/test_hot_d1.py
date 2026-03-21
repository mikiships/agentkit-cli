"""Tests for agentkit hot D1 — HotEngine, fetch, score, tweet generation."""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.hot import (
    HotEngine,
    HotRepoResult,
    HotResult,
    _FALLBACK_REPOS,
    _build_tweet_text,
    _find_most_surprising,
    _grade_from_score,
    _parse_trending_html,
    fetch_github_trending,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_repo_result(rank=1, score=75.0, grade="B", full_name="owner/repo", language="Python"):
    return HotRepoResult(
        full_name=full_name,
        rank=rank,
        score=score,
        grade=grade,
        description="A test repo",
        stars=1000,
        language=language,
    )


def _mock_fetch(language=None, limit=10):
    repos = [
        {"full_name": f"owner/repo{i+1}", "description": f"Repo {i+1}", "stars": 100 * (10 - i), "language": "Python"}
        for i in range(min(limit, 10))
    ]
    return repos, True


def _mock_score(full_name, timeout=60):
    scores = {
        "owner/repo1": (85.0, "B", {}),
        "owner/repo2": (30.0, "F", {}),
        "owner/repo3": (60.0, "C", {}),
    }
    return scores.get(full_name, (50.0, "C", {}))


# ---------------------------------------------------------------------------
# _grade_from_score
# ---------------------------------------------------------------------------

def test_grade_from_score_a():
    assert _grade_from_score(95) == "A"


def test_grade_from_score_b():
    assert _grade_from_score(80) == "B"


def test_grade_from_score_c():
    assert _grade_from_score(65) == "C"


def test_grade_from_score_d():
    assert _grade_from_score(45) == "D"


def test_grade_from_score_f():
    assert _grade_from_score(20) == "F"


def test_grade_from_score_boundary_a():
    assert _grade_from_score(90) == "A"


def test_grade_from_score_boundary_b():
    assert _grade_from_score(75) == "B"


# ---------------------------------------------------------------------------
# _find_most_surprising
# ---------------------------------------------------------------------------

def test_find_most_surprising_low_score_top3():
    repos = [
        _make_repo_result(rank=1, score=25.0, grade="F", full_name="owner/top1"),
        _make_repo_result(rank=2, score=80.0, grade="B", full_name="owner/top2"),
        _make_repo_result(rank=3, score=70.0, grade="C", full_name="owner/top3"),
    ]
    result = _find_most_surprising(repos)
    assert result is not None
    assert result.full_name == "owner/top1"


def test_find_most_surprising_high_score_top5():
    repos = [
        _make_repo_result(rank=1, score=95.0, grade="A", full_name="owner/hot1"),
        _make_repo_result(rank=2, score=70.0, grade="C", full_name="owner/hot2"),
    ]
    result = _find_most_surprising(repos)
    assert result is not None
    assert result.full_name == "owner/hot1"


def test_find_most_surprising_returns_something_with_no_scores():
    repos = [_make_repo_result(rank=1, score=None, grade=None, full_name="owner/r1")]
    result = _find_most_surprising(repos)
    assert result is not None


def test_find_most_surprising_empty():
    result = _find_most_surprising([])
    assert result is None


# ---------------------------------------------------------------------------
# _build_tweet_text
# ---------------------------------------------------------------------------

def test_tweet_text_low_score():
    repos = [_make_repo_result(rank=1, score=25.0, grade="F", full_name="owner/tornado")]
    ms = repos[0]
    tweet = _build_tweet_text(repos, ms, None)
    assert len(tweet) <= 280
    assert "tornado" in tweet
    assert "25" in tweet


def test_tweet_text_high_score():
    repos = [_make_repo_result(rank=1, score=92.0, grade="A", full_name="owner/fastapi")]
    ms = repos[0]
    tweet = _build_tweet_text(repos, ms, None)
    assert len(tweet) <= 280
    assert "fastapi" in tweet


def test_tweet_text_with_language():
    repos = [_make_repo_result(rank=3, score=60.0, grade="C", full_name="owner/flask")]
    ms = repos[0]
    tweet = _build_tweet_text(repos, ms, "python")
    assert len(tweet) <= 280
    assert "python" in tweet


def test_tweet_text_no_most_surprising():
    repos = [_make_repo_result(rank=1, score=50.0, full_name="owner/r1")]
    tweet = _build_tweet_text(repos, None, None)
    assert len(tweet) <= 280
    assert len(tweet) > 0


def test_tweet_text_never_exceeds_280():
    repos = [_make_repo_result(rank=1, score=85.0, grade="B",
                               full_name="owner/" + "x" * 50)]
    ms = repos[0]
    tweet = _build_tweet_text(repos, ms, "somelanguagewithalongname")
    assert len(tweet) <= 280


# ---------------------------------------------------------------------------
# fetch_github_trending
# ---------------------------------------------------------------------------

def test_fetch_github_trending_fallback_on_error():
    with patch("agentkit_cli.hot._requests_module") as mock_requests:
        mock_requests.get.side_effect = Exception("network error")
        repos, available = fetch_github_trending(limit=5)
        assert available is False
        assert len(repos) <= 5
        assert all("full_name" in r for r in repos)


def test_fetch_github_trending_fallback_on_non_200():
    with patch("agentkit_cli.hot._requests_module") as mock_requests:
        resp = MagicMock()
        resp.status_code = 503
        mock_requests.get.return_value = resp
        repos, available = fetch_github_trending(limit=5)
        assert available is False


def test_fetch_github_trending_fallback_limit():
    with patch("agentkit_cli.hot._requests_module") as mock_requests:
        mock_requests.get.side_effect = Exception("timeout")
        repos, available = fetch_github_trending(limit=3)
        assert len(repos) == 3


# ---------------------------------------------------------------------------
# _parse_trending_html
# ---------------------------------------------------------------------------

def test_parse_trending_html_empty():
    result = _parse_trending_html("", limit=10)
    assert isinstance(result, list)


def test_parse_trending_html_no_articles():
    html = "<html><body><p>No repos</p></body></html>"
    result = _parse_trending_html(html, limit=10)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# HotEngine
# ---------------------------------------------------------------------------

def test_hot_engine_run_basic():
    engine = HotEngine(timeout=5)
    result = engine.run(
        language=None,
        limit=3,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    assert isinstance(result, HotResult)
    assert len(result.repos) == 3
    assert result.tweet_text
    assert len(result.tweet_text) <= 280


def test_hot_engine_run_with_language():
    engine = HotEngine(timeout=5)
    result = engine.run(
        language="python",
        limit=3,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    assert result.language_filter == "python"


def test_hot_engine_limit_respected():
    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=2,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    assert len(result.repos) == 2


def test_hot_engine_limit_max_25():
    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=100,
        _fetch_fn=lambda language=None, limit=10: (
            [{"full_name": f"o/r{i}", "description": "", "stars": 0, "language": ""} for i in range(limit)],
            True,
        ),
        _score_fn=lambda fn, t=60: (50.0, "C", {}),
    )
    assert len(result.repos) <= 25


def test_hot_engine_most_surprising_not_none():
    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=3,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    assert result.most_surprising is not None


def test_hot_engine_repos_have_ranks():
    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=3,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    ranks = [r.rank for r in result.repos]
    assert ranks == list(range(1, len(result.repos) + 1))


def test_hot_engine_unavailable_trending():
    def fetch_unavailable(language=None, limit=10):
        repos = [{"full_name": f"o/r{i}", "description": "", "stars": 0, "language": ""} for i in range(limit)]
        return repos, False

    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=3,
        _fetch_fn=fetch_unavailable,
        _score_fn=lambda fn, t=60: (50.0, "C", {}),
    )
    assert result.trending_available is False


def test_hot_engine_to_dict():
    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=2,
        _fetch_fn=_mock_fetch,
        _score_fn=_mock_score,
    )
    d = result.to_dict()
    assert "repos" in d
    assert "tweet_text" in d
    assert "most_surprising" in d
    assert "run_date" in d


def test_hot_engine_score_none_handled():
    """Score function returns None — should not crash."""
    def score_none(full_name, timeout=60):
        return None, None, {}

    engine = HotEngine(timeout=5)
    result = engine.run(
        limit=2,
        _fetch_fn=_mock_fetch,
        _score_fn=score_none,
    )
    assert isinstance(result, HotResult)
    assert all(r.score is None for r in result.repos)


def test_hot_repo_result_to_dict():
    r = _make_repo_result()
    d = r.to_dict()
    assert d["full_name"] == "owner/repo"
    assert d["rank"] == 1
    assert d["score"] == 75.0


def test_fallback_repos_structure():
    for repo in _FALLBACK_REPOS:
        assert "full_name" in repo
        assert "/" in repo["full_name"]
        assert "description" in repo


def test_fallback_repos_count():
    assert len(_FALLBACK_REPOS) >= 10

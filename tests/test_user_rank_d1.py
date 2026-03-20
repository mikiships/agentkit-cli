"""Tests for D1: UserRankEngine core."""
from __future__ import annotations

import json
import pytest

from agentkit_cli.user_rank import (
    UserRankEngine,
    UserRankResult,
    UserRankEntry,
    search_topic_contributors,
)
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult, score_to_grade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_result(username: str, avg_score: float, top_repo: str = "repo-a") -> UserScorecardResult:
    grade = score_to_grade(avg_score)
    repo = RepoResult(
        name=top_repo,
        full_name=f"{username}/{top_repo}",
        score=avg_score,
        grade=grade,
        has_context=True,
    )
    return UserScorecardResult(
        username=username,
        total_repos=5,
        analyzed_repos=5,
        skipped_repos=0,
        avg_score=avg_score,
        grade=grade,
        context_coverage_pct=50.0,
        top_repos=[repo],
        bottom_repos=[],
        all_repos=[repo],
    )


def _make_engine(contributors, scores_map):
    """Create engine with mocked contributors and scorecard results."""
    def _scorecard_factory(username, token, timeout):
        score = scores_map.get(username, 50.0)
        return _make_user_result(username, score)

    return UserRankEngine(
        topic="python",
        limit=20,
        _contributors_override=contributors,
        _scorecard_factory=_scorecard_factory,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_rank_engine_instantiation():
    engine = UserRankEngine(topic="python")
    assert engine.topic == "python"
    assert engine.limit == 20


def test_user_rank_engine_custom_limit():
    engine = UserRankEngine(topic="rust", limit=5)
    assert engine.limit == 5


def test_fetch_contributors_uses_override():
    engine = UserRankEngine(topic="go", _contributors_override=["alice", "bob", "charlie"])
    contribs = engine.fetch_contributors()
    assert contribs == ["alice", "bob", "charlie"]


def test_fetch_contributors_respects_limit():
    members = [f"user{i}" for i in range(30)]
    engine = UserRankEngine(topic="go", limit=5, _contributors_override=members)
    contribs = engine.fetch_contributors()
    assert len(contribs) == 5


def test_rank_contributors_sorted_by_score():
    engine = _make_engine(["alice", "bob", "charlie"], {"alice": 80.0, "bob": 60.0, "charlie": 90.0})
    results = [
        _make_user_result("alice", 80.0),
        _make_user_result("bob", 60.0),
        _make_user_result("charlie", 90.0),
    ]
    entries = engine.rank_contributors(results)
    assert entries[0].username == "charlie"
    assert entries[1].username == "alice"
    assert entries[2].username == "bob"


def test_rank_contributors_assigns_ranks():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 60.0})
    results = [_make_user_result("alice", 80.0), _make_user_result("bob", 60.0)]
    entries = engine.rank_contributors(results)
    assert entries[0].rank == 1
    assert entries[1].rank == 2


def test_rank_entry_has_grade():
    engine = _make_engine(["alice"], {"alice": 85.0})
    result = _make_user_result("alice", 85.0)
    entries = engine.rank_contributors([result])
    assert entries[0].grade == "A"


def test_rank_entry_has_top_repo():
    engine = _make_engine(["alice"], {"alice": 85.0})
    result = _make_user_result("alice", 85.0, top_repo="myrepo")
    entries = engine.rank_contributors([result])
    assert entries[0].top_repo == "myrepo"


def test_rank_entry_has_avatar_url():
    engine = _make_engine(["alice"], {"alice": 85.0})
    result = _make_user_result("alice", 85.0)
    entries = engine.rank_contributors([result])
    assert "github.com/alice" in entries[0].avatar_url


def test_build_result_top_scorer():
    engine = _make_engine(["alice", "bob"], {"alice": 90.0, "bob": 60.0})
    result = engine.run()
    assert result.top_scorer == "alice"


def test_build_result_mean_score():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 60.0})
    result = engine.run()
    assert abs(result.mean_score - 70.0) < 1.0


def test_build_result_grade_distribution():
    engine = _make_engine(["alice", "bob"], {"alice": 90.0, "bob": 30.0})
    result = engine.run()
    assert result.grade_distribution["A"] == 1
    assert result.grade_distribution["D"] == 1


def test_build_result_empty_contributors():
    engine = UserRankEngine(topic="python", _contributors_override=[], _scorecard_factory=lambda u, t, to: None)
    result = engine.run()
    assert result.contributors == []
    assert result.top_scorer == ""
    assert result.mean_score == 0.0


def test_user_rank_result_to_dict():
    engine = _make_engine(["alice"], {"alice": 80.0})
    result = engine.run()
    d = result.to_dict()
    assert d["topic"] == "python"
    assert isinstance(d["contributors"], list)
    assert "top_scorer" in d
    assert "mean_score" in d
    assert "grade_distribution" in d


def test_user_rank_result_to_dict_json_serializable():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 60.0})
    result = engine.run()
    d = result.to_dict()
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["topic"] == "python"


def test_user_rank_entry_to_dict():
    entry = UserRankEntry(rank=1, username="alice", score=85.0, grade="A", top_repo="myrepo")
    d = entry.to_dict()
    assert d["rank"] == 1
    assert d["username"] == "alice"
    assert d["score"] == 85.0
    assert d["grade"] == "A"
    assert d["top_repo"] == "myrepo"


def test_search_topic_contributors_returns_empty_on_error(monkeypatch):
    """search_topic_contributors returns [] when API fails."""
    import agentkit_cli.user_rank as ur
    monkeypatch.setattr(ur, "_fetch_page", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail")))
    result = search_topic_contributors("python", token=None, limit=5)
    assert result == []


def test_search_topic_contributors_deduplicates(monkeypatch):
    """search_topic_contributors deduplicates logins across repos."""
    import agentkit_cli.user_rank as ur

    search_response = [
        {"owner": {"login": "org1"}, "name": "repo1"},
        {"owner": {"login": "org1"}, "name": "repo2"},
    ]
    contrib_response = [
        {"login": "alice", "contributions": 10},
        {"login": "bob", "contributions": 5},
    ]

    call_count = [0]

    def fake_fetch(url, token):
        call_count[0] += 1
        if "search/repositories" in url:
            return search_response, {}, None
        return contrib_response, {}, None

    monkeypatch.setattr(ur, "_fetch_page", fake_fetch)
    result = search_topic_contributors("python", token=None, limit=10)
    # alice and bob should each appear once despite two repos
    assert result.count("alice") == 1
    assert result.count("bob") == 1

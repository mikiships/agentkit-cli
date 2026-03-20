"""Tests for D1: TeamScorecardEngine core."""
from __future__ import annotations

import json
import pytest

from agentkit_cli.user_team import (
    TeamScorecardEngine,
    TeamScorecardResult,
)
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult, score_to_grade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_result(username: str, avg_score: float) -> UserScorecardResult:
    grade = score_to_grade(avg_score)
    return UserScorecardResult(
        username=username,
        total_repos=5,
        analyzed_repos=5,
        skipped_repos=0,
        avg_score=avg_score,
        grade=grade,
        context_coverage_pct=50.0,
        top_repos=[],
        bottom_repos=[],
        all_repos=[],
    )


def _make_engine(members, scores_map):
    """Create engine with mocked members and scorecard results."""
    def _scorecard_factory(username, token, timeout):
        score = scores_map.get(username, 50.0)
        return _make_user_result(username, score)

    return TeamScorecardEngine(
        org="testorg",
        limit=10,
        _members_override=members,
        _scorecard_factory=_scorecard_factory,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_team_scorecard_engine_instantiation():
    engine = TeamScorecardEngine(org="testorg")
    assert engine.org == "testorg"
    assert engine.limit == 10


def test_team_scorecard_engine_custom_limit():
    engine = TeamScorecardEngine(org="testorg", limit=5)
    assert engine.limit == 5


def test_fetch_contributors_uses_override():
    engine = TeamScorecardEngine(org="testorg", _members_override=["alice", "bob", "charlie"])
    contribs = engine.fetch_contributors()
    assert contribs == ["alice", "bob", "charlie"]


def test_fetch_contributors_respects_limit():
    members = [f"user{i}" for i in range(20)]
    engine = TeamScorecardEngine(org="testorg", limit=5, _members_override=members)
    contribs = engine.fetch_contributors()
    assert len(contribs) == 5


def test_per_contributor_score_aggregation():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 60.0})
    result = engine.run()
    usernames = [r.username for r in result.contributor_results]
    assert "alice" in usernames
    assert "bob" in usernames


def test_aggregate_score_calculation_mean():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 60.0})
    result = engine.run()
    assert abs(result.aggregate_score - 70.0) < 0.01


def test_grade_assignment_A():
    engine = _make_engine(["alice"], {"alice": 85.0})
    result = engine.run()
    assert result.aggregate_grade == "A"


def test_grade_assignment_B():
    engine = _make_engine(["alice"], {"alice": 70.0})
    result = engine.run()
    assert result.aggregate_grade == "B"


def test_grade_assignment_D():
    engine = _make_engine(["alice"], {"alice": 30.0})
    result = engine.run()
    assert result.aggregate_grade == "D"


def test_top_scorer_extraction():
    engine = _make_engine(["alice", "bob", "charlie"], {"alice": 90.0, "bob": 60.0, "charlie": 70.0})
    result = engine.run()
    assert result.top_scorer == "alice"


def test_limit_flag_behavior():
    members = [f"user{i}" for i in range(10)]
    scores = {f"user{i}": 70.0 for i in range(10)}
    engine = TeamScorecardEngine(org="testorg", limit=3, _members_override=members,
                                  _scorecard_factory=lambda u, t, to: _make_user_result(u, scores.get(u, 50.0)))
    result = engine.run()
    assert result.contributor_count == 3


def test_empty_org_handling():
    engine = TeamScorecardEngine(org="emptyorg", _members_override=[])
    result = engine.run()
    assert result.contributor_count == 0
    assert result.aggregate_score == 0.0
    assert result.top_scorer == ""


def test_single_contributor_org():
    engine = _make_engine(["solo"], {"solo": 75.0})
    result = engine.run()
    assert result.contributor_count == 1
    assert result.top_scorer == "solo"
    assert abs(result.aggregate_score - 75.0) < 0.01


def test_api_error_handling(monkeypatch):
    from urllib import error as urllib_error

    def _raise(*args, **kwargs):
        raise urllib_error.HTTPError(url="", code=403, msg="Forbidden", hdrs=None, fp=None)

    import agentkit_cli.user_team as ut
    monkeypatch.setattr(ut, "fetch_org_contributors", _raise)
    monkeypatch.setattr(ut, "fetch_org_members", _raise)

    engine = TeamScorecardEngine(org="private-org", limit=5)
    with pytest.raises((ValueError, Exception)):
        engine.fetch_contributors()


def test_json_serialization():
    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 65.0})
    result = engine.run()
    d = result.to_dict()
    assert d["org"] == "testorg"
    assert "contributor_results" in d
    assert "aggregate_score" in d
    assert "aggregate_grade" in d
    assert "top_scorer" in d
    # Should be JSON-serializable
    payload = json.dumps(d)
    parsed = json.loads(payload)
    assert parsed["org"] == "testorg"


def test_integration_result_structure():
    engine = _make_engine(["alice", "bob", "charlie"],
                          {"alice": 90.0, "bob": 70.0, "charlie": 55.0})
    result = engine.run()
    assert isinstance(result, TeamScorecardResult)
    assert result.org == "testorg"
    assert len(result.contributor_results) == 3
    assert result.aggregate_score > 0
    assert result.aggregate_grade in ("A", "B", "C", "D")
    assert result.top_scorer == "alice"
    assert result.contributor_count == 3


def test_grade_distribution_counting():
    """Grade distribution should correctly count contributions by grade."""
    engine = _make_engine(
        ["u1", "u2", "u3", "u4"],
        {"u1": 90.0, "u2": 75.0, "u3": 60.0, "u4": 40.0}
    )
    result = engine.run()
    # u1: A, u2: B, u3: C, u4: D
    assert any(r.grade == "A" for r in result.contributor_results)
    assert any(r.grade == "B" for r in result.contributor_results)
    assert any(r.grade == "C" for r in result.contributor_results)
    assert any(r.grade == "D" for r in result.contributor_results)


def test_contributor_ordering_by_score():
    """Contributors should be orderable by score."""
    engine = _make_engine(
        ["alice", "bob", "charlie"],
        {"alice": 50.0, "bob": 90.0, "charlie": 70.0}
    )
    result = engine.run()
    scores = [r.avg_score for r in result.contributor_results]
    assert 50.0 in scores
    assert 90.0 in scores
    assert 70.0 in scores


def test_progress_callback_invoked():
    """Progress callback should be called for each contributor."""
    calls = []
    def _cb(idx, total, username):
        calls.append((idx, total, username))

    engine = _make_engine(["alice", "bob"], {"alice": 80.0, "bob": 70.0})
    engine.run(progress_callback=_cb)
    assert len(calls) == 2
    assert calls[0][2] == "alice"
    assert calls[1][2] == "bob"


def test_timestamp_present_in_result():
    """Result should have a non-empty timestamp."""
    engine = _make_engine(["alice"], {"alice": 75.0})
    result = engine.run()
    assert result.timestamp
    assert len(result.timestamp) > 0

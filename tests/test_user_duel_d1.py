"""Tests for D1: UserDuelEngine core."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentkit_cli.user_duel import (
    UserDuelEngine,
    UserDuelResult,
    DuelDimension,
    _make_dim,
    _fmt_dim_value,
)
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scorecard(username, avg_score, grade, analyzed=5, all_repos=None):
    if all_repos is None:
        all_repos = [
            RepoResult(name=f"repo{i}", full_name=f"{username}/repo{i}", score=avg_score,
                       grade=grade, has_context=(i % 2 == 0), stars=i * 10)
            for i in range(analyzed)
        ]
    return UserScorecardResult(
        username=username,
        total_repos=analyzed,
        analyzed_repos=analyzed,
        skipped_repos=0,
        avg_score=avg_score,
        grade=grade,
        context_coverage_pct=50.0,
        top_repos=all_repos[:3],
        bottom_repos=[],
        all_repos=all_repos,
    )


def _engine_factory(scorecard_map):
    """Return a factory that uses prebuilt scorecards."""
    def factory(username, limit, token, timeout):
        mock_engine = MagicMock()
        mock_engine.run = MagicMock(return_value=scorecard_map[username])
        return mock_engine
    return factory


# ---------------------------------------------------------------------------
# _make_dim
# ---------------------------------------------------------------------------

def test_make_dim_user1_wins():
    d = _make_dim("avg_score", 80.0, 60.0, higher_wins=True)
    assert d.winner == "user1"


def test_make_dim_user2_wins():
    d = _make_dim("avg_score", 60.0, 80.0, higher_wins=True)
    assert d.winner == "user2"


def test_make_dim_tie():
    d = _make_dim("avg_score", 70.0, 70.0, higher_wins=True)
    assert d.winner == "tie"


def test_make_dim_lower_wins():
    d = _make_dim("errors", 2.0, 5.0, higher_wins=False)
    assert d.winner == "user1"


# ---------------------------------------------------------------------------
# _fmt_dim_value
# ---------------------------------------------------------------------------

def test_fmt_dim_avg_score():
    assert _fmt_dim_value("avg_score", 75.5) == "75.5"


def test_fmt_dim_letter_grade():
    assert _fmt_dim_value("letter_grade", 4.0) == "A"
    assert _fmt_dim_value("letter_grade", 3.0) == "B"
    assert _fmt_dim_value("letter_grade", 2.0) == "C"
    assert _fmt_dim_value("letter_grade", 1.0) == "D"


def test_fmt_dim_repo_count():
    assert _fmt_dim_value("repo_count", 10.0) == "10"


def test_fmt_dim_agent_ready_repos():
    assert _fmt_dim_value("agent_ready_repos", 3.0) == "3"


# ---------------------------------------------------------------------------
# UserDuelEngine
# ---------------------------------------------------------------------------

def test_duel_engine_user1_wins():
    s1 = _make_scorecard("alice", 85.0, "A", analyzed=5)
    s2 = _make_scorecard("bob", 60.0, "C", analyzed=3)
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert isinstance(result, UserDuelResult)
    assert result.overall_winner == "user1"
    assert not result.tied


def test_duel_engine_user2_wins():
    s1 = _make_scorecard("alice", 50.0, "C", analyzed=2)
    s2 = _make_scorecard("bob", 90.0, "A", analyzed=8)
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert result.overall_winner == "user2"
    assert not result.tied


def test_duel_engine_tie():
    # Same scores, same grade, same repo count, same agent ready repos
    repos1 = [RepoResult(f"r{i}", f"alice/r{i}", 70.0, "B", True, stars=5) for i in range(4)]
    repos2 = [RepoResult(f"r{i}", f"bob/r{i}", 70.0, "B", True, stars=5) for i in range(4)]
    s1 = _make_scorecard("alice", 70.0, "B", analyzed=4, all_repos=repos1)
    s2 = _make_scorecard("bob", 70.0, "B", analyzed=4, all_repos=repos2)
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert result.tied


def test_duel_result_has_dimensions():
    s1 = _make_scorecard("alice", 75.0, "B")
    s2 = _make_scorecard("bob", 65.0, "C")
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert len(result.dimensions) == 4  # avg_score, letter_grade, repo_count, agent_ready_repos


def test_duel_result_to_dict():
    s1 = _make_scorecard("alice", 80.0, "A")
    s2 = _make_scorecard("bob", 60.0, "C")
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    d = result.to_dict()
    assert d["user1"] == "alice"
    assert d["user2"] == "bob"
    assert "dimensions" in d
    assert "overall_winner" in d
    assert "tied" in d


def test_duel_dimension_to_dict():
    d = DuelDimension(name="avg_score", user1_value=80.0, user2_value=60.0, winner="user1")
    dd = d.to_dict()
    assert dd["name"] == "avg_score"
    assert dd["user1_value"] == 80.0
    assert dd["winner"] == "user1"


def test_duel_agent_ready_repos_dimension():
    # user1 has more repos with context
    repos1 = [RepoResult(f"r{i}", f"alice/r{i}", 70.0, "B", has_context=True, stars=5) for i in range(5)]
    repos2 = [RepoResult(f"r{i}", f"bob/r{i}", 70.0, "B", has_context=False, stars=5) for i in range(5)]
    s1 = _make_scorecard("alice", 70.0, "B", analyzed=5, all_repos=repos1)
    s2 = _make_scorecard("bob", 70.0, "B", analyzed=5, all_repos=repos2)
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    ar_dim = next(d for d in result.dimensions if d.name == "agent_ready_repos")
    assert ar_dim.winner == "user1"
    assert ar_dim.user1_value == 5.0
    assert ar_dim.user2_value == 0.0


def test_duel_timestamps_set():
    s1 = _make_scorecard("alice", 80.0, "A")
    s2 = _make_scorecard("bob", 60.0, "C")
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert result.timestamp != ""


def test_duel_users_stored_correctly():
    s1 = _make_scorecard("alice", 80.0, "A")
    s2 = _make_scorecard("bob", 60.0, "C")
    factory = _engine_factory({"alice": s1, "bob": s2})
    engine = UserDuelEngine(_engine_factory=factory)
    result = engine.run("alice", "bob")
    assert result.user1 == "alice"
    assert result.user2 == "bob"

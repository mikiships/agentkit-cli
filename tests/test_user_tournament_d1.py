"""Tests for D1: UserTournamentEngine core."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.engines.user_tournament import (
    Standings,
    TournamentResult,
    UserTournamentEngine,
)
from agentkit_cli.user_duel import UserDuelResult, DuelDimension
from agentkit_cli.user_scorecard import UserScorecardResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scorecard(handle: str, avg_score: float = 75.0) -> UserScorecardResult:
    sc = MagicMock(spec=UserScorecardResult)
    sc.avg_score = avg_score
    sc.grade = "A" if avg_score >= 80 else "B"
    sc.analyzed_repos = 5
    sc.all_repos = []
    sc.to_dict.return_value = {"handle": handle, "avg_score": avg_score}
    return sc


def _make_duel_result(u1: str, u2: str, winner: str = "user1", tied: bool = False, s1: float = 80.0, s2: float = 60.0) -> UserDuelResult:
    sc1 = _make_scorecard(u1, s1)
    sc2 = _make_scorecard(u2, s2)
    dims = [DuelDimension(name="avg_score", user1_value=s1, user2_value=s2, winner=winner)]
    r = MagicMock(spec=UserDuelResult)
    r.user1 = u1
    r.user2 = u2
    r.user1_scorecard = sc1
    r.user2_scorecard = sc2
    r.dimensions = dims
    r.overall_winner = winner
    r.tied = tied
    r.timestamp = "2026-01-01 00:00 UTC"
    r.to_dict.return_value = {"user1": u1, "user2": u2}
    return r


def _duel_factory_for(results: dict):
    """Returns a duel engine factory that returns preset results."""
    def factory(u1, u2, limit, token, timeout):
        engine = MagicMock()
        key = (u1, u2)
        if key in results:
            engine.run.return_value = results[key]
        else:
            engine.run.return_value = _make_duel_result(u1, u2, "user1", False, 70.0, 50.0)
        return engine
    return factory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_tournament_requires_at_least_two():
    engine = UserTournamentEngine()
    with pytest.raises(ValueError):
        engine.run(["alice"])


def test_tournament_two_users_round_robin():
    dr = _make_duel_result("alice", "bob", "user1")
    factory = _duel_factory_for({("alice", "bob"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob"])
    assert isinstance(result, TournamentResult)
    assert result.champion == "alice"
    assert result.mode == "round-robin"
    assert len(result.standings) == 2
    assert result.standings[0].handle == "alice"
    assert result.standings[0].wins == 1
    assert result.standings[1].handle == "bob"
    assert result.standings[1].losses == 1


def test_tournament_three_users():
    results = {
        ("alice", "bob"): _make_duel_result("alice", "bob", "user1"),
        ("alice", "carol"): _make_duel_result("alice", "carol", "user1"),
        ("bob", "carol"): _make_duel_result("bob", "carol", "user1"),
    }
    factory = _duel_factory_for(results)
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob", "carol"])
    assert result.champion == "alice"
    assert result.standings[0].wins == 2
    assert result.rounds == 3


def test_standings_rank_assigned():
    results = {
        ("a", "b"): _make_duel_result("a", "b", "user1"),
        ("a", "c"): _make_duel_result("a", "c", "user1"),
        ("b", "c"): _make_duel_result("b", "c", "user2"),
    }
    factory = _duel_factory_for(results)
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["a", "b", "c"])
    ranks = [s.rank for s in result.standings]
    assert ranks == [1, 2, 3]


def test_tournament_tie_no_wins():
    dr = _make_duel_result("alice", "bob", "tie", tied=True, s1=70.0, s2=70.0)
    factory = _duel_factory_for({("alice", "bob"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob"])
    # Both 0 wins — champion is first alphabetically after sort (avg_score tiebreak)
    assert result.standings[0].wins == 0
    assert result.standings[1].wins == 0


def test_max_comparisons_limits_matchups():
    calls = []
    def factory(u1, u2, limit, token, timeout):
        calls.append((u1, u2))
        engine = MagicMock()
        engine.run.return_value = _make_duel_result(u1, u2, "user1")
        return engine

    engine = UserTournamentEngine(_duel_engine_factory=factory, max_comparisons=2)
    engine.run(["a", "b", "c", "d"])
    assert len(calls) == 2


def test_tournament_result_to_dict():
    dr = _make_duel_result("alice", "bob", "user1")
    factory = _duel_factory_for({("alice", "bob"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob"])
    d = result.to_dict()
    assert "participants" in d
    assert "standings" in d
    assert "match_results" in d
    assert "champion" in d
    assert "rounds" in d
    assert "timestamp" in d


def test_standings_to_dict():
    s = Standings(rank=1, handle="alice", wins=3, losses=0, avg_score=85.0, total_duel_score=255.0, grade="A")
    d = s.to_dict()
    assert d["rank"] == 1
    assert d["handle"] == "alice"
    assert d["wins"] == 3
    assert d["losses"] == 0
    assert d["grade"] == "A"
    assert d["record"] == "3-0"


def test_standings_record():
    s = Standings(rank=2, handle="bob", wins=2, losses=1, avg_score=70.0, total_duel_score=210.0, grade="B")
    assert s.record() == "2-1"


def test_tournament_graceful_skip_on_error():
    """If a duel raises, both users are skipped — no crash."""
    def factory(u1, u2, limit, token, timeout):
        engine = MagicMock()
        engine.run.side_effect = RuntimeError("API error")
        return engine

    engine = UserTournamentEngine(_duel_engine_factory=factory)
    # Should not raise
    result = engine.run(["alice", "bob"])
    assert result.champion  # still has a champion
    assert result.rounds >= 0


def test_tournament_many_users_bracket_mode():
    def factory(u1, u2, limit, token, timeout):
        engine = MagicMock()
        engine.run.return_value = _make_duel_result(u1, u2, "user1")
        return engine

    participants = [f"user{i}" for i in range(9)]
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(participants)
    assert result.mode == "bracket"


def test_tournament_few_users_round_robin_mode():
    def factory(u1, u2, limit, token, timeout):
        engine = MagicMock()
        engine.run.return_value = _make_duel_result(u1, u2, "user1")
        return engine

    participants = ["a", "b", "c"]
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(participants)
    assert result.mode == "round-robin"


def test_champion_tiebreak_by_avg_score():
    """When wins are tied, higher avg_score wins."""
    results = {
        ("alice", "bob"): _make_duel_result("alice", "bob", "tie", tied=True, s1=90.0, s2=50.0),
    }
    factory = _duel_factory_for(results)
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob"])
    # alice has higher avg_score so should be ranked first
    assert result.standings[0].handle == "alice"


def test_tournament_timestamp_set():
    dr = _make_duel_result("a", "b", "user1")
    factory = _duel_factory_for({("a", "b"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["a", "b"])
    assert result.timestamp != ""
    assert "UTC" in result.timestamp


def test_tournament_participants_preserved():
    dr = _make_duel_result("a", "b", "user1")
    factory = _duel_factory_for({("a", "b"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["a", "b"])
    assert result.participants == ["a", "b"]


def test_grade_assigned_in_standings():
    dr = _make_duel_result("alice", "bob", "user1", s1=85.0, s2=55.0)
    factory = _duel_factory_for({("alice", "bob"): dr})
    engine = UserTournamentEngine(_duel_engine_factory=factory)
    result = engine.run(["alice", "bob"])
    alice_standing = next(s for s in result.standings if s.handle == "alice")
    assert alice_standing.grade == "A"

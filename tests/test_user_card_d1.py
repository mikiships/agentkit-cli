"""Tests for D1: UserCardEngine core (≥14 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.user_card import UserCardEngine, UserCardResult, AGENT_READY_THRESHOLD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scorecard(username="alice", avg_score=72.0, grade="B", top_repos=None, all_repos=None, total_repos=10, analyzed_repos=8, context_pct=60.0):
    sc = MagicMock()
    sc.username = username
    sc.avg_score = avg_score
    sc.grade = grade
    sc.total_repos = total_repos
    sc.analyzed_repos = analyzed_repos
    sc.context_coverage_pct = context_pct

    if top_repos is None:
        r = MagicMock()
        r.name = "top-repo"
        r.score = 90.0
        top_repos = [r]
    sc.top_repos = top_repos

    if all_repos is None:
        repos = []
        for i in range(analyzed_repos):
            r = MagicMock()
            r.score = 85.0 if i < 3 else 60.0
            repos.append(r)
        all_repos = repos
    sc.all_repos = all_repos

    return sc


def _make_engine_that_returns(scorecard):
    class _MockEngine:
        def __init__(self, *a, **kw):
            pass
        def run(self, progress_callback=None):
            return scorecard
    return _MockEngine


# ---------------------------------------------------------------------------
# UserCardResult
# ---------------------------------------------------------------------------

def test_user_card_result_to_dict_fields():
    r = UserCardResult(
        username="alice",
        avatar_url="https://github.com/alice.png",
        grade="B",
        avg_score=72.0,
        total_repos=10,
        analyzed_repos=8,
        context_coverage_pct=60.0,
        top_repo_name="best-repo",
        top_repo_score=90.0,
        agent_ready_count=3,
        summary_line="3/8 repos agent-ready · Grade B",
    )
    d = r.to_dict()
    assert d["username"] == "alice"
    assert d["grade"] == "B"
    assert d["avg_score"] == 72.0
    assert d["top_repo_name"] == "best-repo"
    assert d["top_repo_score"] == 90.0
    assert d["agent_ready_count"] == 3
    assert d["summary_line"] == "3/8 repos agent-ready · Grade B"
    assert d["context_coverage_pct"] == 60.0
    assert d["total_repos"] == 10
    assert d["analyzed_repos"] == 8


def test_user_card_result_to_dict_has_error_field():
    r = UserCardResult(
        username="alice", avatar_url="", grade="D", avg_score=0.0,
        total_repos=0, analyzed_repos=0, context_coverage_pct=0.0,
        top_repo_name="", top_repo_score=0.0, agent_ready_count=0,
        summary_line="0/0 repos agent-ready · Grade D", error="some error"
    )
    d = r.to_dict()
    assert d["error"] == "some error"


def test_user_card_result_error_none_by_default():
    r = UserCardResult(
        username="bob", avatar_url="", grade="A", avg_score=85.0,
        total_repos=5, analyzed_repos=5, context_coverage_pct=80.0,
        top_repo_name="r", top_repo_score=95.0, agent_ready_count=4,
        summary_line="4/5 repos agent-ready · Grade A",
    )
    assert r.error is None


# ---------------------------------------------------------------------------
# UserCardEngine construction
# ---------------------------------------------------------------------------

def test_engine_defaults():
    e = UserCardEngine()
    assert e.limit == 10
    assert e.min_stars == 0
    assert e.skip_forks is True
    assert e.timeout == 60


def test_engine_limit_clamped_to_30():
    e = UserCardEngine(limit=999)
    assert e.limit == 30


def test_engine_limit_minimum_1():
    e = UserCardEngine(limit=0)
    assert e.limit == 1


# ---------------------------------------------------------------------------
# UserCardEngine.run
# ---------------------------------------------------------------------------

def test_run_strips_github_prefix():
    sc = _make_scorecard(username="alice")
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("github:alice")
    assert result.username == "alice"


def test_run_empty_username_returns_error():
    e = UserCardEngine()
    result = e.run("")
    assert result.error is not None
    assert result.grade == "D"


def test_run_sets_avatar_url():
    sc = _make_scorecard(username="alice")
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("alice")
    assert result.avatar_url == "https://github.com/alice.png"


def test_run_computes_agent_ready_count():
    sc = _make_scorecard(username="alice")
    # 3 repos with score 85 (>=80), 5 with 60 (<80)
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("alice")
    assert result.agent_ready_count == 3


def test_run_top_repo_populated():
    sc = _make_scorecard(username="alice")
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("alice")
    assert result.top_repo_name == "top-repo"
    assert result.top_repo_score == 90.0


def test_run_summary_line_format():
    sc = _make_scorecard(username="alice")
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("alice")
    assert "agent-ready" in result.summary_line
    assert "Grade" in result.summary_line


def test_run_engine_exception_returns_error_card():
    def _bad_init(*a, **kw):
        raise RuntimeError("API error")
    with patch("agentkit_cli.user_card.UserScorecardEngine", _bad_init):
        e = UserCardEngine()
        result = e.run("alice")
    assert result.error is not None
    assert result.grade == "D"
    assert result.avg_score == 0.0


def test_run_no_top_repos():
    sc = _make_scorecard(username="alice", top_repos=[], all_repos=[])
    with patch("agentkit_cli.user_card.UserScorecardEngine", _make_engine_that_returns(sc)):
        e = UserCardEngine()
        result = e.run("alice")
    assert result.top_repo_name == ""
    assert result.top_repo_score == 0.0
    assert result.agent_ready_count == 0


def test_agent_ready_threshold_value():
    assert AGENT_READY_THRESHOLD == 80.0

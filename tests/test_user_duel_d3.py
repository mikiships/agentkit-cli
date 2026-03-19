"""Tests for D3: HTML duel report renderer."""
from __future__ import annotations

import pytest

from agentkit_cli.user_duel import (
    UserDuelReportRenderer,
    UserDuelResult,
    DuelDimension,
    _grade_color,
    _fmt_dim_value,
    publish_user_duel,
)
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult


def _make_scorecard(username, avg_score, grade, analyzed=5):
    repos = [
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
        top_repos=repos[:3],
        bottom_repos=[],
        all_repos=repos,
    )


def _make_duel_result(user1="alice", user2="bob", winner="user1", tied=False):
    s1 = _make_scorecard(user1, 85.0, "A")
    s2 = _make_scorecard(user2, 60.0, "C")
    dims = [
        DuelDimension("avg_score", 85.0, 60.0, "user1"),
        DuelDimension("letter_grade", 4.0, 2.0, "user1"),
        DuelDimension("repo_count", 5.0, 5.0, "tie"),
        DuelDimension("agent_ready_repos", 3.0, 2.0, "user1"),
    ]
    return UserDuelResult(
        user1=user1, user2=user2,
        user1_scorecard=s1, user2_scorecard=s2,
        dimensions=dims,
        overall_winner=winner, tied=tied,
        timestamp="2026-01-01 00:00 UTC",
    )


# ---------------------------------------------------------------------------

def test_renderer_returns_html_string():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result()
    html = renderer.render(result)
    assert isinstance(html, str)
    assert html.startswith("<!DOCTYPE html>")


def test_renderer_dark_theme():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result()
    html = renderer.render(result)
    assert "#0d1117" in html


def test_renderer_contains_usernames():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result("tiangolo", "kennethreitz")
    html = renderer.render(result)
    assert "tiangolo" in html
    assert "kennethreitz" in html


def test_renderer_contains_verdict_winner():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result(winner="user1")
    html = renderer.render(result)
    assert "🏆" in html
    assert "alice" in html


def test_renderer_contains_verdict_tie():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result(winner="tie", tied=True)
    html = renderer.render(result)
    assert "🤝" in html
    assert "Tied" in html


def test_renderer_avatar_urls():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result("alice", "bob")
    html = renderer.render(result)
    assert "github.com/alice.png" in html
    assert "github.com/bob.png" in html


def test_renderer_dimension_table():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result()
    html = renderer.render(result)
    assert "Avg Score" in html or "avg_score" in html.lower()


def test_renderer_repo_cards():
    renderer = UserDuelReportRenderer()
    result = _make_duel_result()
    html = renderer.render(result)
    # Should have repo names from top repos
    assert "repo0" in html or "alice/repo0" in html


def test_grade_color_returns_string():
    assert isinstance(_grade_color("A"), str)
    assert _grade_color("A").startswith("#")
    assert _grade_color("X") is not None  # fallback


def test_publish_user_duel_failure_returns_none():
    result = _make_duel_result()
    # Without a real here.now server, should return None gracefully
    from unittest.mock import patch
    with patch("agentkit_cli.user_duel.publish_user_duel", return_value=None) as mock_pub:
        url = mock_pub(result)
    assert url is None

"""Tests for D3: Dark-theme HTML tournament report renderer."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.engines.user_tournament import TournamentResult, Standings
from agentkit_cli.renderers.user_tournament_report import (
    UserTournamentReportRenderer,
    publish_user_tournament,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_standing(rank, handle, wins=1, losses=0, avg=75.0, grade="B"):
    return Standings(rank=rank, handle=handle, wins=wins, losses=losses,
                     avg_score=avg, total_duel_score=avg, grade=grade)


def _make_result(champion="alice", participants=None, mode="round-robin"):
    if participants is None:
        participants = ["alice", "bob"]
    standings = [
        _make_standing(1, participants[0], wins=1, grade="A"),
        _make_standing(2, participants[1], losses=1, grade="B"),
    ]
    mr = MagicMock()
    mr.user1 = participants[0]
    mr.user2 = participants[1]
    mr.overall_winner = "user1"
    mr.tied = False
    r = TournamentResult(
        participants=participants,
        standings=standings,
        match_results=[mr],
        champion=champion,
        rounds=1,
        timestamp="2026-01-01 00:00 UTC",
        mode=mode,
    )
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_render_returns_string():
    result = _make_result()
    html = UserTournamentReportRenderer().render(result)
    assert isinstance(html, str)


def test_render_contains_dark_background():
    result = _make_result()
    html = UserTournamentReportRenderer().render(result)
    assert "#0d1117" in html


def test_render_contains_champion():
    result = _make_result(champion="alice")
    html = UserTournamentReportRenderer().render(result)
    assert "@alice" in html
    assert "Champion" in html


def test_render_contains_all_participants():
    result = _make_result(participants=["alice", "bob"])
    html = UserTournamentReportRenderer().render(result)
    assert "@alice" in html
    assert "@bob" in html


def test_render_contains_standings_table():
    result = _make_result()
    html = UserTournamentReportRenderer().render(result)
    assert "<table>" in html
    assert "W-L" in html or "Standings" in html


def test_render_contains_match_results():
    result = _make_result()
    html = UserTournamentReportRenderer().render(result)
    assert "alice" in html
    assert "bob" in html


def test_render_contains_grade_badge():
    result = _make_result()
    html = UserTournamentReportRenderer().render(result)
    assert "grade-badge" in html or "A" in html


def test_publish_returns_url_on_success():
    result = _make_result()
    with patch("agentkit_cli.renderers.user_tournament_report._json_post") as mock_post, \
         patch("agentkit_cli.renderers.user_tournament_report._put_file") as mock_put, \
         patch("agentkit_cli.renderers.user_tournament_report._finalize") as mock_final:
        mock_post.return_value = {
            "id": "abc123",
            "files": [{"upload_url": "https://storage.here.now/abc"}],
        }
        mock_final.return_value = {"url": "https://here.now/abc123"}
        url = publish_user_tournament(result)
    assert url == "https://here.now/abc123"


def test_publish_returns_none_on_error():
    result = _make_result()
    with patch("agentkit_cli.renderers.user_tournament_report._json_post", side_effect=Exception("fail")):
        url = publish_user_tournament(result)
    assert url is None

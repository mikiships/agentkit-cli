"""Tests for D2: agentkit user-tournament CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.user_tournament import TournamentResult, Standings
from agentkit_cli.commands.user_tournament_cmd import user_tournament_command


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_standing(rank, handle, wins=1, losses=0, avg=75.0, grade="B"):
    return Standings(rank=rank, handle=handle, wins=wins, losses=losses,
                     avg_score=avg, total_duel_score=avg, grade=grade)


def _make_result(champion="alice", participants=None):
    if participants is None:
        participants = ["alice", "bob"]
    standings = [
        _make_standing(1, participants[0], wins=1),
        _make_standing(2, participants[1], losses=1),
    ]
    mr = MagicMock()
    mr.to_dict.return_value = {}
    r = TournamentResult(
        participants=participants,
        standings=standings,
        match_results=[mr],
        champion=champion,
        rounds=1,
        timestamp="2026-01-01 00:00 UTC",
        mode="round-robin",
    )
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_help_shows_flags():
    result = runner.invoke(app, ["user-tournament", "--help"])
    assert result.exit_code == 0
    assert "--share" in result.output
    assert "--json" in result.output
    assert "--quiet" in result.output
    assert "--output" in result.output
    assert "--limit" in result.output
    assert "--timeout" in result.output


def test_fewer_than_two_participants_exits_1():
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.side_effect = ValueError("need 2")
        result = runner.invoke(app, ["user-tournament", "github:alice"])
    assert result.exit_code == 1


def test_json_output():
    mock_result = _make_result()
    def factory(u1, u2, limit, token, timeout):
        engine = MagicMock()
        from agentkit_cli.user_duel import UserDuelResult
        dr = MagicMock(spec=UserDuelResult)
        dr.user1 = u1
        dr.user2 = u2
        dr.overall_winner = "user1"
        dr.tied = False
        sc1 = MagicMock()
        sc1.avg_score = 80.0
        sc2 = MagicMock()
        sc2.avg_score = 60.0
        dr.user1_scorecard = sc1
        dr.user2_scorecard = sc2
        dr.to_dict.return_value = {}
        engine.run.return_value = dr
        return engine

    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-tournament", "alice", "bob", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "champion" in data


def test_quiet_output():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-tournament", "alice", "bob", "--quiet"])
    assert result.exit_code == 0
    assert "champion:" in result.output
    assert "alice" in result.output


def test_github_prefix_stripped():
    mock_result = _make_result()
    captured = {}
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        def capture_run(participants, progress_callback=None):
            captured["participants"] = participants
            return mock_result
        mock_cls.return_value.run.side_effect = capture_run
        runner.invoke(app, ["user-tournament", "github:alice", "github:bob"])
    assert captured.get("participants") == ["alice", "bob"]


def test_output_flag_writes_file(tmp_path):
    html_file = tmp_path / "out.html"
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls, \
         patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentReportRenderer") as mock_renderer:
        mock_cls.return_value.run.return_value = mock_result
        mock_renderer.return_value.render.return_value = "<html>test</html>"
        result = runner.invoke(app, ["user-tournament", "alice", "bob", "--output", str(html_file)])
    assert result.exit_code == 0
    assert html_file.exists()
    assert "<html>" in html_file.read_text()


def test_share_flag_calls_publish():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls, \
         patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentReportRenderer") as mock_renderer, \
         patch("agentkit_cli.commands.user_tournament_cmd.publish_user_tournament") as mock_pub:
        mock_cls.return_value.run.return_value = mock_result
        mock_renderer.return_value.render.return_value = "<html></html>"
        mock_pub.return_value = "https://here.now/abc"
        result = runner.invoke(app, ["user-tournament", "alice", "bob", "--share"])
    assert result.exit_code == 0
    mock_pub.assert_called_once()


def test_limit_flag_passed_to_engine():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        runner.invoke(app, ["user-tournament", "alice", "bob", "--limit", "5"])
    call_kwargs = mock_cls.call_args
    assert call_kwargs is not None


def test_exit_0_on_success():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-tournament", "alice", "bob"])
    assert result.exit_code == 0


def test_standings_table_shown():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-tournament", "alice", "bob"])
    assert "alice" in result.output
    assert "Champion" in result.output


def test_json_with_share_url():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentEngine") as mock_cls, \
         patch("agentkit_cli.commands.user_tournament_cmd.UserTournamentReportRenderer") as mock_renderer, \
         patch("agentkit_cli.commands.user_tournament_cmd.publish_user_tournament") as mock_pub:
        mock_cls.return_value.run.return_value = mock_result
        mock_renderer.return_value.render.return_value = "<html></html>"
        mock_pub.return_value = "https://here.now/xyz"
        result = runner.invoke(app, ["user-tournament", "alice", "bob", "--json", "--share"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data.get("share_url") == "https://here.now/xyz"

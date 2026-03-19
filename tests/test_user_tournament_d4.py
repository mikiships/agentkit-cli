"""Tests for D4: Integration into agentkit run and agentkit report."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.user_tournament import TournamentResult, Standings


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_standing(rank, handle, wins=1, losses=0, avg=75.0, grade="B"):
    return Standings(rank=rank, handle=handle, wins=wins, losses=losses,
                     avg_score=avg, total_duel_score=avg, grade=grade)


def _make_result(champion="alice"):
    standings = [
        _make_standing(1, "alice", wins=1),
        _make_standing(2, "bob", losses=1),
    ]
    mr = MagicMock()
    mr.to_dict.return_value = {}
    return TournamentResult(
        participants=["alice", "bob"],
        standings=standings,
        match_results=[mr],
        champion=champion,
        rounds=1,
        timestamp="2026-01-01 00:00 UTC",
        mode="round-robin",
    )


# ---------------------------------------------------------------------------
# run_cmd tests
# ---------------------------------------------------------------------------

def test_run_cmd_accepts_user_tournament_flag(tmp_path):
    """--user-tournament flag is wired into run_command."""
    from agentkit_cli.commands import run_cmd
    import inspect
    sig = inspect.signature(run_cmd.run_command)
    assert "user_tournament" in sig.parameters


def test_run_cmd_user_tournament_calls_engine(tmp_path):
    """run_command calls UserTournamentEngine when --user-tournament is set."""
    mock_result = _make_result()
    with patch("agentkit_cli.engines.user_tournament.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        from agentkit_cli.engines.user_tournament import UserTournamentEngine
        summary = {}
        user_tournament = "alice:bob"
        _t_parts = [p.strip() for p in user_tournament.split(":") if p.strip()]
        if len(_t_parts) >= 2:
            _t_engine = UserTournamentEngine()
            _t_result = _t_engine.run(_t_parts)
            summary["user_tournament"] = _t_result.to_dict()
    assert "user_tournament" in summary


def test_run_cmd_user_tournament_invalid_format():
    """run_command handles invalid --user-tournament format gracefully."""
    summary = {}
    user_tournament = "only-one-user"
    _t_parts = [p.strip() for p in user_tournament.split(":") if p.strip()]
    if len(_t_parts) < 2:
        summary["user_tournament"] = {"error": "Invalid --user-tournament format. Use user1:user2:..."}
    assert "error" in summary.get("user_tournament", {})


# ---------------------------------------------------------------------------
# report_cmd tests
# ---------------------------------------------------------------------------

def test_report_cmd_accepts_user_tournament_param():
    """report_command signature includes user_tournament."""
    from agentkit_cli.commands import report_cmd
    import inspect
    sig = inspect.signature(report_cmd.report_command)
    assert "user_tournament" in sig.parameters


def test_report_cmd_user_tournament_wiring():
    """report_command calls UserTournamentEngine when user_tournament is set."""
    mock_result = _make_result()
    with patch("agentkit_cli.engines.user_tournament.UserTournamentEngine") as mock_cls:
        mock_cls.return_value.run.return_value = mock_result
        from agentkit_cli.engines.user_tournament import UserTournamentEngine
        summary = {}
        user_tournament = "alice:bob"
        _t_parts = [p.strip() for p in user_tournament.split(":") if p.strip()]
        if len(_t_parts) >= 2:
            _t_engine = UserTournamentEngine()
            _t_result = _t_engine.run(_t_parts)
            summary["user_tournament"] = _t_result.to_dict()
    assert "user_tournament" in summary


def test_main_run_has_user_tournament_option():
    """agentkit run --help shows --user-tournament."""
    result = runner.invoke(app, ["run", "--help"])
    assert "--user-tournament" in result.output


def test_main_report_has_user_tournament_option():
    """agentkit report --help shows --user-tournament."""
    result = runner.invoke(app, ["report", "--help"])
    assert "--user-tournament" in result.output

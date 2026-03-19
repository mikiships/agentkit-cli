"""Tests for D2: user-duel CLI command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_duel import UserDuelResult, DuelDimension
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult


runner = CliRunner()


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
        user1=user1,
        user2=user2,
        user1_scorecard=s1,
        user2_scorecard=s2,
        dimensions=dims,
        overall_winner=winner,
        tied=tied,
        timestamp="2026-01-01 00:00 UTC",
    )


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_user_duel_basic(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "github:alice", "github:bob"])
    assert result.exit_code == 0
    assert "alice" in result.output or "Duel" in result.output


def test_user_duel_json_output(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "github:alice", "github:bob", "--json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["user1"] == "alice"
    assert data["user2"] == "bob"
    assert "overall_winner" in data


def test_user_duel_quiet_winner(monkeypatch):
    mock_result = _make_duel_result(winner="user1")
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "github:alice", "github:bob", "--quiet"])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_user_duel_quiet_user2_wins(monkeypatch):
    mock_result = _make_duel_result(winner="user2")
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "github:alice", "github:bob", "--quiet"])
    assert result.exit_code == 0
    assert "bob" in result.output


def test_user_duel_quiet_tie(monkeypatch):
    mock_result = _make_duel_result(winner="tie", tied=True)
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "github:alice", "github:bob", "--quiet"])
    assert result.exit_code == 0
    assert "tied" in result.output.lower() or "tie" in result.output.lower()


def test_user_duel_bare_usernames(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "alice", "bob"])
    assert result.exit_code == 0


def test_user_duel_limit_flag(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "alice", "bob", "--limit", "3"])
    assert result.exit_code == 0
    # Check limit was passed
    call_kwargs = MockEngine.call_args
    assert call_kwargs is not None
    assert call_kwargs[1].get("limit") == 3 or (call_kwargs[0] and call_kwargs[0][0] == 3)


def test_user_duel_json_dimensions(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "alice", "bob", "--json"])
    import json
    data = json.loads(result.output)
    assert "dimensions" in data
    assert len(data["dimensions"]) == 4


def test_user_duel_error_handling(monkeypatch):
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.side_effect = ValueError("GitHub user 'notexist' not found")
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "notexist", "bob"])
    assert result.exit_code != 0


def test_user_duel_json_error_handling(monkeypatch):
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.side_effect = ValueError("GitHub user 'notexist' not found")
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "notexist", "bob", "--json"])
    import json
    data = json.loads(result.output)
    assert "error" in data


def test_user_duel_verdict_banner_in_output(monkeypatch):
    mock_result = _make_duel_result(winner="user1")
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        result = runner.invoke(app, ["user-duel", "alice", "bob"])
    assert result.exit_code == 0
    # Should show winner
    assert "alice" in result.output or "wins" in result.output


def test_user_duel_share_url_in_json(monkeypatch):
    mock_result = _make_duel_result()
    with patch("agentkit_cli.commands.user_duel_cmd.UserDuelEngine") as MockEngine:
        instance = MagicMock()
        instance.run.return_value = mock_result
        MockEngine.return_value = instance
        with patch("agentkit_cli.commands.user_duel_cmd.publish_user_duel", return_value="https://here.now/abc"):
            result = runner.invoke(app, ["user-duel", "alice", "bob", "--share", "--json"])
    import json
    data = json.loads(result.output)
    assert data.get("share_url") == "https://here.now/abc"

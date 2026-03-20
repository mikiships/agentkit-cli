"""Tests for D2: agentkit user-team CLI command."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_team import TeamScorecardResult
from agentkit_cli.user_scorecard import UserScorecardResult, score_to_grade

runner = CliRunner()


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


def _make_team_result(org: str = "testorg") -> TeamScorecardResult:
    results = [_make_user_result("alice", 80.0), _make_user_result("bob", 60.0)]
    return TeamScorecardResult(
        org=org,
        contributor_results=results,
        aggregate_score=70.0,
        aggregate_grade="B",
        top_scorer="alice",
        contributor_count=2,
        timestamp="2026-03-20 00:00 UTC",
    )


def _mock_engine(result=None):
    if result is None:
        result = _make_team_result()
    mock = MagicMock()
    mock.return_value.run.return_value = result
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_command_registered():
    result = runner.invoke(app, ["user-team", "--help"])
    assert result.exit_code == 0


def test_help_text_present():
    result = runner.invoke(app, ["user-team", "--help"])
    assert "org" in result.output.lower() or "agent" in result.output.lower()


def test_github_prefix_parsing():
    """github: prefix should be parsed correctly."""
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "github:pallets"])
    assert result.exit_code == 0


def test_bare_org_parsing():
    """Bare org name (no github: prefix) should also work."""
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "pallets"])
    assert result.exit_code == 0


def test_limit_flag_passed_to_engine():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        runner.invoke(app, ["user-team", "github:testorg", "--limit", "5"])
    call_kwargs = mock_cls.call_args
    assert call_kwargs is not None
    # limit=5 should be passed
    assert mock_cls.call_args.kwargs.get("limit") == 5 or (
        len(mock_cls.call_args.args) > 1 and mock_cls.call_args.args[1] == 5
    )


def test_json_output_is_valid():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "github:testorg", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert "org" in parsed
    assert "aggregate_score" in parsed


def test_quiet_suppresses_progress():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "github:testorg", "--quiet"])
    assert result.exit_code == 0
    # No "agentkit user-team" header in quiet mode
    assert "agentkit user-team" not in result.output


def test_output_writes_html_file():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = runner.invoke(app, ["user-team", "github:testorg", "--output", path])
            assert result.exit_code == 0
            with open(path) as fh:
                content = fh.read()
            assert "<!DOCTYPE html>" in content
            assert "testorg" in content
        finally:
            os.unlink(path)


def test_rich_table_rendered():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "github:testorg"])
    assert result.exit_code == 0
    # Should contain usernames in output
    assert "alice" in result.output or "testorg" in result.output


def test_missing_github_token_graceful_warning(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.return_value = _make_team_result()
        result = runner.invoke(app, ["user-team", "github:testorg"])
    # Should not crash (exit code 0)
    assert result.exit_code == 0


def test_invalid_org_format_shows_error():
    with patch("agentkit_cli.commands.user_team_cmd.TeamScorecardEngine") as mock_cls:
        mock_cls.return_value.run.side_effect = ValueError("Org 'github:' not found")
        result = runner.invoke(app, ["user-team", "github:"])
    # Empty org name error
    assert result.exit_code != 0 or "error" in result.output.lower() or "required" in result.output.lower()

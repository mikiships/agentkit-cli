"""Tests for D4: --badge flag on user-scorecard and user-card (≥8 tests)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _mock_scorecard(username="alice", avg_score=78.0, grade="B"):
    sc = MagicMock()
    sc.username = username
    sc.avg_score = avg_score
    sc.grade = grade
    sc.total_repos = 10
    sc.analyzed_repos = 8
    sc.skipped_repos = 2
    sc.context_coverage_pct = 60.0
    sc.top_repos = []
    sc.bottom_repos = []
    sc.all_repos = []
    sc.to_dict.return_value = {
        "username": username,
        "avg_score": avg_score,
        "grade": grade,
        "total_repos": 10,
        "analyzed_repos": 8,
        "skipped_repos": 2,
        "context_coverage_pct": 60.0,
        "top_repos": [],
        "bottom_repos": [],
        "all_repos": [],
    }
    return sc


def _mock_card_result(username="alice", avg_score=78.0, grade="B"):
    r = MagicMock()
    r.username = username
    r.avg_score = avg_score
    r.grade = grade
    r.error = None
    r.context_coverage_pct = 60.0
    r.total_repos = 10
    r.analyzed_repos = 8
    r.agent_ready_count = 3
    r.top_repo_name = "top-repo"
    r.top_repo_score = 90.0
    r.summary_line = "3/8 repos agent-ready · Grade B"
    r.to_dict.return_value = {
        "username": username,
        "avg_score": avg_score,
        "grade": grade,
        "error": None,
        "context_coverage_pct": 60.0,
        "total_repos": 10,
        "analyzed_repos": 8,
        "agent_ready_count": 3,
        "top_repo_name": "top-repo",
        "top_repo_score": 90.0,
        "summary_line": "3/8 repos agent-ready · Grade B",
        "avatar_url": "",
    }
    return r


# ---------------------------------------------------------------------------
# user-scorecard --badge
# ---------------------------------------------------------------------------

def test_user_scorecard_badge_flag_prints_badge():
    sc = _mock_scorecard()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEng:
        MockEng.return_value.run.return_value = sc
        with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardReportRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            result = runner.invoke(app, ["user-scorecard", "github:alice", "--badge"])
    assert result.exit_code == 0
    assert "img.shields.io" in result.output


def test_user_scorecard_badge_json_has_badge_url():
    sc = _mock_scorecard()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEng:
        MockEng.return_value.run.return_value = sc
        with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardReportRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            result = runner.invoke(app, ["user-scorecard", "github:alice", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "badge_url" in data


def test_user_scorecard_without_badge_no_shields():
    sc = _mock_scorecard()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEng:
        MockEng.return_value.run.return_value = sc
        with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardReportRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            result = runner.invoke(app, ["user-scorecard", "github:alice"])
    assert result.exit_code == 0
    # Without --badge, no shields URL in terminal output
    assert "img.shields.io" not in result.output


# ---------------------------------------------------------------------------
# user-card --badge
# ---------------------------------------------------------------------------

def test_user_card_badge_flag_prints_badge():
    card = _mock_card_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine") as MockEng:
        MockEng.return_value.run.return_value = card
        with patch("agentkit_cli.commands.user_card_cmd.UserCardHTMLRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                result = runner.invoke(app, ["user-card", "github:alice", "--badge"])
    assert result.exit_code == 0
    assert "img.shields.io" in result.output


def test_user_card_badge_json_has_badge_url():
    card = _mock_card_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine") as MockEng:
        MockEng.return_value.run.return_value = card
        with patch("agentkit_cli.commands.user_card_cmd.UserCardHTMLRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                result = runner.invoke(app, ["user-card", "github:alice", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "badge_url" in data


def test_user_card_without_badge_no_shields():
    card = _mock_card_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine") as MockEng:
        MockEng.return_value.run.return_value = card
        with patch("agentkit_cli.commands.user_card_cmd.UserCardHTMLRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                result = runner.invoke(app, ["user-card", "github:alice"])
    assert result.exit_code == 0
    assert "img.shields.io" not in result.output


def test_user_card_badge_contains_grade():
    card = _mock_card_result(grade="A", avg_score=92.0)
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine") as MockEng:
        MockEng.return_value.run.return_value = card
        with patch("agentkit_cli.commands.user_card_cmd.UserCardHTMLRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                result = runner.invoke(app, ["user-card", "github:alice", "--badge"])
    assert "A" in result.output


def test_user_scorecard_badge_contains_grade():
    sc = _mock_scorecard(grade="A", avg_score=92.0)
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEng:
        MockEng.return_value.run.return_value = sc
        with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardReportRenderer") as MockRend:
            MockRend.return_value.render.return_value = "<html/>"
            result = runner.invoke(app, ["user-scorecard", "github:alice", "--badge"])
    assert "A" in result.output

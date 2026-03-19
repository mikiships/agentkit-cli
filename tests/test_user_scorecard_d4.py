"""Tests for D4: --share and --pages wiring."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult

runner = CliRunner()


def _make_result(username="alice"):
    repos = [RepoResult("repo-0", f"{username}/repo-0", 80.0, "A", True, stars=5)]
    return UserScorecardResult(
        username=username,
        total_repos=1,
        analyzed_repos=1,
        skipped_repos=0,
        avg_score=80.0,
        grade="A",
        context_coverage_pct=100.0,
        top_repos=repos,
        bottom_repos=[],
        all_repos=repos,
    )


def _make_engine_cls(result):
    class _MockEngine:
        def __init__(self, *a, **kw): pass
        def run(self, progress_callback=None): return result
    return _MockEngine


# ---------------------------------------------------------------------------
# --share
# ---------------------------------------------------------------------------

def test_share_upload_called():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/abc") as mock_up:
        out = runner.invoke(app, ["user-scorecard", "alice", "--share"])
    assert out.exit_code == 0
    assert mock_up.called


def test_share_url_printed():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/abc"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--share"])
    assert "here.now/abc" in out.stdout


def test_share_upload_failure_continues():
    """If upload fails (returns None), command should not crash."""
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value=None):
        out = runner.invoke(app, ["user-scorecard", "alice", "--share"])
    assert out.exit_code == 0


def test_share_url_in_json_output():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/xyz"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--share", "--json"])
    data = json.loads(out.stdout)
    assert data["share_url"] == "https://here.now/xyz"


# ---------------------------------------------------------------------------
# --pages
# ---------------------------------------------------------------------------

def test_pages_push_called():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd._push_to_pages", return_value="https://alice.github.io/pages/") as mock_pages:
        out = runner.invoke(app, ["user-scorecard", "alice", "--pages", "github:alice/pages"])
    assert out.exit_code == 0
    assert mock_pages.called


def test_pages_url_in_json():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd._push_to_pages", return_value="https://alice.github.io/pages/"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--pages", "github:alice/pages", "--json"])
    data = json.loads(out.stdout)
    assert "pages_url" in data


def test_pages_push_failure_handled():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd._push_to_pages", return_value=None):
        out = runner.invoke(app, ["user-scorecard", "alice", "--pages", "github:alice/pages"])
    assert out.exit_code == 0


def test_share_and_pages_together():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/abc"), \
         patch("agentkit_cli.commands.user_scorecard_cmd._push_to_pages", return_value="https://alice.github.io/p/"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--share", "--pages", "github:alice/p", "--json"])
    data = json.loads(out.stdout)
    assert data["share_url"] == "https://here.now/abc"
    assert data["pages_url"] == "https://alice.github.io/p/"

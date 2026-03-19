"""Tests for D2: user-scorecard CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult

runner = CliRunner()


def _make_result(username="alice", grade="B", avg_score=72.0):
    repos = [
        RepoResult("repo-0", f"{username}/repo-0", 90.0, "A", True, stars=10),
        RepoResult("repo-1", f"{username}/repo-1", 70.0, "B", False, stars=5),
        RepoResult("repo-2", f"{username}/repo-2", 56.0, "C", True, stars=2),
    ]
    return UserScorecardResult(
        username=username,
        total_repos=3,
        analyzed_repos=3,
        skipped_repos=0,
        avg_score=avg_score,
        grade=grade,
        context_coverage_pct=66.7,
        top_repos=repos[:3],
        bottom_repos=[],
        all_repos=repos,
    )


def _make_engine_cls(result):
    """Return a mock engine class that returns the given result."""
    class _MockEngine:
        def __init__(self, *a, **kw):
            pass
        def run(self, progress_callback=None):
            return result
    return _MockEngine


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def test_cli_bare_username():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)):
        out = runner.invoke(app, ["user-scorecard", "alice"])
    assert out.exit_code == 0


def test_cli_github_prefix():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)):
        out = runner.invoke(app, ["user-scorecard", "github:alice"])
    assert out.exit_code == 0


def test_cli_empty_username_error():
    out = runner.invoke(app, ["user-scorecard", "github:"])
    assert out.exit_code != 0


def test_cli_json_output():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)):
        out = runner.invoke(app, ["user-scorecard", "alice", "--json"])
    assert out.exit_code == 0
    data = json.loads(out.stdout)
    assert data["username"] == "alice"
    assert "grade" in data
    assert "avg_score" in data
    assert "all_repos" in data


def test_cli_json_schema_fields():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)):
        out = runner.invoke(app, ["user-scorecard", "alice", "--json"])
    data = json.loads(out.stdout)
    required_keys = {"username", "grade", "avg_score", "context_coverage_pct", "all_repos", "analyzed_repos"}
    assert required_keys.issubset(data.keys())


def test_cli_quiet_no_extra_output():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)):
        out = runner.invoke(app, ["user-scorecard", "alice", "--quiet"])
    assert out.exit_code == 0
    # quiet with no share/pages prints nothing
    assert out.stdout.strip() == ""


def test_cli_quiet_with_share_prints_url():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/abc"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--quiet", "--share"])
    assert out.exit_code == 0
    assert "https://here.now/abc" in out.stdout


def test_cli_limit_flag():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        runner.invoke(app, ["user-scorecard", "alice", "--limit", "5"])
        kwargs = MockEngine.call_args[1]
        assert kwargs.get("limit") == 5


def test_cli_min_stars_flag():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        runner.invoke(app, ["user-scorecard", "alice", "--min-stars", "10"])
        kwargs = MockEngine.call_args[1]
        assert kwargs.get("min_stars") == 10


def test_cli_no_skip_forks_flag():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        runner.invoke(app, ["user-scorecard", "alice", "--no-skip-forks"])
        kwargs = MockEngine.call_args[1]
        assert kwargs.get("skip_forks") is False


def test_cli_share_flag():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/xyz") as mock_upload:
        out = runner.invoke(app, ["user-scorecard", "alice", "--share"])
    assert out.exit_code == 0
    assert mock_upload.called


def test_cli_share_url_in_json():
    result = _make_result()
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine", _make_engine_cls(result)), \
         patch("agentkit_cli.commands.user_scorecard_cmd.upload_scorecard", return_value="https://here.now/xyz"):
        out = runner.invoke(app, ["user-scorecard", "alice", "--json", "--share"])
    data = json.loads(out.stdout)
    assert data.get("share_url") == "https://here.now/xyz"


def test_cli_user_not_found():
    with patch("agentkit_cli.commands.user_scorecard_cmd.UserScorecardEngine") as MockEngine:
        MockEngine.return_value.run.side_effect = ValueError("GitHub user 'nobody' not found")
        out = runner.invoke(app, ["user-scorecard", "nobody"])
    assert out.exit_code != 0

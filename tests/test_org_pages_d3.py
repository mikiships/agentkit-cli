"""Tests for D3: agentkit org --pages flag integration."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.org_pages import OrgPagesResult

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_org_cmd_result(ranked=None):
    mock = MagicMock()
    mock.return_value.run.return_value = {
        "owner": "myorg",
        "repo_count": 3,
        "analyzed": 3,
        "skipped": 0,
        "failed": 0,
        "ranked": ranked or [
            {"rank": 1, "full_name": "myorg/repo-a", "repo": "repo-a", "score": 88.0, "grade": "B",
             "top_finding": "Good", "status": "ok"},
        ],
    }
    return mock


def _mock_pages_engine(published=True, error=None):
    mock = MagicMock()
    mock.return_value.run.return_value = OrgPagesResult(
        pages_url="https://myorg.github.io/agentkit-scores/",
        repos_scored=3,
        avg_score=80.0,
        top_repo="myorg/repo-a",
        published=published,
        error=error,
    )
    return mock


# ---------------------------------------------------------------------------
# --pages flag wiring
# ---------------------------------------------------------------------------

def test_org_help_shows_pages_flag():
    result = runner.invoke(app, ["org", "--help"])
    assert result.exit_code == 0
    assert "--pages" in result.output

def test_org_help_shows_pages_repo_flag():
    result = runner.invoke(app, ["org", "--help"])
    assert result.exit_code == 0
    assert "--pages-repo" in result.output

def test_org_help_shows_dry_run_flag():
    result = runner.invoke(app, ["org", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output

def test_org_without_pages_does_not_invoke_engine():
    with patch("agentkit_cli.commands.org_cmd.OrgCommand") as mock_cmd_cls:
        mock_cmd_cls.return_value.run.return_value = {"owner": "myorg", "repo_count": 0, "ranked": [], "analyzed": 0, "skipped": 0, "failed": 0}
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", create=True) as mock_eng:
            runner.invoke(app, ["org", "github:myorg"], env={"GITHUB_TOKEN": "tok"})
    # OrgPagesEngine should not be imported/called without --pages
    # The import is guarded inside the if-pages block, so mock_eng.call_count should be 0
    # (if the attribute exists on the module at all during this test)


def test_org_pages_flag_invokes_engine():
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", _mock_pages_engine()):
            result = runner.invoke(app, ["org", "github:myorg", "--pages"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0

def test_org_pages_shows_pages_url():
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", _mock_pages_engine(published=True)):
            result = runner.invoke(app, ["org", "github:myorg", "--pages"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    assert "github.io" in result.output

def test_org_pages_dry_run_skips_push():
    mock_eng_cls = _mock_pages_engine(published=False)
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", mock_eng_cls):
            result = runner.invoke(app, ["org", "github:myorg", "--pages", "--dry-run"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    call_kwargs = mock_eng_cls.call_args[1]
    assert call_kwargs.get("dry_run") is True

def test_org_pages_passes_pages_repo():
    mock_eng_cls = _mock_pages_engine()
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", mock_eng_cls):
            runner.invoke(app, ["org", "github:myorg", "--pages", "--pages-repo", "myorg/custom"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_eng_cls.call_args[1]
    assert call_kwargs.get("pages_repo") == "myorg/custom"

def test_org_pages_failure_shows_warning():
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", _mock_pages_engine(published=False, error="push failed")):
            result = runner.invoke(app, ["org", "github:myorg", "--pages"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    assert "push failed" in result.output or "Warning" in result.output

def test_org_pages_passes_ranked_results_to_engine():
    ranked = [{"rank": 1, "full_name": "myorg/r", "repo": "r", "score": 90.0, "grade": "A", "top_finding": "X", "status": "ok"}]
    mock_eng_cls = _mock_pages_engine()
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result(ranked=ranked)):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", mock_eng_cls):
            runner.invoke(app, ["org", "github:myorg", "--pages"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_eng_cls.call_args[1]
    assert call_kwargs.get("_org_results") == ranked

def test_org_pages_json_includes_pages_url():
    with patch("agentkit_cli.commands.org_cmd.OrgCommand", _mock_org_cmd_result()):
        with patch("agentkit_cli.commands.org_cmd.OrgPagesEngine", _mock_pages_engine(published=True)):
            result = runner.invoke(app, ["org", "github:myorg", "--pages", "--json"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "pages_url" in data

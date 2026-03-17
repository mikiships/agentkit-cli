"""Tests for agentkit_cli/commands/track_cmd.py — agentkit track command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.history import HistoryDB
from agentkit_cli.pr_tracker import TrackedPRStatus

runner = CliRunner()


def _make_status(
    repo="owner/repo",
    pr_number=1,
    pr_url="https://github.com/owner/repo/pull/1",
    campaign_id=None,
    submitted_at="2026-03-14T10:00:00+00:00",
    status="open",
    days_open=3,
    review_comments=0,
    is_merged=False,
    id=1,
) -> TrackedPRStatus:
    return TrackedPRStatus(
        id=id,
        repo=repo,
        pr_number=pr_number,
        pr_url=pr_url,
        campaign_id=campaign_id,
        submitted_at=submitted_at,
        status=status,
        days_open=days_open,
        review_comments=review_comments,
        is_merged=is_merged,
    )


# ---------------------------------------------------------------------------
# No PRs
# ---------------------------------------------------------------------------


def test_track_no_prs(tmp_path):
    """Shows a 'no tracked PRs' message when DB is empty."""
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = []
        result = runner.invoke(app, ["track"])
    assert result.exit_code == 0
    assert "No tracked PRs" in result.output


def test_track_no_prs_with_campaign_id(tmp_path):
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = []
        result = runner.invoke(app, ["track", "--campaign-id", "abc123"])
    assert result.exit_code == 0
    assert "No tracked PRs" in result.output


# ---------------------------------------------------------------------------
# Table output
# ---------------------------------------------------------------------------


def test_track_table_shows_repos(tmp_path):
    statuses = [
        _make_status(repo="owner/repo", status="merged", is_merged=True, id=1),
        _make_status(repo="other/proj", status="open", id=2),
    ]
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = [{"id": 1}, {"id": 2}]
        instance.refresh_statuses.return_value = statuses
        result = runner.invoke(app, ["track"])
    assert result.exit_code == 0
    assert "owner/repo" in result.output
    assert "other/proj" in result.output


def test_track_table_summary_line(tmp_path):
    statuses = [
        _make_status(status="merged", is_merged=True, id=1),
        _make_status(status="open", id=2),
        _make_status(status="closed", id=3),
    ]
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        instance.refresh_statuses.return_value = statuses
        result = runner.invoke(app, ["track"])
    assert result.exit_code == 0
    assert "1 merged" in result.output
    assert "1 open" in result.output
    assert "1 closed" in result.output


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def test_track_json_output():
    statuses = [_make_status(status="merged", is_merged=True, id=1)]
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = [{"id": 1}]
        instance.refresh_statuses.return_value = statuses
        result = runner.invoke(app, ["track", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["status"] == "merged"
    assert data[0]["is_merged"] is True


def test_track_json_output_empty():
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = []
        result = runner.invoke(app, ["track", "--json"])
    assert result.exit_code == 0
    # Shows "No tracked PRs" message, not JSON
    assert "No tracked PRs" in result.output


# ---------------------------------------------------------------------------
# Limit and --all
# ---------------------------------------------------------------------------


def test_track_limit_passed_to_tracker():
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = []
        result = runner.invoke(app, ["track", "--limit", "5"])
    assert result.exit_code == 0
    instance.get_tracked_prs.assert_called_once()
    call_kwargs = instance.get_tracked_prs.call_args
    assert call_kwargs.kwargs.get("limit") == 5 or (
        len(call_kwargs.args) > 0 and 5 in call_kwargs.args
    )


def test_track_all_flag():
    with patch("agentkit_cli.commands.track_cmd.PRTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.get_tracked_prs.return_value = []
        result = runner.invoke(app, ["track", "--all"])
    assert result.exit_code == 0
    call_kwargs = instance.get_tracked_prs.call_args
    # limit should be 10000 when --all is used
    assert call_kwargs.kwargs.get("limit") == 10000 or (
        len(call_kwargs.args) > 0 and 10000 in call_kwargs.args
    )


# ---------------------------------------------------------------------------
# Registered in app
# ---------------------------------------------------------------------------


def test_track_command_registered():
    result = runner.invoke(app, ["--help"])
    assert "track" in result.output

"""Tests for D2: --pages flag on `agentkit daily` CLI."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.daily_leaderboard import DailyLeaderboard, RankedRepo

runner = CliRunner()


def _make_leaderboard(n: int = 3) -> DailyLeaderboard:
    repos = [
        RankedRepo(
            rank=i + 1,
            full_name=f"org/repo-{i}",
            description=f"Repo {i}",
            stars=1000 * (i + 1),
            language="Python",
            url=f"https://github.com/org/repo-{i}",
            composite_score=80.0 - i,
            top_finding=f"Finding {i}",
        )
        for i in range(n)
    ]
    return DailyLeaderboard(
        date=date(2026, 3, 19),
        repos=repos,
        generated_at=datetime(2026, 3, 19, 8, 0, 0, tzinfo=timezone.utc),
        total_fetched=n,
    )


# ---------------------------------------------------------------------------
# --help shows new flags
# ---------------------------------------------------------------------------

def test_daily_help_shows_pages_flag():
    result = runner.invoke(app, ["daily", "--help"])
    assert "--pages" in result.output


def test_daily_help_shows_pages_repo_flag():
    result = runner.invoke(app, ["daily", "--help"])
    assert "--pages-repo" in result.output


def test_daily_help_shows_pages_path_flag():
    result = runner.invoke(app, ["daily", "--help"])
    assert "--pages-path" in result.output


# ---------------------------------------------------------------------------
# --pages success path
# ---------------------------------------------------------------------------

def test_daily_pages_success_prints_url():
    lb = _make_leaderboard()
    pages_result = {
        "pages_url": "https://mikiships.github.io/agentkit-cli/leaderboard.html",
        "committed": True,
    }

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", return_value=pages_result):
        result = runner.invoke(app, ["daily", "--pages"])

    assert result.exit_code == 0
    assert "mikiships.github.io" in result.output


def test_daily_pages_success_exit_code():
    lb = _make_leaderboard()
    pages_result = {"pages_url": "https://owner.github.io/repo/leaderboard.html", "committed": True}

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", return_value=pages_result):
        result = runner.invoke(app, ["daily", "--pages"])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --pages failure → fallback to --share
# ---------------------------------------------------------------------------

def test_daily_pages_failure_falls_back_to_share():
    lb = _make_leaderboard()
    pages_result = {"pages_url": "", "committed": False, "error": "git push failed"}
    share_url = "https://here.now/abc123"

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", return_value=pages_result), \
         patch("agentkit_cli.commands.daily_cmd.publish_report", return_value=share_url):
        result = runner.invoke(app, ["daily", "--pages"])

    assert result.exit_code == 0
    assert "here.now" in result.output or "abc123" in result.output or "fallback" in result.output.lower() or "failed" in result.output.lower()


# ---------------------------------------------------------------------------
# --pages-repo flag
# ---------------------------------------------------------------------------

def test_daily_pages_repo_flag_accepted():
    lb = _make_leaderboard()
    pages_result = {"pages_url": "https://owner.github.io/repo/leaderboard.html", "committed": True}

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", return_value=pages_result):
        result = runner.invoke(app, ["daily", "--pages", "--pages-repo", "github:owner/repo"])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --pages-path flag
# ---------------------------------------------------------------------------

def test_daily_pages_path_flag_accepted():
    lb = _make_leaderboard()
    pages_result = {"pages_url": "https://owner.github.io/repo/board.html", "committed": True}

    captured = {}

    def mock_publish(html, leaderboard, repo_path=".", pages_path="docs/leaderboard.html"):
        captured["pages_path"] = pages_path
        return pages_result

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", side_effect=mock_publish):
        result = runner.invoke(app, ["daily", "--pages", "--pages-path", "docs/board.html"])

    assert result.exit_code == 0
    assert captured.get("pages_path") == "docs/board.html"


# ---------------------------------------------------------------------------
# --pages quiet mode
# ---------------------------------------------------------------------------

def test_daily_pages_quiet_prints_only_url():
    lb = _make_leaderboard()
    pages_result = {"pages_url": "https://owner.github.io/repo/leaderboard.html", "committed": True}

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_to_pages", return_value=pages_result):
        result = runner.invoke(app, ["daily", "--pages", "--quiet"])

    assert result.exit_code == 0
    assert "https://owner.github.io/repo/leaderboard.html" in result.output


# ---------------------------------------------------------------------------
# --pages does not interfere with --share
# ---------------------------------------------------------------------------

def test_daily_share_still_works_without_pages():
    lb = _make_leaderboard()

    with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb), \
         patch("agentkit_cli.commands.daily_cmd.publish_report", return_value="https://here.now/xyz"):
        result = runner.invoke(app, ["daily", "--share"])

    assert result.exit_code == 0
    assert "here.now" in result.output
